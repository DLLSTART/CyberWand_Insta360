#pragma once
#include <Arduino.h>
#include <stdint.h>

#include "base.h"

namespace cw {
namespace ble {

// =============================================================================
// 配对记录持久化 (PairedStore)
// -----------------------------------------------------------------------------
// 设备 (魔杖) 在每次成功完成应用层握手后, 都会从对端收到一段 6 字节 ASCII
// token (实际上就是对端的产品 SN), 用作对端在协议层面的唯一标识.
// 后续未连接时, 设备使用最近一次配对的 token 拼装 vendor-specific
// 唤醒广播包, 让该 (而且仅是该) 对端的硬件唤醒过滤器命中, 并发起连接.
//
// 本类用于把 "最近一次配对记录" 持久化到 NVS, 重启后仍可使用.
// 设计上仅保存最近一条:
//   - 嵌入式资源有限, 无需维护多配对列表
//   - 实际使用场景就是 1 个魔杖对 1 台对端的常用搭配
//   - 用户更换对端时, 由新一次配对覆盖旧记录
//
// 配对状态决定开机后的广播包形态:
//   Has() == false  -> 普通可发现广播 (任意对端可手动连)
//   Has() == true   -> 带 token 的唤醒广播 (匹配的对端
//                      会被硬件过滤器命中并自动唤醒连接)
// =============================================================================

// 最近一次配对记录
// token 由对端在连接成功后通过应用层协议下发, 6 字节 ASCII (= 对端产品 SN)
// mac 仅做诊断用途 (日志 / 调试), 与协议层面的匹配无关
struct PairedRecord {
    uint8_t  token[6];     // 6 字节 ASCII 标识, 不含 '\0'
    uint8_t  mac[6];       // 蓝牙地址 (大端), 仅做诊断
    uint8_t  mac_valid;    // 0=mac 字段无效; 1=mac 字段有效
    uint32_t last_link_ms; // 最近一次配对时间戳 (millis()), 仅做诊断
};

class PairedStore : public base::Singleton<PairedStore> {
    friend class base::Singleton<PairedStore>;

public:
    /**
     * @brief 一次性初始化: 从 NVS 加载最近一次配对记录到内存.
     * @note  幂等; 系统启动时由 BleRemote::Init() 显式触发.
     */
    void Init();

    /**
     * @brief  保存一条新的配对记录 (覆盖旧记录).
     * @param  token       对端下发的 6 字节 ASCII token
     * @param  mac         对端蓝牙地址 (6 字节, 大端), 可为 nullptr
     * @param  mac_valid   true 表示 mac 参数可用并入库
     * @note   立即写入 NVS, 调用线程会发生短暂 flash 写延时.
     */
    void Save(const uint8_t token[6], const uint8_t mac[6], bool mac_valid);

    /// 是否已保存过任何配对记录 (false 表示首次出厂或被 Forget 过)
    bool Has() const { return m_valid; }

    /**
     * @brief  取出最近一次配对记录的常引用.
     * @note   仅在 Has() == true 时有效;
     *         调用方应先检查 Has() 再使用.
     */
    const PairedRecord& Get() const { return m_record; }

    /**
     * @brief 忘记当前配对记录, 让设备回到 "未配对" 状态.
     * @note  立即写入 NVS, 重启后仍生效.
     *        调用后开机将退回普通广播.
     */
    void Forget();

private:
    PairedStore() = default;

    // NVS 读写, 失败时仅静默 (m_valid 维持当前内存值)
    void LoadFromNvs();
    void SaveToNvs() const;

    PairedRecord m_record = {};    // 最近一次配对记录的内存缓存
    bool         m_valid  = false; // m_record 是否有效 (NVS 中是否存在)
    bool         m_inited = false; // Init() 是否已执行
};

}  // namespace ble
}  // namespace cw
