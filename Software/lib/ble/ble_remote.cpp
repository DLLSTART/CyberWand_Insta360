#include "ble_remote.h"

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLEAdvertising.h>
#include <BLE2902.h>
#include <esp_gap_ble_api.h>
#include <esp_gatt_common_api.h>
#include <string.h>

#include "remote_frame.h"
#include "paired_store.h"
#include "command_codec.h"
#include "protocol_config.h"

namespace cw {
namespace ble {

// =============================================================================
// 嵌套回调实现
// -----------------------------------------------------------------------------
// 设计动机:
//   ESP32 BLE 库的回调接口要求继承固定基类 (BLEServerCallbacks /
//   BLECharacteristicCallbacks). 把它们做成 BleRemote 的私有嵌套类, 可以
//   在不暴露内部状态的前提下, 把所有事件转发回 BleRemote 实例处理.
// =============================================================================

/**
 * GAP/GATT 服务器级回调:
 *   - 收到对端发起的连接 / 断开时, 转发给 BleRemote.
 *   - 兼容两个版本的 onConnect 重载, 以适配不同版本 Arduino-ESP32 BLE 库.
 */
class BleRemote::ServerCallbacksImpl : public BLEServerCallbacks {
public:
    explicit ServerCallbacksImpl(BleRemote* owner) : m_owner(owner) {}

    // 新版库带 param: 可拿到对端蓝牙地址
    void onConnect(BLEServer* /*server*/, esp_ble_gatts_cb_param_t* param) override {
        uint8_t addr[6] = {0};
        if (param != nullptr) {
            memcpy(addr, param->connect.remote_bda, 6);
        }
        m_owner->HandleConnected(addr);
    }

    // 老版库不带 param: 只能传全 0 地址, 仅用于翻转状态
    void onConnect(BLEServer* /*server*/) override {
        uint8_t addr[6] = {0};
        m_owner->HandleConnected(addr);
    }

    void onDisconnect(BLEServer* /*server*/) override {
        m_owner->HandleDisconnected();
    }

private:
    BleRemote* m_owner;
};

/**
 * Characteristic 级回调:
 *   - onWrite : 对端通过 Write 通道发来一帧, 转发给 BleRemote 解析
 */
class BleRemote::CharCallbacksImpl : public BLECharacteristicCallbacks {
public:
    explicit CharCallbacksImpl(BleRemote* owner) : m_owner(owner) {}

