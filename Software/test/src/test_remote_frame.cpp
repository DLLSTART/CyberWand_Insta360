// =============================================================================
// test_remote_frame.cpp
// -----------------------------------------------------------------------------
// 覆盖 cw::ble::RemoteFrame 的全部对外方法 + 内部 SN 计数器边界:
//   1. HeaderLength()  / MaxPayloadLength()    — 元信息暴露
//   2. AllocateNextSequenceNumber()            — 0~127 自然回绕
//   3. EncodeOutboundFrame()                   — 帧布局 / 容量保护 / SN 写入
//   4. DecodeInboundFrame()                    — 帧头校验 / 长度自洽 / data 指针
//
// 测试策略:
//   - 对所有边界条件 (size=0 / size=Max / size=Max+1 / out_cap 不足 / 头不对)
//     一条路径写一条用例, 失败时打印具体字段
//   - 跨用例 SN 不可预测 (静态计数器跨用例累积), 但用例内可断言相邻两次差
// =============================================================================

#include "mini_test.h"

#include <cstring>

#include "remote_frame.h"
#include "protocol_config.h"

using cw::ble::RemoteFrame;
using cw::ble::InboundFrame;
namespace cfg = cw::ble::cfg;

// -----------------------------------------------------------------------------
// 元信息: 头长 / 单帧最大 payload — 必须等于协议描述符
// -----------------------------------------------------------------------------
MT_TEST(RemoteFrame, HeaderLengthMatchesConfig) {
    MT_EXPECT_EQ((int)RemoteFrame::HeaderLength(), (int)cfg::kFrameHeadLen);
}

MT_TEST(RemoteFrame, MaxPayloadLengthMatchesConfig) {
    MT_EXPECT_EQ((int)RemoteFrame::MaxPayloadLength(), (int)cfg::kFrameMaxData);
}

// -----------------------------------------------------------------------------
// SN 序列: 0~127 自增 + 自然回绕
// -----------------------------------------------------------------------------
// 注: 静态计数器跨用例累积, 不能假设起点为 0; 只断言 "相邻递增 + 范围"
MT_TEST(RemoteFrame, AllocateNextSequenceNumberRange) {
    for (int i = 0; i < 200; i++) {
        uint8_t sn = RemoteFrame::AllocateNextSequenceNumber();
        MT_EXPECT_TRUE(sn <= 127);
    }
}

MT_TEST(RemoteFrame, AllocateNextSequenceNumberMonotonicWithWrap) {
    // 取 130 个连续 SN, 应该恰好出现一次 127->0 的回绕
    uint8_t prev = RemoteFrame::AllocateNextSequenceNumber();
    int wrap_cnt = 0;
    for (int i = 0; i < 129; i++) {
        uint8_t cur = RemoteFrame::AllocateNextSequenceNumber();
        if (cur == 0 && prev == 127) {
            wrap_cnt++;
        } else {
            MT_EXPECT_EQ((int)cur, (int)((prev + 1) & 0x7F));
        }
        prev = cur;
    }
    MT_EXPECT_TRUE(wrap_cnt >= 1);
}

// -----------------------------------------------------------------------------
// EncodeOutboundFrame: 头布局 / 容量校验 / END 位 / 空 payload
// -----------------------------------------------------------------------------
MT_TEST(RemoteFrame, EncodeOutboundFrameZeroPayload) {
    uint8_t buf[16] = {0};
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxRecordStart, nullptr, 0, buf, sizeof(buf));
    MT_EXPECT_EQ((int)n, (int)cfg::kFrameHeadLen);

    // 头 3 字节必须等于出向头
    MT_EXPECT_BYTES_EQ(buf, cfg::kFrameHeadOutbound, 3);
    // CMD
    MT_EXPECT_EQ((int)buf[3], (int)cfg::kCmdTxRecordStart);
    // END 位必须置位 (单包语义)
    MT_EXPECT_TRUE((buf[4] & cfg::kFrameEndBit) != 0);
    // SIZE
    MT_EXPECT_EQ((int)buf[5], 0);
}

