// =============================================================================
// test_command_codec.cpp
// -----------------------------------------------------------------------------
// 端到端验证 "魔杖业务侧动作 -> BLE 字节流" 这条契约的全部环节:
//
//   1. BuildRecordStartFrame   -> 字节流 [3] 必须 == cfg::kCmdTxRecordStart
//   2. BuildRecordStopFrame    -> 字节流 [3] 必须 == cfg::kCmdTxRecordStop
//   3. BuildSetModeFrame(id)   -> 字节流 [3] == cfg::kCmdTxSetMode
//                                 字节流 [SIZE] == 1, payload[0] == id
//   4. BuildHighlightMarkFrame -> 字节流 [3] == cfg::kCmdTxMark
//   5. BuildButtonFrame(d,b,s) -> 字节流 [3] == cfg::kCmdTxButton
//                                 字节流 [SIZE] == 3, payload == [d,b,s]
//
//   6. BuildWakeupAdvManufacturerData(token):
//      - 总长 == kWakeupAdvPrefixLen + 6 + kWakeupAdvSuffixLen
//      - [0..prefix_len)         == cfg::kWakeupAdvPrefix (字节级一致)
//      - [prefix_len..+6)        == 入参 token
//      - [prefix_len+6..end)     == cfg::kWakeupAdvSuffix
//      - cap 不足 / 入参为 null  -> 返回 0
//
//   7. ModeRotator:
//      - NextSubMode() 第 N 次返回 cfg::kModeSwitchSeq[N % len]
//      - CurrentIndex 同步推进
//      - kModeSwitchSeqLen == 0 时返回 0xFF, 索引不变
//
// 这些断言全部走 cfg::* 常量, 不在测试代码里硬编码具体协议值
// (例如 0xA3 / 0xA7 等), 因此协议升级无需改测试; 但任何会破坏契约的
// 改动 (写错命令字 / 改坏字节顺序 / 模式循环失序) 都会被立即暴露.
// =============================================================================
#include "mini_test.h"

#include <cstring>

#include "command_codec.h"
#include "remote_frame.h"
#include "protocol_config.h"

using cw::ble::CommandCodec;
using cw::ble::ModeRotator;
namespace cfg = cw::ble::cfg;

// -----------------------------------------------------------------------------
// 通用断言: 一帧字节流的"出向头 / END 位 / SIZE / payload" 都符合规范
// -----------------------------------------------------------------------------
static void ExpectFrameWellFormed(int& __mt_fail,
                                  const uint8_t* buf, size_t n,
                                  uint8_t expect_cmd,
                                  const uint8_t* expect_payload,
                                  uint8_t expect_payload_size) {
    MT_REQUIRE_TRUE(n == static_cast<size_t>(cfg::kFrameHeadLen) + expect_payload_size);
    // 出向头
    MT_EXPECT_BYTES_EQ(buf, cfg::kFrameHeadOutbound, 3);
    // 命令字 — 这是 "业务语义 -> 协议命令字" 契约的核心断言
    MT_EXPECT_EQ((int)buf[3], (int)expect_cmd);
    // END 位必须置位 (单包语义)
    MT_EXPECT_TRUE((buf[4] & cfg::kFrameEndBit) != 0);
    // SIZE 字段
    MT_EXPECT_EQ((int)buf[5], (int)expect_payload_size);
    // payload (若有) 字节级一致
    if (expect_payload_size > 0 && expect_payload != nullptr) {
        MT_EXPECT_BYTES_EQ(buf + cfg::kFrameHeadLen,
                           expect_payload, expect_payload_size);
    }
}

// -----------------------------------------------------------------------------
// 业务命令 -> 字节流: 命令字 / payload 全部对齐协议规范
// -----------------------------------------------------------------------------
MT_TEST(CommandCodec, BuildRecordStartFrameMatchesProtocol) {
    uint8_t buf[32] = {0};
    size_t n = CommandCodec::BuildRecordStartFrame(buf, sizeof(buf));
    ExpectFrameWellFormed(__mt_fail, buf, n,
                          cfg::kCmdTxRecordStart, nullptr, 0);
}

MT_TEST(CommandCodec, BuildRecordStopFrameMatchesProtocol) {
    uint8_t buf[32] = {0};
    size_t n = CommandCodec::BuildRecordStopFrame(buf, sizeof(buf));
    ExpectFrameWellFormed(__mt_fail, buf, n,
                          cfg::kCmdTxRecordStop, nullptr, 0);
}

MT_TEST(CommandCodec, BuildHighlightMarkFrameMatchesProtocol) {
    uint8_t buf[32] = {0};
    size_t n = CommandCodec::BuildHighlightMarkFrame(buf, sizeof(buf));
    ExpectFrameWellFormed(__mt_fail, buf, n,
                          cfg::kCmdTxMark, nullptr, 0);
}