    void onWrite(BLECharacteristic* characteristic) override {
        if (characteristic == nullptr) {
            return;
        }
        // 注意: getValue() 返回的 std::string 仅在本回调作用域内有效
        std::string value = characteristic->getValue();
        m_owner->Write(
            reinterpret_cast<const uint8_t*>(value.data()),
            value.size());
    }

private:
    BleRemote* m_owner;
};

// =============================================================================
// 公共生命周期
// =============================================================================

/**
 * 初始化 BLE 协议栈与 GATT Service, 启动初始广播.
 *
 * 流程 (按依赖顺序):
 *   1) 幂等保护: 已 init 直接返回
 *   2) 加载 NVS 中最近一次配对记录
 *      (后续广播包形态、对端 token 校验都依赖此数据)
 *   3) 启动 BLEDevice, 设置 GAP 名与首选 MTU
 *      MTU 越大单帧 payload 越大, 但实际生效需对端协商通过
 *   4) 创建 GATT Server, 绑定 Server 级回调
 *   5) 在 Server 上创建 Service (UUID 由协议描述符指定)
 *   6) 创建两条 Characteristic:
 *      - Notify  : Wand 推命令到对端, 同时支持 Read 便于对端首次握手
 *                  附加 BLE2902 描述符以支持对端的 CCCD 订阅
 *      - Write   : 对端推数据到 Wand (绑定 onWrite 回调)
 *   7) 启动 Service
 *   8) 拿到 Advertising 句柄, 注入 Service UUID, 设置广播间隔参数
 *      0x06/0x12 是 BLE Spec 推荐的 minPreferred 取值
 *   9) 根据当前配对状态选择初始广播包内容
 *      - 未配对 -> 一直 Normal
 *      - 已配对 -> 起始 Wakeup, 后续由 Tick 驱动 Normal/Wakeup 轮换
 *  10) 启动广播, 进入 "等待对端连接" 状态
 */
void BleRemote::Init() {
    if (m_inited) {
        ILOGN("[ble] Init: already inited, skip");
        return;
    }
    PairedStore::GetInstance().Init();

    BLEDevice::init(cfg::kRemoteGapName);
    BLEDevice::setMTU(cfg::kPreferredMtu);

    m_server = BLEDevice::createServer();
    if (m_server == nullptr) {
        ILOGN("[ble] Init FAILED: createServer returned null");
        return;
    }
    m_server->setCallbacks(new ServerCallbacksImpl(this));

    BLEService* service = m_server->createService(BLEUUID(cfg::kRemoteServiceUuid16));
    if (service == nullptr) {
        ILOGT("[ble] Init FAILED: createService(0x%04X) returned null\n",
              cfg::kRemoteServiceUuid16);
        return;
    }

    // Notify 通道: Wand -> Peer 控制帧
    m_notify_char = service->createCharacteristic(
        BLEUUID(cfg::kRemoteNotifyUuid16),
        BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ);
    if (m_notify_char == nullptr) {
        ILOGT("[ble] Init FAILED: createChar notify(0x%04X) null\n",
              cfg::kRemoteNotifyUuid16);
        return;
    }
    m_notify_char->addDescriptor(new BLE2902());

    // Write 通道: Peer -> Wand
    m_write_char = service->createCharacteristic(
        BLEUUID(cfg::kRemoteWriteUuid16),
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
    if (m_write_char == nullptr) {
        ILOGT("[ble] Init FAILED: createChar write(0x%04X) null\n",
              cfg::kRemoteWriteUuid16);
        return;
    }
    m_write_char->setCallbacks(new CharCallbacksImpl(this));

    service->start();

    m_adv = BLEDevice::getAdvertising();
    if (m_adv == nullptr) {
        ILOGN("[ble] Init FAILED: getAdvertising returned null");
        return;
    }
    m_adv->addServiceUUID(BLEUUID(cfg::kRemoteServiceUuid16));
    m_adv->setScanResponse(true);
    // 设置广播 minInterval / maxInterval, 取值符合 BLE Spec 推荐
    m_adv->setMinPreferred(0x06);
    m_adv->setMinPreferred(0x12);

    ApplyCurrentAdvertisement();
    m_adv->start();

    if (PairedStore::GetInstance().Has()) {
        const auto& paired = PairedStore::GetInstance().Get();
        ILOGT("[ble] Init OK as \"%s\" (paired, token=%c%c%c%c%c%c, rotating every %u ms)\n",
              cfg::kRemoteGapName,
              paired.token[0], paired.token[1], paired.token[2],
              paired.token[3], paired.token[4], paired.token[5],
              static_cast<unsigned>(cfg::kWakeupAdvRotatePeriodMs));
    } else {
        ILOGT("[ble] Init OK as \"%s\" (unpaired, normal adv only)\n",
              cfg::kRemoteGapName);
    }
    m_inited = true;
}

/**
 * 主循环周期调用 (按 tick 节流), 驱动 "已配对 + 未连接" 状态下的广播轮换.
 *
 * 流程:
 *   1) 状态前置: 已 Init / 当前未连接
 *      - 未 Init: 还没准备好, 直接退出
 *      - 已连接: BLE 库自动停止 advertising, 切来切去也没意义
 *   2) 配对前置: PairedStore::Has() == true
 *      - 未配对: 一直发普通广播, 不需要切换
 *   3) 节流: 距上次切换 < kWakeupAdvRotatePeriodMs 直接返回
 *   4) 翻转 m_current_adv_mode (Normal <-> Wakeup) 并应用
 *   5) 打日志, 便于现场调试每次切换时间
 */
void BleRemote::SwitchAdvByTick() {
    if (!m_inited || m_connected) {
        return;
    }
    if (!PairedStore::GetInstance().Has()) {
        return;
    }

    uint32_t now = millis();
    if ((now - m_last_rotate_ms) < cfg::kWakeupAdvRotatePeriodMs) {
        return;
    }
    m_last_rotate_ms = now;

    m_current_adv_mode = (m_current_adv_mode == AdvMode::Normal)
                       ? AdvMode::Wakeup
                       : AdvMode::Normal;
    ApplyAdvertisementPayload(m_current_adv_mode);

    ILOGT("[ble] adv rotated -> %s\n",
          m_current_adv_mode == AdvMode::Wakeup ? "wakeup" : "normal");
}

// =============================================================================
// 业务命令封装
// =============================================================================

/**
 * 内部辅助: 把已经组好的字节流通过 GATT NOTIFY 推送给对端.
 *
 * 流程:
 *   1) 状态前置: 已 Init / 已连接 / Notify 句柄存在
 *   2) 字节数有效 (n > 0, CommandCodec 失败时返回 0)
 *   3) 把字节数据写入 Notify Characteristic 并触发 notify()
 *
 * 失败时返回 false, 调用方按需给用户 LED / 日志反馈.
 *
 * 注意: 字节流的拼装 (帧头 / 命令字 / END|SN / SIZE / payload) 完全由
 *       CommandCodec 模块负责, 本函数只做 GATT 推送, 不感知任何协议字段.
 *       这种 "拼装 vs 推送" 的解耦让字节流拼装可以在本地单元测试里单独验证.
 */
bool BleRemote::PushNotify(const uint8_t* buf, size_t n, const char* tag) {
    if (!m_inited) {
        ILOGT("[ble] notify %s drop: not inited\n", tag ? tag : "?");
        return false;
    }
    if (!m_connected) {
        ILOGT("[ble] notify %s drop: peer not connected\n", tag ? tag : "?");
        return false;
    }
    if (m_notify_char == nullptr) {
        ILOGT("[ble] notify %s drop: notify char null\n", tag ? tag : "?");
        return false;
    }
    if (buf == nullptr || n == 0) {
        ILOGT("[ble] notify %s drop: encode failed (buf=%p n=%u)\n",
              tag ? tag : "?",
              static_cast<const void*>(buf),
              static_cast<unsigned>(n));
        return false;
    }
    m_notify_char->setValue(const_cast<uint8_t*>(buf), n);
    m_notify_char->notify();
    ILOGT("[ble] notify %s OK (%u bytes)\n",
          tag ? tag : "?", static_cast<unsigned>(n));
    return true;
}

/// 录制开始 (cmd = kCmdTxRecordStart, 无 payload), 字节流由 CommandCodec 拼装
bool BleRemote::SendRecordStart() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildRecordStartFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "RecordStart");
}

/// 录制停止 (cmd = kCmdTxRecordStop, 无 payload)
bool BleRemote::SendRecordStop() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildRecordStopFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "RecordStop");
}