MT_TEST(RemoteFrame, EncodeOutboundFrameWithPayload) {
    uint8_t buf[32] = {0};
    uint8_t payload[3] = {0xAA, 0xBB, 0xCC};
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxButton, payload, sizeof(payload), buf, sizeof(buf));
    MT_EXPECT_EQ((int)n, (int)(cfg::kFrameHeadLen + sizeof(payload)));
    MT_EXPECT_BYTES_EQ(buf, cfg::kFrameHeadOutbound, 3);
    MT_EXPECT_EQ((int)buf[3], (int)cfg::kCmdTxButton);
    MT_EXPECT_EQ((int)buf[5], (int)sizeof(payload));
    MT_EXPECT_BYTES_EQ(buf + cfg::kFrameHeadLen, payload, sizeof(payload));
}

MT_TEST(RemoteFrame, EncodeOutboundFrameRejectsNullBuf) {
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxMark, nullptr, 0, nullptr, 0);
    MT_EXPECT_EQ((int)n, 0);
}

MT_TEST(RemoteFrame, EncodeOutboundFrameRejectsOversizedPayload) {
    uint8_t buf[300] = {0};
    // size > kFrameMaxData 必须拒绝
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxButton, buf, cfg::kFrameMaxData + 1, buf, sizeof(buf));
    MT_EXPECT_EQ((int)n, 0);
}

MT_TEST(RemoteFrame, EncodeOutboundFrameRejectsInsufficientCapacity) {
    uint8_t buf[16] = {0};
    uint8_t payload[20] = {0};
    // out_cap < head + size 必须拒绝
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxButton, payload, sizeof(payload), buf, sizeof(buf));
    MT_EXPECT_EQ((int)n, 0);
}

MT_TEST(RemoteFrame, EncodeOutboundFrameSnLowSevenBits) {
    uint8_t buf1[16] = {0};
    uint8_t buf2[16] = {0};
    RemoteFrame::EncodeOutboundFrame(cfg::kCmdTxMark, nullptr, 0, buf1, sizeof(buf1));
    RemoteFrame::EncodeOutboundFrame(cfg::kCmdTxMark, nullptr, 0, buf2, sizeof(buf2));
    uint8_t sn1 = buf1[4] & 0x7F;
    uint8_t sn2 = buf2[4] & 0x7F;
    MT_EXPECT_EQ((int)sn2, (int)((sn1 + 1) & 0x7F));
    // END 位都是置位的
    MT_EXPECT_TRUE((buf1[4] & cfg::kFrameEndBit) != 0);
    MT_EXPECT_TRUE((buf2[4] & cfg::kFrameEndBit) != 0);
}

// -----------------------------------------------------------------------------
// DecodeInboundFrame: 头校验 / 长度自洽 / data 指针 / END 解析
// -----------------------------------------------------------------------------
MT_TEST(RemoteFrame, DecodeInboundFrameZeroPayload) {
    uint8_t buf[8] = {
        cfg::kFrameHeadInbound[0],
        cfg::kFrameHeadInbound[1],
        cfg::kFrameHeadInbound[2],
        cfg::kCmdRxShutdown,
        (uint8_t)(cfg::kFrameEndBit | 0x05),
        0,            // SIZE
        0xDE, 0xAD,   // 多余 payload, 应被忽略
    };
    InboundFrame f{};
    bool ok = RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f);
    MT_REQUIRE_TRUE(ok);
    MT_EXPECT_EQ((int)f.cmd, (int)cfg::kCmdRxShutdown);
    MT_EXPECT_EQ((int)f.sn,  5);
    MT_EXPECT_TRUE(f.end);
    MT_EXPECT_EQ((int)f.size, 0);
    MT_EXPECT_TRUE(f.data == nullptr);
}

MT_TEST(RemoteFrame, DecodeInboundFrameWithPayload) {
    uint8_t buf[16] = {
        cfg::kFrameHeadInbound[0],
        cfg::kFrameHeadInbound[1],
        cfg::kFrameHeadInbound[2],
        cfg::kCmdRxPeerToken,
        (uint8_t)(0x00 | 0x10),  // END=0, SN=0x10
        6,                       // SIZE=6
        '1','2','3','4','5','6'  // payload
    };
    InboundFrame f{};
    bool ok = RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f);
    MT_REQUIRE_TRUE(ok);
    MT_EXPECT_EQ((int)f.cmd, (int)cfg::kCmdRxPeerToken);
    MT_EXPECT_EQ((int)f.sn,  0x10);
    MT_EXPECT_FALSE(f.end);
    MT_EXPECT_EQ((int)f.size, 6);
    MT_REQUIRE_TRUE(f.data != nullptr);
    MT_EXPECT_BYTES_EQ(f.data, "123456", 6);
}

