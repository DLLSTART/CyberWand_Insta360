#pragma once
#include <stddef.h>
#include <stdint.h>

namespace cw {
namespace ble {

// =============================================================================
// 应用层帧描述 (codec)
// -----------------------------------------------------------------------------
// 本模块只负责 "字节流 <-> 业务帧" 的两向转换, 不感知任何 BLE / GATT 细节.
// 帧的具体取值 (帧头 / 命令字 / END 位 / 单帧最大 payload) 由
// protocol_config.h (由 config/protocol.json 构建期生成) 提供, 见 cfg:: 命名空间.
//
// 单帧通用布局:
//      [HEAD 3B] [CMD 1B] [END|SN 1B] [SIZE 1B] [DATA SIZE B]
//   其中:
//     - HEAD 3B   : 出向(Wand->Peer) / 入向(Peer->Wand) 各自不同, 用于栈一致性校验
//     - CMD       : 业务命令字
//     - END       : 多帧拆分时表示 "本片是最后一片"; 当前实现单包发送, END 恒置位
//     - SN        : 7bit 序列号, 用于丢帧 / 重发判定
//     - SIZE      : 紧随头之后 DATA 字段的字节数 (不含头本身)
//     - DATA      : 业务负载, 可选; 长度受 cfg::kFrameMaxData 限制
// =============================================================================

// 解析出的入向帧描述
// data 指针指向原始缓冲区中 DATA 段起始位置, 调用方需保证缓冲区生命周期.
struct InboundFrame {
    uint8_t        cmd;   // CMD 字段
    uint8_t        sn;    // 7bit SN
    bool           end;   // END 标记 (true 表示本片是末片)
    uint8_t        size;  // DATA 字段字节数
    const uint8_t* data;  // 指向 DATA 段, size==0 时为 nullptr
};

class RemoteFrame {
public:
    /**
     * @brief  分配出向帧的下一个 SN (Sequence Number) 序列号.
     *
     * SN 是 0~127 自动回绕的递增计数器, 每发出一帧就 +1.
     * 它会被写入帧布局的 [END|SN] 字节的低 7 位
     * (高位被 END 标志占用):
     *
     *     bit 7 6 5 4 3 2 1 0
     *         |--SN (7bit)--|
     *         ^
     *         END 位
     *
     * 用途:
     *   - 对端按收到帧的 SN 判断有无跳号, 例如接收序列 5 -> 6 -> 8
     *     就能识别 "中间漏了一帧 SN=7", 用作丢帧感知.
     *   - 同一帧若被对端误重收, SN 重复也能识别为重复帧.
     *
     * 本端策略:
     *   只递增, 不重发. 因为 BLE NOTIFY 本身就是 best-effort,
     *   业务命令 (录像 / 标记) 丢了用户重试一次即可, 不需要协议层重传.
     *
     * @return 本次帧应当使用的 SN 值 (0~127); 调用后内部计数已自增.
     *
     * @note   通常只由 EncodeOutboundFrame() 内部使用, 暴露 public 是方便:
     *           - 单元测试构造特定 SN 序列
     *           - 调试日志预读下一个 SN 关联打印
     *         单线程使用 (BLE 任务), 未做锁保护.
     */
    static uint8_t AllocateNextSequenceNumber();

    /**
     * @brief  把业务字段编码为一个出向帧字节流 (Wand -> Peer).
     * @param  cmd      业务命令字
     * @param  data     payload 缓冲区, 允许为 nullptr (当 size==0)
     * @param  size     payload 字节数, 必须 <= cfg::kFrameMaxData
     * @param  out_buf  调用方提供的输出缓冲区
     * @param  out_cap  out_buf 容量
     * @return 写入字节数 (含帧头), 失败返回 0.
     * @note   SN 字段每次自动递增; END 位恒置位 (单包语义).
     */
    static size_t EncodeOutboundFrame(uint8_t cmd,
                                      const uint8_t* data,
                                      uint8_t size,
                                      uint8_t* out_buf,
                                      size_t out_cap);

    /**
     * @brief  把入向字节流解码成一个 InboundFrame 描述 (Peer -> Wand).
     * @param  buf    原始字节流
     * @param  len    buf 中实际字节数
     * @param  frame  [out] 解析结果; 仅在返回 true 时有效
     * @return true 解析成功且字段自洽; false 帧头不匹配 / 长度不足.
     * @note   仅做轻量校验 (帧头 / 长度), 不做 CRC; 与对端栈实现保持一致.
     */
    static bool DecodeInboundFrame(const uint8_t* buf, size_t len, InboundFrame& frame);

    /// 帧头总长度 (HEAD+CMD+END|SN+SIZE), 供调用方分配缓冲
    static uint8_t HeaderLength();

    /// 单帧 DATA 字段最大字节数
    static uint8_t MaxPayloadLength();

private:
    // 出向 SN 全局自增计数器, 跨线程暂未保护 (当前仅 BLE 任务调用)
    static uint8_t s_sn_seq;
};

}  // namespace ble
}  // namespace cw