/**
 * 循环切换到下一个子模式.
 *
 * 流程:
 *   1) 通过 ModeRotator 取出 "本次该用哪个 sub_mode ID" 并把内部索引推进
 *      (循环逻辑封装在 ModeRotator 内, 本类不再持有索引字段)
 *   2) 模式表为空时 NextSubMode 返回 0xFF, 这里据此放弃发送
 *   3) 由 CommandCodec 组装 kCmdTxSetMode + 1B payload 字节流
 *   4) 调 PushNotify 通过 GATT NOTIFY 推出去
 *
 * 模式 ID 序列由 protocol.json 配置, 业务侧只暴露 "切下一个" 语义,
 * 完全隔离了协议细节.
 */
bool BleRemote::CycleToNextSubMode() {
    if (cfg::kModeSwitchSeqLen == 0) {
        ILOGN("[ble] CycleToNextSubMode skip: mode-switch sequence is empty");
        return false;
    }
    uint8_t prev_idx = m_mode_rotator.CurrentIndex();
    uint8_t sub_mode = m_mode_rotator.NextSubMode();
    ILOGT("[ble] CycleToNextSubMode: send sub_mode=%u (idx %u -> %u)\n",
          static_cast<unsigned>(sub_mode),
          static_cast<unsigned>(prev_idx),
          static_cast<unsigned>(m_mode_rotator.CurrentIndex()));

    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildSetModeFrame(sub_mode, buf, sizeof(buf));
    return PushNotify(buf, n, "SetMode");
}

