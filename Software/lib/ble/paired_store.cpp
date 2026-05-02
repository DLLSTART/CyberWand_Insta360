#include "paired_store.h"

#include <Preferences.h>
#include <string.h>

#include "base.h"

namespace cw {
namespace ble {

namespace {
// NVS 命名空间与键
//   - 命名空间统一为 "cw_paired", 与其它模块隔离
//   - kNvsKeyValid : 1 字节 "是否有效" 标志, 用于区分 "首次烧录" 与 "曾经配对"
//   - kNvsKeyLast  : sizeof(PairedRecord) 字节的二进制配对记录
constexpr const char* kNvsNamespace = "cw_paired";
constexpr const char* kNvsKeyLast   = "last";
constexpr const char* kNvsKeyValid  = "valid";
}  // namespace

/**
 * 一次性初始化.
 *
 * 流程:
 *   1) 若已 Init 过则直接返回 (幂等)
 *   2) 从 NVS 加载最近一次配对记录到内存缓存
 *   3) 置 m_inited 防止重复加载
 */
void PairedStore::Init() {
    if (m_inited) {
        return;
    }
    LoadFromNvs();
    m_inited = true;
}

/**
 * 从 NVS 加载最近一次配对记录.
 *
 * 流程:
 *   1) 以只读方式打开 NVS 命名空间; 打开失败 -> 标记无效后返回
 *   2) 读取 valid 标志位; 为 0 -> 标记无效, 跳过 byte 读取
 *   3) 检查 last 键的字节长度: 必须 >= sizeof(PairedRecord), 否则视为损坏
 *   4) 全量读出 PairedRecord 结构体到 m_record; 置 m_valid = true
 *   5) 关闭 NVS handle
 *
 * 健壮性: 任何异常 (打开失败 / 长度不足 / 标志为 0) 一律视为 "无配对",
 * 不抛错, 让设备回退到 "未配对开机" 状态发送普通广播.
 */
void PairedStore::LoadFromNvs() {
    Preferences prefs;
    if (!prefs.begin(kNvsNamespace, /*readOnly=*/true)) {
        // NVS 命名空间首次访问可能不存在, 这是首次烧录的正常情况, 仅 trace
        ILOGT("[paired] NVS open(ro, ns=%s) failed -> treat as unpaired\n",
              kNvsNamespace);
        m_valid = false;
        return;
    }
    uint8_t valid = prefs.getUChar(kNvsKeyValid, 0);
    size_t  blen  = prefs.getBytesLength(kNvsKeyLast);
    if (valid && blen >= sizeof(PairedRecord)) {
        prefs.getBytes(kNvsKeyLast, &m_record, sizeof(PairedRecord));
        m_valid = true;
        ILOGT("[paired] NVS load OK: token=%c%c%c%c%c%c mac_valid=%u\n",
              m_record.token[0], m_record.token[1], m_record.token[2],
              m_record.token[3], m_record.token[4], m_record.token[5],
              static_cast<unsigned>(m_record.mac_valid));
    } else {
        ILOGT("[paired] NVS load: no record (valid=%u blen=%u)\n",
              static_cast<unsigned>(valid),
              static_cast<unsigned>(blen));
        m_valid = false;
    }
    prefs.end();
}

/**
 * 把当前内存缓存写回 NVS.
 *
 * 流程:
 *   1) 以读写方式打开 NVS 命名空间; 打开失败 -> 静默返回
 *   2) 写入 valid 标志位
 *   3) 若有效, 把 m_record 整个结构体二进制写入
 *      若无效 (用户调用 Forget), 则删除 last 键避免残留
 *   4) 关闭 NVS handle
 *
 * 注意: Preferences::put*() 会同步擦写 flash, 调用线程会被阻塞数毫秒,
 *       本类调用频率较低 (仅在 Save / Forget), 可接受.
 */
void PairedStore::SaveToNvs() const {
    Preferences prefs;
    if (!prefs.begin(kNvsNamespace, /*readOnly=*/false)) {
        // 写失败说明 NVS flash 异常, 是真异常 - 用 ILOGN 提高可见度
        ILOGN("[paired] NVS open(rw) FAILED, paired record NOT persisted");
        return;
    }
    prefs.putUChar(kNvsKeyValid, m_valid ? 1 : 0);
    if (m_valid) {
        size_t wrote = prefs.putBytes(kNvsKeyLast, &m_record, sizeof(PairedRecord));
        if (wrote != sizeof(PairedRecord)) {
            ILOGT("[paired] NVS save WARN: wrote %u/%u bytes\n",
                  static_cast<unsigned>(wrote),
                  static_cast<unsigned>(sizeof(PairedRecord)));
        } else {
            ILOGT("[paired] NVS save OK: token=%c%c%c%c%c%c\n",
                  m_record.token[0], m_record.token[1], m_record.token[2],
                  m_record.token[3], m_record.token[4], m_record.token[5]);
        }
    } else {
        prefs.remove(kNvsKeyLast);
        ILOGN("[paired] NVS save: record cleared");
    }
    prefs.end();
}

/**
 * 保存一条新的配对记录 (覆盖旧记录).
 *
 * 流程:
 *   1) 入参合法性: token 不可为空
 *   2) 拷贝 6 字节 token 到内存缓存
 *   3) mac 字段:
 *      - mac_valid 且 mac != nullptr -> 拷贝并标记有效
 *      - 其它情况 -> 清零并标记无效
 *   4) 记录当前时间戳 (仅做诊断)
 *   5) 标记内存有效, 立即同步到 NVS
 *
 * 调用时机: BleRemote::Write() 收到 kCmdRxPeerToken 帧时.
 */
void PairedStore::Save(const uint8_t token[6], const uint8_t mac[6], bool mac_valid) {
    if (token == nullptr) {
        ILOGN("[paired] Save drop: token is null");
        return;
    }
    memcpy(m_record.token, token, 6);
    if (mac_valid && mac != nullptr) {
        memcpy(m_record.mac, mac, 6);
        m_record.mac_valid = 1;
    } else {
        memset(m_record.mac, 0, 6);
        m_record.mac_valid = 0;
    }
    m_record.last_link_ms = millis();
    m_valid = true;
    SaveToNvs();
}

/**
 * 忘记当前配对记录.
 *
 * 流程:
 *   1) 内存缓存清零
 *   2) m_valid 置 false
 *   3) 立即把 "无效" 状态同步写入 NVS, 触发 last 键删除
 *
 * 后果: 下次 BleRemote::ApplyCurrentAdvertisement() 调用时
 *       会回退到普通广播模式, 等待用户在新对端上手动连接.
 */
void PairedStore::Forget() {
    ILOGN("[paired] Forget: clear paired record");
    memset(&m_record, 0, sizeof(m_record));
    m_valid = false;
    SaveToNvs();
}

}  // namespace ble
}  // namespace cw
