#pragma once
#include <Arduino.h>
#include <stdint.h>

#include "base.h"
#include "command_codec.h"

class BLEServer;
class BLECharacteristic;
class BLEAdvertising;

namespace cw {
namespace ble {

// =============================================================================
// 通用 BLE 控制适配器
// -----------------------------------------------------------------------------
// 本类把 ESP32 BLE 协议栈 (Arduino-ESP32 BLEDevice 系列 API) 与本项目的
// "手势 -> 命令" 业务流封装在一起, 上层只看到几个语义化方法:
//
//   - Init                              : 一次性初始化
//   - SwitchAdvByTick                   : 主循环周期调用, 驱动广播轮换
//   - IsConnected                       : 状态查询
//   - SendRecordStart / SendRecordStop /
//     CycleToNextSubMode / SendHighlightMark / SendButton
//                                       : 已连接时下发业务命令
//
// 广播策略 (BleRemote 内部全自动管理, 调用方无需介入):
//
//   未配对                                未连接
//      | 普通可发现广播 (Name + ServiceUUID)                  无窗口
//      | 等待任意对端在 BLE 列表里手动选择并连接                 切换
//      v
//   已配对                                未连接
//      | 普通广播  <-- kWakeupAdvRotatePeriodMs --> 唤醒广播
//      | (Name)                                    (manufacturer-data 含 SN)
//      | 让 *任意* 新对端能扫到 Name 并手动配对     | 让 *原配对* 对端的硬件
//      v 实现重复配对                              v 唤醒过滤器命中并自动连接
//
// 与具体对端厂家相关的所有协议字段 (GAP 名 / Service UUID / 帧头 / 命令字 /
// 唤醒广播 manufacturer-data 字节布局 / 子模式 ID 序列) 全部由
// config/protocol.json -> include/protocol_config.h 提供, 本头文件中
// 不出现任何具体取值, 便于代码上传开源而不泄露私有协议细节.
//
// 单例存在: 整个系统只有一个 BLE radio.
// =============================================================================
class BleRemote : public base::Singleton<BleRemote> {
    friend class base::Singleton<BleRemote>;

public:
    /**
     * @brief  一次性初始化 BLE 协议栈与 GATT Service.
     *
     * 内部依次完成:
     *   1) 加载 NVS 中最近一次配对对端记录
     *   2) 启动 BLE Device, 设置 GAP 名与首选 MTU
     *   3) 创建 GATT Server / Service / Characteristic (Notify + Write)
     *   4) 根据当前配对状态选择初始广播包内容
     *      (未配对 -> Normal; 已配对 -> Wakeup, 后续由 Tick 驱动轮换)
     *   5) 启动广播
     *
     * @note 幂等; 多次调用只会执行一次.
     *       调用线程: setup() 阶段, 早于业务循环.
     */
    void Init();

    /**
     * @brief 由主循环周期调用, 按 tick 节流驱动 "已配对 + 未连接" 状态下的广播轮换.
     *
     * 函数语义: 每次主循环 tick 时被调用, 内部判断是否到了切换广播形态的时刻
     *           (Normal <-> Wakeup), 是则切换, 否则立即返回.
     *
     * 触发条件 (全部满足才执行轮换):
     *   - 已 Init
     *   - 当前未连接 (连接中 BLE 库自动停 adv, 没必要切换)
     *   - 已配对 (PairedStore::Has() == true; 未配对一直发普通广播)
     *
     * 节流: 内部按 cfg::kWakeupAdvRotatePeriodMs (默认 5s) 切换一次,
     *       即使主循环极高频调用也只会到时才切.
     */
    void SwitchAdvByTick();

    /// 是否已与对端建立 GATT 连接
    bool IsConnected() const { return m_connected; }

    // ===== 业务封装: 手势 -> 控制命令 =====
    // 全部接口的语义:
    //   返回 true  : 已通过 GATT NOTIFY 推送 (但不保证对端已收到)
    //   返回 false : 未连接 / 内部组帧失败, 调用方应给用户合理提示

    /// 触发对端开始录制
    bool SendRecordStart();

    /// 触发对端停止录制
    bool SendRecordStop();