MT_TEST(RemoteFrame, DecodeInboundFrameRejectsNullBuf) {
    InboundFrame f{};
    MT_EXPECT_FALSE(RemoteFrame::DecodeInboundFrame(nullptr, 100, f));
}

MT_TEST(RemoteFrame, DecodeInboundFrameRejectsTruncatedHeader) {
    uint8_t buf[2] = {cfg::kFrameHeadInbound[0], cfg::kFrameHeadInbound[1]};
    InboundFrame f{};
    MT_EXPECT_FALSE(RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f));
}

MT_TEST(RemoteFrame, DecodeInboundFrameRejectsBadHeader) {
    uint8_t buf[8] = {0};
    buf[0] = 0xAB;  // 错的头
    buf[2] = 0xCD;
    InboundFrame f{};
    MT_EXPECT_FALSE(RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f));
}

MT_TEST(RemoteFrame, DecodeInboundFrameToleratesByte1Mismatch) {
    // 实现注释里说: 仅校验 buf[0] / buf[2], 第 1 字节宽松匹配
    uint8_t buf[8] = {
        cfg::kFrameHeadInbound[0],
        (uint8_t)(cfg::kFrameHeadInbound[1] ^ 0xFF),  // 故意改坏
        cfg::kFrameHeadInbound[2],
        cfg::kCmdRxDisconnect,
        cfg::kFrameEndBit,
        0
    };
    InboundFrame f{};
    bool ok = RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f);
    MT_EXPECT_TRUE(ok);
    if (ok) {
        MT_EXPECT_EQ((int)f.cmd, (int)cfg::kCmdRxDisconnect);
    }
}

MT_TEST(RemoteFrame, DecodeInboundFrameRejectsOversizedSize) {
    // SIZE 字段声称比实际剩余字节还多 -> 必须拒绝, 防越界读
    uint8_t buf[8] = {
        cfg::kFrameHeadInbound[0],
        cfg::kFrameHeadInbound[1],
        cfg::kFrameHeadInbound[2],
        cfg::kCmdRxPeerToken,
        cfg::kFrameEndBit,
        100,           // SIZE=100, 但 buf 只剩 2 字节 payload 空间
        0, 0
    };
    InboundFrame f{};
    MT_EXPECT_FALSE(RemoteFrame::DecodeInboundFrame(buf, sizeof(buf), f));
}

// -----------------------------------------------------------------------------
// Round-trip: encode -> decode (用入向头模拟自收, 验证字段语义一致)
// -----------------------------------------------------------------------------
MT_TEST(RemoteFrame, EncodeDecodeRoundTripUsingInboundHead) {
    uint8_t enc[32] = {0};
    uint8_t payload[4] = {0x01, 0x02, 0x03, 0x04};
    size_t n = RemoteFrame::EncodeOutboundFrame(
        cfg::kCmdTxButton, payload, sizeof(payload), enc, sizeof(enc));
    MT_REQUIRE_TRUE(n > 0);

    // 复制一份, 把头改成入向头, 让 Decode 能接受 (Decode 校验入向头)
    uint8_t dec_buf[32] = {0};
    std::memcpy(dec_buf, enc, n);
    dec_buf[0] = cfg::kFrameHeadInbound[0];
    dec_buf[1] = cfg::kFrameHeadInbound[1];
    dec_buf[2] = cfg::kFrameHeadInbound[2];

    InboundFrame f{};
    bool ok = RemoteFrame::DecodeInboundFrame(dec_buf, n, f);
    MT_REQUIRE_TRUE(ok);
    MT_EXPECT_EQ((int)f.cmd, (int)cfg::kCmdTxButton);
    MT_EXPECT_TRUE(f.end);
    MT_EXPECT_EQ((int)f.size, (int)sizeof(payload));
    MT_REQUIRE_TRUE(f.data != nullptr);
    MT_EXPECT_BYTES_EQ(f.data, payload, sizeof(payload));
}