/// 在当前流上打一个高光标记 (cmd = kCmdTxMark, 无 payload)
bool BleRemote::SendHighlightMark() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildHighlightMarkFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "Mark");
}

/**
 * 转发自定义按键事件.
 *
 * 流程:
 *   1) 由 CommandCodec 把 3 个上下文字段拼成 kCmdTxButton + 3B payload 字节流
 *   2) 调 PushNotify 通过 GATT NOTIFY 推出去
 *
 * 字段语义由协议描述符规定, 本类不解释也不校验.
 */
bool BleRemote::SendButton(uint8_t device_id, uint8_t button_id, uint8_t state) {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildButtonFrame(
        device_id, button_id, state, buf, sizeof(buf));
    return PushNotify(buf, n, "Button");
}

// =============================================================================
// 广播包内容生成
// =============================================================================

/**
 * 根据当前配对状态决定并应用初始广播形态, 重置轮换计时.
 *
 * 流程:
 *   1) 查询 PairedStore::Has():
 *      - true  : 进入轮换状态. 起始用 Wakeup 让原对端硬件先命中,
 *                kWakeupAdvRotatePeriodMs 后由 SwitchAdvByTick 切到 Normal,
 *                给新对端被动扫描的窗口, 然后再切回 Wakeup, 循环.
 *      - false : 一直保持 Normal 普通广播.
 *   2) 重置 m_last_rotate_ms 让下一次轮换从 "现在" 起算
 *   3) 立即把选定形态的广播包应用到 m_adv
 *
 * 调用时机统一封装于此, 任何配对状态变化 (开机加载 / 收到新 SN /
 * 用户 Forget 等) 都通过本方法重新决定起始广播包.
 *
 * 注意: 本方法只更新 m_adv 内的广播数据.
 *       - 当前正在广播 (未连接), 数据立即生效, 下一个 adv 间隔起按新内容发
 *       - 当前已连接 (BLE 库自动停止 advertising), 数据被保存,
 *         待下一次 m_adv->start() 时使用 (HandleDisconnected 会触发)
 */
void BleRemote::ApplyCurrentAdvertisement() {
    if (PairedStore::GetInstance().Has()) {
        m_current_adv_mode = AdvMode::Wakeup;
    } else {
        m_current_adv_mode = AdvMode::Normal;
    }
    m_last_rotate_ms = millis();
    ApplyAdvertisementPayload(m_current_adv_mode);
}

/**
 * 把指定形态的广播包应用到 BLE Advertising.
 *
 * Normal 模式 (普通可发现广播):
 *   主包 (Adv)     : Flags(0x06) + Name
 *                    Name 在主包里, 让对端 *被动扫描* 也能直接看到 Name
 *   ScanResp       : ServiceUUID
 *
 * Wakeup 模式 (vendor-specific 唤醒广播):
 *   主包 (Adv)     : Flags(0x06) + ManufacturerData
 *                    主包不含 Name, 因为 manufacturer-data 已 26+B 几乎用满 31B,
 *                    且原配对对端只关心 ManufacturerData 里的 SN, 不需要 Name
 *   ScanResp       : Name + ServiceUUID
 *                    新对端 *主动扫描* 时仍能拿到 Name 用于显示
 *
 *   manufacturer-data 字节布局:
 *     [prefix N B]  含 CompanyID(2B LE) + iBeacon header 等 (协议描述符提供)
 *     [token  6 B]  最近一次配对对端的 SN (从 PairedStore 取)
 *     [suffix M B]  Major / Minor / TxPower 等 (协议描述符提供)
 *
 * 流程:
 *   1) Advertising 句柄无效则放弃 (理论上 Init 后不会发生)
 *   2) 准备 adv_data 与 scan_rsp 两个对象, 都先打 Flags
 *   3) 按 mode 分支:
 *      Normal -> 主包加 Name; ScanResp 加 ServiceUUID
 *      Wakeup -> 主包加 ManufacturerData (拼装 prefix + token + suffix);
 *                ScanResp 加 Name + ServiceUUID
 *      Wakeup 但无配对记录 (不应该发生) -> 退化到 Normal
 *   4) 应用到 m_adv
 */