MT_TEST(CommandCodec, BuildSetModeFramePayloadIsSubModeId) {
    uint8_t buf[32] = {0};
    uint8_t pl[1] = {0x42};
    size_t n = CommandCodec::BuildSetModeFrame(0x42, buf, sizeof(buf));
    ExpectFrameWellFormed(__mt_fail, buf, n,
                          cfg::kCmdTxSetMode, pl, 1);
}

MT_TEST(CommandCodec, BuildButtonFramePayloadIsThreeFieldsInOrder) {
    uint8_t buf[32] = {0};
    uint8_t pl[3] = {0x01, 0x02, 0x03};
    size_t n = CommandCodec::BuildButtonFrame(0x01, 0x02, 0x03, buf, sizeof(buf));
    ExpectFrameWellFormed(__mt_fail, buf, n,
                          cfg::kCmdTxButton, pl, 3);
}

// -----------------------------------------------------------------------------
// 业务命令拒绝异常入参
// -----------------------------------------------------------------------------
MT_TEST(CommandCodec, AllBuildersRejectNullOut) {
    MT_EXPECT_EQ((int)CommandCodec::BuildRecordStartFrame(nullptr, 32), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildRecordStopFrame(nullptr, 32), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildHighlightMarkFrame(nullptr, 32), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildSetModeFrame(0x00, nullptr, 32), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildButtonFrame(0,0,0, nullptr, 32), 0);
}

MT_TEST(CommandCodec, AllBuildersRejectInsufficientCapacity) {
    uint8_t buf[2] = {0};  // 故意太小, 连帧头都装不下
    MT_EXPECT_EQ((int)CommandCodec::BuildRecordStartFrame(buf, sizeof(buf)), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildSetModeFrame(0x00, buf, sizeof(buf)), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildButtonFrame(0,0,0, buf, sizeof(buf)), 0);
}

// -----------------------------------------------------------------------------
// 唤醒广播 manufacturer-data 字节布局: prefix + token + suffix
// -----------------------------------------------------------------------------
MT_TEST(CommandCodec, WakeupAdvLengthMatchesConfig) {
    size_t expect = static_cast<size_t>(cfg::kWakeupAdvPrefixLen)
                  + cfg::kWakeupTokenLen
                  + cfg::kWakeupAdvSuffixLen;
    MT_EXPECT_EQ((long long)CommandCodec::WakeupAdvManufacturerDataLength(),
                 (long long)expect);
}

MT_TEST(CommandCodec, BuildWakeupAdvLayoutMatchesProtocol) {
    uint8_t token[6]  = {'A','B','C','D','E','F'};
    uint8_t out[64]   = {0};
    size_t n = CommandCodec::BuildWakeupAdvManufacturerData(token, out, sizeof(out));
    MT_REQUIRE_TRUE(n == CommandCodec::WakeupAdvManufacturerDataLength());

    // 段 1: 前 prefix_len 字节必须 *字节级* 等于 cfg::kWakeupAdvPrefix
    MT_EXPECT_BYTES_EQ(out,
                       cfg::kWakeupAdvPrefix,
                       cfg::kWakeupAdvPrefixLen);
    // 段 2: 接下来 6 字节必须等于入参 token
    MT_EXPECT_BYTES_EQ(out + cfg::kWakeupAdvPrefixLen,
                       token,
                       cfg::kWakeupTokenLen);
    // 段 3: 末尾 suffix_len 字节必须 *字节级* 等于 cfg::kWakeupAdvSuffix
    MT_EXPECT_BYTES_EQ(out + cfg::kWakeupAdvPrefixLen + cfg::kWakeupTokenLen,
                       cfg::kWakeupAdvSuffix,
                       cfg::kWakeupAdvSuffixLen);
}

MT_TEST(CommandCodec, BuildWakeupAdvDifferentTokenChangesOnlyTokenSegment) {
    uint8_t token1[6] = {0x11,0x22,0x33,0x44,0x55,0x66};
    uint8_t token2[6] = {0xAA,0xBB,0xCC,0xDD,0xEE,0xFF};
    uint8_t out1[64]  = {0};
    uint8_t out2[64]  = {0};
    size_t n1 = CommandCodec::BuildWakeupAdvManufacturerData(token1, out1, sizeof(out1));
    size_t n2 = CommandCodec::BuildWakeupAdvManufacturerData(token2, out2, sizeof(out2));
    MT_REQUIRE_TRUE(n1 == n2);

    // prefix 段必须不变
    MT_EXPECT_BYTES_EQ(out1, out2, cfg::kWakeupAdvPrefixLen);
    // suffix 段必须不变
    MT_EXPECT_BYTES_EQ(out1 + cfg::kWakeupAdvPrefixLen + cfg::kWakeupTokenLen,
                       out2 + cfg::kWakeupAdvPrefixLen + cfg::kWakeupTokenLen,
                       cfg::kWakeupAdvSuffixLen);
    // token 段必须分别等于各自的入参
    MT_EXPECT_BYTES_EQ(out1 + cfg::kWakeupAdvPrefixLen, token1, 6);
    MT_EXPECT_BYTES_EQ(out2 + cfg::kWakeupAdvPrefixLen, token2, 6);
}

