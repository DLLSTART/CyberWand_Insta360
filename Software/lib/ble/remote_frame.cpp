#include "remote_frame.h"

#include <string.h>

#include "protocol_config.h"

namespace cw {
namespace ble {

// 出向 SN 全局计数器, 0~127 间循环
uint8_t RemoteFrame::s_sn_seq = 0;

/**
 * 简单转发到协议描述符常量, 单独封装是为了:
 *   1) 让外部头不依赖 protocol_config.h (避免泄露常量取值)
 *   2) 上层无需关心头长度变化, 直接通过本接口分配缓冲
 */
uint8_t RemoteFrame::HeaderLength() {
    return cfg::kFrameHeadLen;
}

uint8_t RemoteFrame::MaxPayloadLength() {
    return cfg::kFrameMaxData;
}

/**
 * 分配下一个 SN 并自增.
 *
 * 流程:
 *   1) 取计数器低 7bit 作为本次帧的 SN
 *      (& 0x7F 是防御性掩码, 保证写入帧的 [END|SN] 字节时
 *       不会污染高位的 END 标志)
 *   2) 计数器 +1 再次 & 0x7F:
 *      127 + 1 = 128 -> & 0x7F 后变 0, 实现自然回绕
 *
 * 调用序列示例:
 *   第 1 次返回 0,   计数器 -> 1
 *   第 2 次返回 1,   计数器 -> 2
 *   ...
 *   第 128 次返回 127, 计数器 -> 0  (回绕)
 *   第 129 次返回 0,   计数器 -> 1  (新一轮)
 *
 * 帧组装时 (EncodeOutboundFrame) 会把返回值与 cfg::kFrameEndBit 按位或:
 *   out_buf[4] = cfg::kFrameEndBit | AllocateNextSequenceNumber();
 * 所以 SN=0 对应字节 0x80, SN=127 对应字节 0xFF.
 */
uint8_t RemoteFrame::AllocateNextSequenceNumber() {
    uint8_t sn = s_sn_seq & 0x7F;
    s_sn_seq = (s_sn_seq + 1) & 0x7F;
    return sn;
}

/**
 * 把业务字段编码为一个出向帧字节流 (Wand -> Peer).
 *
 * 流程:
 *   1) 入参合法性: out_buf 不为空, payload 不超限, 缓冲区容量足够
 *   2) 按协议描述符写入 3 字节 HEAD
 *   3) 写入 CMD 字节
 *   4) 写入 END|SN: END 位恒置位 (单包语义), SN 由 AllocateNextSequenceNumber 自增提供
 *   5) 写入 SIZE 字节
 *   6) 若 payload 非空, 拷贝至 HEAD 之后
 *   7) 返回总长度 = 头长 + payload 长
 *
 * 失败约定: 任意校验失败统一返回 0, 调用方据此跳过 GATT 推送.
 */
size_t RemoteFrame::EncodeOutboundFrame(uint8_t cmd,
                                        const uint8_t* data,
                                        uint8_t size,
                                        uint8_t* out_buf,
                                        size_t out_cap) {
    if (out_buf == nullptr) {
        return 0;
    }
    // payload 上限由协议描述符决定, 防止溢出 BLE MTU
    if (size > cfg::kFrameMaxData) {
        return 0;
    }
    const size_t total = static_cast<size_t>(cfg::kFrameHeadLen) + size;
    if (out_cap < total) {
        return 0;
    }

    // 3 字节 HEAD: 出向头与入向头方向相反, 由协议描述符定义
    out_buf[0] = cfg::kFrameHeadOutbound[0];
    out_buf[1] = cfg::kFrameHeadOutbound[1];
    out_buf[2] = cfg::kFrameHeadOutbound[2];
    out_buf[3] = cmd;
    // END 位 | 7bit SN: 单包发送恒置 END
    out_buf[4] = cfg::kFrameEndBit | AllocateNextSequenceNumber();
    out_buf[5] = size;

    if (size > 0 && data != nullptr) {
        memcpy(out_buf + cfg::kFrameHeadLen, data, size);
    }
    return total;
}

/**
 * 把入向字节流解码成一个 InboundFrame 描述 (Peer -> Wand).
 *
 * 流程:
 *   1) 入参合法性: buf 不为空, 长度至少够一个完整头
 *   2) 帧头校验: 仅匹配第 0/2 字节, 与对端栈实现一致
 *      (对端在某些版本中第 1 字节会做掩码, 此处宽松匹配以兼容)
 *   3) 抽取 CMD / END / SN / SIZE
 *   4) 二次长度校验: 头长 + DATA 长 不能超出实际接收字节数
 *   5) 设置 frame.data 指针 (size==0 时置 nullptr 避免误用)
 *
 * 任何校验失败时:
 *   - 返回 false
 *   - frame 内容未定义, 调用方禁止使用
 */
bool RemoteFrame::DecodeInboundFrame(const uint8_t* buf, size_t len, InboundFrame& frame) {
    if (buf == nullptr || len < cfg::kFrameHeadLen) {
        return false;
    }
    // 与对端栈一致, 仅校验 buf[0]/buf[2]
    if (buf[0] != cfg::kFrameHeadInbound[0] ||
        buf[2] != cfg::kFrameHeadInbound[2]) {
        return false;
    }
    frame.cmd  = buf[3];
    frame.end  = (buf[4] & cfg::kFrameEndBit) != 0;
    frame.sn   = buf[4] & 0x7F;
    frame.size = buf[5];
    // 防御性长度校验: 防止越界读 payload
    if (static_cast<size_t>(cfg::kFrameHeadLen) + frame.size > len) {
        return false;
    }
    frame.data = (frame.size > 0) ? (buf + cfg::kFrameHeadLen) : nullptr;
    return true;
}

}  // namespace ble
}  // namespace cw