void BleRemote::ApplyAdvertisementPayload(AdvMode mode) {
    if (m_adv == nullptr) {
        ILOGN("[ble] ApplyAdv FAILED: m_adv null");
        return;
    }

    BLEAdvertisementData adv_data;
    BLEAdvertisementData scan_rsp;
    adv_data.setFlags(0x06);  // BR/EDR Not Supported + LE General Discoverable

    auto& store = PairedStore::GetInstance();
    const bool can_wakeup = (mode == AdvMode::Wakeup) && store.Has();

    if (can_wakeup) {
        // ---- Wakeup 模式: 主包注入 manufacturer-data ----
        // 防御性上限: BLE 主包总容量 31 B, mfr 不可过大
        uint8_t mfr[64] = {0};
        const auto& paired = store.Get();
        // 字节流拼装 (prefix + token + suffix) 完全由 CommandCodec 负责,
        // 协议布局变更只需改 protocol.json + CommandCodec, BleRemote 无感.
        size_t mfr_len = CommandCodec::BuildWakeupAdvManufacturerData(
            paired.token, mfr, sizeof(mfr));
        if (mfr_len == 0) {
            ILOGT("[ble] ApplyAdv FAILED: BuildWakeupAdvManufacturerData "
                  "returned 0 (need %u, buf %u, check protocol.json)\n",
                  static_cast<unsigned>(
                      CommandCodec::WakeupAdvManufacturerDataLength()),
                  static_cast<unsigned>(sizeof(mfr)));
            return;
        }

        std::string mfr_str(reinterpret_cast<const char*>(mfr), mfr_len);
        adv_data.setManufacturerData(mfr_str);

        // ScanResp 仍然带 Name + ServiceUUID, 让 active scan 也能显示 Name
        scan_rsp.setName(cfg::kRemoteGapName);
        scan_rsp.setCompleteServices(BLEUUID(cfg::kRemoteServiceUuid16));
    } else {
        // ---- Normal 模式: 主包就是 Name ----
        adv_data.setName(cfg::kRemoteGapName);

        // ScanResp 单独放 ServiceUUID, 同时让 31B 主包不溢出
        scan_rsp.setCompleteServices(BLEUUID(cfg::kRemoteServiceUuid16));
    }

    m_adv->setAdvertisementData(adv_data);
    m_adv->setScanResponseData(scan_rsp);
}

// =============================================================================
// GATT 事件
// =============================================================================

/**
 * 对端建立连接时回调.
 *
 * 流程:
 *   1) 标记已连接 (后续业务命令将能成功推送, Tick 内的轮换自动停止)
 *   2) 缓存对端蓝牙地址 (仅做诊断, 与协议匹配无关)
 *   3) 打印对端 MAC 便于现场调试
 *
 * 注意: BLE 库会在连接建立时自动停止 advertising, 我们不必手动 stop.
 *       后续断开后由 HandleDisconnected() 重新启动广播.
 */
void BleRemote::HandleConnected(const uint8_t peer_addr[6]) {
    m_connected = true;
    if (peer_addr != nullptr) {
        memcpy(m_peer_addr, peer_addr, 6);
    }
    ILOGT("[ble] connected by %02X:%02X:%02X:%02X:%02X:%02X\n",
          m_peer_addr[0], m_peer_addr[1], m_peer_addr[2],
          m_peer_addr[3], m_peer_addr[4], m_peer_addr[5]);
}

/**
 * 对端断开连接时回调.
 *
 * 流程:
 *   1) 打印日志
 *   2) 清连接标志 (业务命令将自动失败, Tick 重新进入轮换)
 *   3) 根据当前配对状态重新选择初始广播形态并重置轮换计时
 *      (若上次连接中刚刚收到了 SN, 这里就会从 Wakeup 模式起跑)
 *   4) 主动重启广播 (BLE 库连接期间会自动停止 adv, 断开后需手动 start)
 */