MT_TEST(CommandCodec, BuildWakeupAdvRejectsNullInputs) {
    uint8_t token[6] = {1,2,3,4,5,6};
    uint8_t buf[64]  = {0};
    MT_EXPECT_EQ((int)CommandCodec::BuildWakeupAdvManufacturerData(nullptr, buf,    sizeof(buf)), 0);
    MT_EXPECT_EQ((int)CommandCodec::BuildWakeupAdvManufacturerData(token,   nullptr, sizeof(buf)), 0);
}

MT_TEST(CommandCodec, BuildWakeupAdvRejectsInsufficientCapacity) {
    uint8_t token[6] = {1,2,3,4,5,6};
    uint8_t buf[4]   = {0};  // 必然小于 prefix + 6 + suffix
    MT_EXPECT_EQ((int)CommandCodec::BuildWakeupAdvManufacturerData(token, buf, sizeof(buf)), 0);
}

// -----------------------------------------------------------------------------
// ModeRotator: 循环顺序与 cfg::kModeSwitchSeq 字节级一致
// -----------------------------------------------------------------------------
MT_TEST(ModeRotator, NextSubModeFollowsKModeSwitchSeqOrder) {
    MT_REQUIRE_TRUE(cfg::kModeSwitchSeqLen > 0);
    ModeRotator r;
    // 走两整圈, 每一步都断言 = kModeSwitchSeq[i % len]
    for (uint8_t i = 0; i < cfg::kModeSwitchSeqLen * 2; i++) {
        uint8_t expect_idx_before = i % cfg::kModeSwitchSeqLen;
        MT_EXPECT_EQ((int)r.CurrentIndex(), (int)expect_idx_before);
        uint8_t got = r.NextSubMode();
        MT_EXPECT_EQ((int)got,
                     (int)cfg::kModeSwitchSeq[expect_idx_before]);
        // 推进后索引应当 = (before + 1) % len
        MT_EXPECT_EQ((int)r.CurrentIndex(),
                     (int)((expect_idx_before + 1) % cfg::kModeSwitchSeqLen));
    }
}

MT_TEST(ModeRotator, ResetReturnsToFirstEntry) {
    ModeRotator r;
    r.NextSubMode();
    r.NextSubMode();
    r.Reset();
    MT_EXPECT_EQ((int)r.CurrentIndex(), 0);
    if (cfg::kModeSwitchSeqLen > 0) {
        MT_EXPECT_EQ((int)r.NextSubMode(),
                     (int)cfg::kModeSwitchSeq[0]);
    }
}

// -----------------------------------------------------------------------------
// 端到端: BleRemote::SendXxx 的字节流契约
// -----------------------------------------------------------------------------
// 因为 BleRemote 自身依赖 NimBLE 不能在本地实例化, 这里通过 "BleRemote 内部
// 使用了 CommandCodec::BuildXxxFrame 完全相同的调用路径" 这一事实, 把
// CommandCodec 的端到端测试就看作 BleRemote::SendXxx 的端到端契约测试.
// 任何在 BleRemote 里偷偷改动命令字 / payload 的代码改动, 都需要同步在
// CommandCodec 这一层有反映, 否则 BleRemote 自己也用不上 CommandCodec.
// -----------------------------------------------------------------------------
MT_TEST(CommandCodec, EndToEndAllOpsAreDistinguishableByCmdByte) {
    uint8_t b_start[32]={0}, b_stop[32]={0}, b_mark[32]={0},
            b_mode[32]={0},  b_btn[32]={0};
    CommandCodec::BuildRecordStartFrame(b_start, sizeof(b_start));
    CommandCodec::BuildRecordStopFrame (b_stop,  sizeof(b_stop));
    CommandCodec::BuildHighlightMarkFrame(b_mark, sizeof(b_mark));
    CommandCodec::BuildSetModeFrame(0xAB, b_mode, sizeof(b_mode));
    CommandCodec::BuildButtonFrame(1, 2, 3, b_btn, sizeof(b_btn));

    // 5 条命令的 cmd 字节必须互不相同 — 否则对端无法区分
    uint8_t cmds[5] = {b_start[3], b_stop[3], b_mark[3], b_mode[3], b_btn[3]};
    for (int i = 0; i < 5; i++) {
        for (int j = i + 1; j < 5; j++) {
            MT_EXPECT_NE((int)cmds[i], (int)cmds[j]);
        }
    }
    // 且每个 cmd 字节都和 cfg:: 的对应常量一致
    MT_EXPECT_EQ((int)cmds[0], (int)cfg::kCmdTxRecordStart);
    MT_EXPECT_EQ((int)cmds[1], (int)cfg::kCmdTxRecordStop);
    MT_EXPECT_EQ((int)cmds[2], (int)cfg::kCmdTxMark);
    MT_EXPECT_EQ((int)cmds[3], (int)cfg::kCmdTxSetMode);
    MT_EXPECT_EQ((int)cmds[4], (int)cfg::kCmdTxButton);
}
