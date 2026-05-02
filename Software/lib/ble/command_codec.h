#pragma once
#include <stddef.h>
#include <stdint.h>

namespace cw {
namespace ble {

// =============================================================================
// 业务命令 / 唤醒广播 字节流编码器 (CommandCodec)
// -----------------------------------------------------------------------------
// 把 "魔杖业务侧动作 (开始录像 / 切模式 / 打高光 / 按键 / 唤醒广播)"
// 翻译成 "符合协议规范的字节流" 的纯函数库.
//
// 设计动机:
//   1) 把 BleRemote 中混在一起的 "GATT 协议栈集成" 与 "字节流拼装" 解耦.
//      BleRemote 只负责把已经组好的字节流通过 NOTIFY / Advertising 推出去,
//      具体字节布局完全交给本模块.
//   2) 字节流拼装是 "纯逻辑", 不依赖 BLE 库, 因此可以在 *本地 Linux* 上
//      用单元测试覆盖 (Software/test/), 而不需要 ESP32 / NimBLE 工具链.
//   3) 协议规范的契约 (命令字 = cfg::kCmdTxXxx / 唤醒广播 = prefix+token+suffix
//      / 模式循环 = kModeSwitchSeq) 在测试代码中作为断言点反复出现, 一旦
//      某次提交不小心改坏了 BleRemote::SendXxx 的命令字或字节顺序, 测试
//      立即失败.
//
// 不感知任何具体协议字段取值: 所有具体值 (kCmdTx* / kWakeupAdvPrefix 等)
// 都来自 protocol_config.h (由 protocol.json 构建期生成), 本头文件只在函数
// 名上反映业务语义 (RecordStart / SetMode / Mark / Button / WakeupAdv).
// =============================================================================

class CommandCodec {
public:
    // ===== 业务命令 -> 出向帧字节流 (Wand -> Peer) =====
    //
    // 通用约定:
    //   - out      : 调用方提供的输出缓冲区, 不可为 nullptr
    //   - cap      : out 容量, 必须 >= 帧头长 + payload 长
    //   - 返回值   : 写入字节数 (含帧头), 失败返回 0
    //   - 失败语义 : out 为空 / cap 不足 / 内部 RemoteFrame 编码失败
    //
    // 字节流统一布局 (由 RemoteFrame::EncodeOutboundFrame 保证):
    //   [HEAD 3B] [CMD 1B] [END|SN 1B] [SIZE 1B] [DATA SIZE B]

    /// 开始录制: cmd = cfg::kCmdTxRecordStart, 无 payload
    static size_t BuildRecordStartFrame(uint8_t* out, size_t cap);

    /// 停止录制: cmd = cfg::kCmdTxRecordStop, 无 payload
    static size_t BuildRecordStopFrame(uint8_t* out, size_t cap);

    /// 切到指定子模式: cmd = cfg::kCmdTxSetMode, payload = [sub_mode_id] (1B)
    static size_t BuildSetModeFrame(uint8_t sub_mode_id, uint8_t* out, size_t cap);

    /// 打高光标记: cmd = cfg::kCmdTxMark, 无 payload
    static size_t BuildHighlightMarkFrame(uint8_t* out, size_t cap);

    /// 自定义按键事件: cmd = cfg::kCmdTxButton, payload = [device_id, button_id, state] (3B)
    static size_t BuildButtonFrame(uint8_t device_id,
                                   uint8_t button_id,
                                   uint8_t state,
                                   uint8_t* out,
                                   size_t cap);

    // ===== 唤醒广播 manufacturer-data 字节流 =====

    /**
     * @brief  组装唤醒广播包的 manufacturer-data 字节流.
     *
     * 字节布局 (与协议描述符一致):
     *   [prefix N B]  cfg::kWakeupAdvPrefix  (含 CompanyID + iBeacon header 等)
     *   [token  6 B]  最近一次配对对端的 SN
     *   [suffix M B]  cfg::kWakeupAdvSuffix  (Major / Minor / TxPower 等)
     *
     * @param  token  最近一次配对对端的 6 字节 SN, 不可为 nullptr
     * @param  out    输出缓冲区, 不可为 nullptr
     * @param  cap    out 容量, 必须 >= prefix_len + 6 + suffix_len
     * @return 写入字节数 (= prefix_len + 6 + suffix_len), 失败返回 0
     */
    static size_t BuildWakeupAdvManufacturerData(const uint8_t token[6],
                                                 uint8_t* out,
                                                 size_t cap);

    /// 唤醒广播 manufacturer-data 总长度 (常量, 等于 prefix + 6 + suffix)
    static size_t WakeupAdvManufacturerDataLength();
};

// =============================================================================
// ModeRotator: 子模式循环索引器
// -----------------------------------------------------------------------------
// 维护 "下一次 CycleToNextSubMode 应该发送 kModeSwitchSeq 的哪一项" 状态.
// 抽出来作为独立类是为了:
//   1) 让 BleRemote 不必持有这个索引字段 (单一职责)
//   2) 让 "循环顺序符合 kModeSwitchSeq" 这个协议契约可单测
//
// 用法:
//   ModeRotator r;
//   r.NextSubMode();  // -> kModeSwitchSeq[0], 索引推进到 1
//   r.NextSubMode();  // -> kModeSwitchSeq[1], 索引推进到 2
//   ...
//   r.NextSubMode();  // -> kModeSwitchSeq[N-1], 索引回绕到 0
//   r.NextSubMode();  // -> kModeSwitchSeq[0], 新一轮
// =============================================================================
class ModeRotator {
public:
    /**
     * @brief  取出当前 sub_mode ID, 同时把索引推进一格 (循环).
     *
     * @return 当前 sub_mode ID;
     *         若 cfg::kModeSwitchSeqLen == 0 (协议未配置任何模式),
     *         返回 0xFF 且不推进索引 (调用方应据此放弃发送).
     */
    uint8_t NextSubMode();

    /// 当前内部索引值 (主要给单元测试用; 业务方不应依赖)
    uint8_t CurrentIndex() const { return m_idx; }

    /// 重置到序列起点 (主要给单元测试用)
    void Reset() { m_idx = 0; }

private:
    uint8_t m_idx = 0;
};

}  // namespace ble
}  // namespace cw