    /**
     * @brief  循环切换到下一个子模式.
     * @return 是否成功推送
     * @note   切换序列由 protocol.json 中 "modes.switch_sequence" 配置,
     *         本类内部维护循环索引, 调用方无需关心当前是哪个模式.
     */
    bool CycleToNextSubMode();

    /// 触发对端在当前流上打一个高光标记 (常用于事后剪辑定位)
    bool SendHighlightMark();

    /**
     * @brief  自定义按键事件转发, 具体语义由协议描述决定.
     * @param  device_id  上下文字段 1
     * @param  button_id  上下文字段 2
     * @param  state      上下文字段 3 (按下 / 释放等)
     */
    bool SendButton(uint8_t device_id, uint8_t button_id, uint8_t state);

private:
    BleRemote() = default;

    /**
     * @brief 广播包形态.
     *
     * - Normal : 主包放 GAP Name + Flags, ScanResp 放 ServiceUUID.
     *            被动扫描的中心设备能看到 Name, 用户可在列表里手动选中.
     *            未配对 / 已配对均可使用.
     * - Wakeup : 主包放 vendor-specific manufacturer-data (含 6B SN),
     *            ScanResp 放 Name + ServiceUUID 供主动扫描时获取.
     *            主包匿名, 仅原配对对端的硬件唤醒过滤器能命中 SN.
     *            仅在 PairedStore::Has() == true 时有意义.
     */
    enum class AdvMode { Normal, Wakeup };

    /**
     * @brief 根据当前配对状态决定并应用初始广播形态, 重置轮换计时.
     *
     * 调用时机:
     *   - Init() 末尾, 决定初始广播
     *   - HandleDisconnected() 之后, 决定重连广播
     *   - Write() 收到对端 SN 后, 让下一次广播立即用新 SN
     *
     * 选择策略:
     *   未配对 -> AdvMode::Normal (一直保持)
     *   已配对 -> AdvMode::Wakeup (由 Tick 5s 后切到 Normal, 然后循环)
     */
    void ApplyCurrentAdvertisement();

    /// 把指定形态的广播包应用到 BLE Advertising.
    void ApplyAdvertisementPayload(AdvMode mode);

    /// GATT 写回调 -> 解析对端帧并按 cmd 分发
    void Write(const uint8_t* data, size_t len);

    /// GATT 连接事件 (peer_addr 为对端蓝牙地址, 可为全 0)
    void HandleConnected(const uint8_t peer_addr[6]);

    /// GATT 断开事件: 重置状态并恢复广播
    void HandleDisconnected();

    /**
     * @brief 内部辅助: 把已经组好的字节流通过 GATT NOTIFY 推送给对端.
     *        字节流的拼装 (帧头 / 命令字 / payload) 完全由 CommandCodec 负责.
     * @param buf  CommandCodec::BuildXxxFrame 输出的字节流
     * @param n    字节流长度; 0 表示拼装失败, 本函数将返回 false
     * @param tag  仅日志用的简短 tag (例如 "RecordStart"), 可为 nullptr
     * @return 是否成功推送; 调用方一般直接转发本返回值.
     */
    bool PushNotify(const uint8_t* buf, size_t n, const char* tag);

    // 嵌入式回调实现, 与外部解耦
    class ServerCallbacksImpl;
    class CharCallbacksImpl;

    BLEServer*         m_server      = nullptr;
    BLECharacteristic* m_notify_char = nullptr; // Wand -> Peer
    BLECharacteristic* m_write_char  = nullptr; // Peer -> Wand
    BLEAdvertising*    m_adv         = nullptr;

    bool     m_inited       = false;
    bool     m_connected    = false;
    uint8_t  m_peer_addr[6] = {0};   // 当前对端地址, 仅做诊断

    // 子模式循环器 (封装 cfg::kModeSwitchSeq 上的循环逻辑, 可单测)
    ModeRotator m_mode_rotator;

    // 广播轮换状态
    AdvMode  m_current_adv_mode = AdvMode::Normal;
    uint32_t m_last_rotate_ms   = 0;
};

}  // namespace ble
}  // namespace cw