void BleRemote::HandleDisconnected() {
    ILOGT("[ble] disconnected from %02X:%02X:%02X:%02X:%02X:%02X, restart adv\n",
          m_peer_addr[0], m_peer_addr[1], m_peer_addr[2],
          m_peer_addr[3], m_peer_addr[4], m_peer_addr[5]);
    m_connected = false;
    if (m_adv != nullptr) {
        ApplyCurrentAdvertisement();
        m_adv->start();
    } else {
        ILOGN("[ble] WARN: cannot restart adv, m_adv is null");
    }
}

/**
 * Write Characteristic 收到对端数据时的统一入口.
 *
 * 流程:
 *   1) 入参合法性: 数据非空且至少够一个完整帧头
 *   2) 调用 RemoteFrame::DecodeInboundFrame 做轻量解析:
 *      失败 -> 打印长度后丢弃, 不影响连接
 *   3) 按 cmd 分发:
 *      - kCmdRxPeerToken (对端在握手阶段下发自身 SN):
 *           * 长度必须等于 cfg::kFramePeerTokenPayloadLen (通常 6B)
 *           * 调用 PairedStore::Save 持久化 SN + MAC
 *           * 调用 ApplyCurrentAdvertisement() 立即更新内存广播数据,
 *             这样下次断开重启广播时就会用新 SN 进入 Wakeup/Normal 轮换
 *           * 此后该魔杖与该对端形成 "1 对 1" 配对关系
 *             (但仍允许后续被新对端通过 Normal 切片重新配对)
 *      - kCmdRxShutdown / kCmdRxDisconnect:
 *           对端请求关机或主动断开, 本设备 (魔杖) 不做任何响应,
 *           仅打印日志便于排查.
 *      - 其它 cmd: 静默忽略, 不让对端的协议升级影响本端稳定性.
 */
void BleRemote::Write(const uint8_t* data, size_t len) {
    if (data == nullptr || len < RemoteFrame::HeaderLength()) {
        ILOGT("[ble] write drop: bad input (data=%p len=%u min=%u)\n",
              static_cast<const void*>(data),
              static_cast<unsigned>(len),
              static_cast<unsigned>(RemoteFrame::HeaderLength()));
        return;
    }
    InboundFrame frame{};
    if (!RemoteFrame::DecodeInboundFrame(data, len, frame)) {
        ILOGT("[ble] write %u bytes, header mismatch (b0=0x%02X b2=0x%02X)\n",
              static_cast<unsigned>(len), data[0], data[2]);
        return;
    }
    ILOGT("[ble] write OK: cmd=0x%02X end=%d sn=%u size=%u\n",
          frame.cmd, frame.end ? 1 : 0,
          static_cast<unsigned>(frame.sn),
          static_cast<unsigned>(frame.size));

    if (frame.cmd == cfg::kCmdRxPeerToken) {
        if (frame.size != cfg::kFramePeerTokenPayloadLen ||
            frame.data == nullptr) {
            ILOGT("[ble] peer-token bad size=%u (expect %u)\n",
                  static_cast<unsigned>(frame.size),
                  static_cast<unsigned>(cfg::kFramePeerTokenPayloadLen));
            return;
        }
        PairedStore::GetInstance().Save(frame.data, m_peer_addr, true);
        // 立刻按新 SN 重算广播数据; 当前虽在连接中 (BLE 库已停 adv),
        // 但数据保存到 m_adv 后, 断开重启 adv 时会自动生效.
        ApplyCurrentAdvertisement();
        ILOGT("[ble] paired record saved, token=%c%c%c%c%c%c (will rotate on next disconnect)\n",
              frame.data[0], frame.data[1], frame.data[2],
              frame.data[3], frame.data[4], frame.data[5]);
        return;
    }

    if (frame.cmd == cfg::kCmdRxShutdown ||
        frame.cmd == cfg::kCmdRxDisconnect) {
        ILOGT("[ble] peer asked cmd=0x%02X (ignored on wand)\n", frame.cmd);
        return;
    }

    // 其它对端命令对魔杖无业务意义, 但记录 trace 便于抓未支持的命令字
    ILOGT("[ble] unhandled inbound cmd=0x%02X size=%u, ignored\n",
          frame.cmd, static_cast<unsigned>(frame.size));
}

}  // namespace ble
}  // namespace cw

