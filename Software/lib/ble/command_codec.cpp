#include "command_codec.h"

#include <string.h>

#include "remote_frame.h"
#include "protocol_config.h"

namespace cw {
namespace ble {

// -----------------------------------------------------------------------------
// 业务命令 -> 帧字节流
// -----------------------------------------------------------------------------
// 全部 5 个 BuildXxx 都是单行透传到 RemoteFrame::EncodeOutboundFrame,
// 区别只在于:
//   1) 用哪个 cfg::kCmdTx* 命令字
//   2) payload 是否有内容, 多大
//
// 这一层薄薄的包装看似多余, 但价值在于:
//   - 业务侧 (BleRemote::SendXxx) 不再硬编码 cfg::kCmdTx*, 减少改协议时
//     遗漏修改某个 SendXxx 的风险.
//   - 单元测试可以直接断言 "BuildRecordStartFrame 产生的字节流第 4 字节
//     一定等于 cfg::kCmdTxRecordStart", 把 "业务语义 -> 命令字" 这条
//     映射关系作为协议契约固化下来.
// -----------------------------------------------------------------------------

size_t CommandCodec::BuildRecordStartFrame(uint8_t* out, size_t cap) {
    return RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxRecordStart, nullptr, 0, out, cap);
}

size_t CommandCodec::BuildRecordStopFrame(uint8_t* out, size_t cap) {
    return RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxRecordStop, nullptr, 0, out, cap);
}

size_t CommandCodec::BuildSetModeFrame(uint8_t sub_mode_id, uint8_t* out, size_t cap) {
    return RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxSetMode, &sub_mode_id, 1, out, cap);
}

size_t CommandCodec::BuildHighlightMarkFrame(uint8_t* out, size_t cap) {
    return RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxMark, nullptr, 0, out, cap);
}

size_t CommandCodec::BuildButtonFrame(uint8_t device_id,
                                      uint8_t button_id,
                                      uint8_t state,
                                      uint8_t* out,
                                      size_t cap) {
    uint8_t payload[3] = {device_id, button_id, state};
    return RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxButton, payload, sizeof(payload), out, cap);
}

// -----------------------------------------------------------------------------
// 唤醒广播 manufacturer-data 字节流
// -----------------------------------------------------------------------------

size_t CommandCodec::WakeupAdvManufacturerDataLength() {
    return static_cast<size_t>(cfg::kWakeupAdvPrefixLen)
         + cfg::kWakeupTokenLen
         + cfg::kWakeupAdvSuffixLen;
}

/**
 * 组装唤醒广播包.
 *
 * 流程:
 *   1) 入参合法性: token 与 out 不可为空
 *   2) 容量校验: cap 必须 >= prefix + 6 + suffix
 *   3) 顺序拷贝三段:
 *      - cfg::kWakeupAdvPrefix (固定 N 字节)
 *      - token                 (固定 6 字节)
 *      - cfg::kWakeupAdvSuffix (固定 M 字节)
 *   4) 返回总写入字节数
 *
 * 任何一步失败均返回 0; 成功时 out 内容完整.
 */
size_t CommandCodec::BuildWakeupAdvManufacturerData(const uint8_t token[6],
                                                    uint8_t* out,
                                                    size_t cap) {
    if (token == nullptr || out == nullptr) {
        return 0;
    }
    const size_t total = WakeupAdvManufacturerDataLength();
    if (cap < total) {
        return 0;
    }

    size_t off = 0;
    memcpy(out + off, cfg::kWakeupAdvPrefix, cfg::kWakeupAdvPrefixLen);
    off += cfg::kWakeupAdvPrefixLen;

    memcpy(out + off, token, cfg::kWakeupTokenLen);
    off += cfg::kWakeupTokenLen;

    memcpy(out + off, cfg::kWakeupAdvSuffix, cfg::kWakeupAdvSuffixLen);
    off += cfg::kWakeupAdvSuffixLen;

    return off;
}

// -----------------------------------------------------------------------------
// ModeRotator
// -----------------------------------------------------------------------------

/**
 * 取出当前 sub_mode ID 并循环推进索引.
 *
 * 流程:
 *   1) 模式表为空 (cfg::kModeSwitchSeqLen == 0): 返回 0xFF, 索引不动
 *   2) 取 cfg::kModeSwitchSeq[m_idx] 作为本次返回值
 *   3) 索引 +1 后对长度取模, 实现自然循环
 */
uint8_t ModeRotator::NextSubMode() {
    if (cfg::kModeSwitchSeqLen == 0) {
        return 0xFF;
    }
    uint8_t cur = cfg::kModeSwitchSeq[m_idx];
    m_idx = (m_idx + 1) % cfg::kModeSwitchSeqLen;
    return cur;
}

}  // namespace ble
}  // namespace cw
