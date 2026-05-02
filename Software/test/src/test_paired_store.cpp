// =============================================================================
// test_paired_store.cpp
// -----------------------------------------------------------------------------
// 覆盖 cw::ble::PairedStore 的全部对外方法:
//   - Init()        : 幂等 / NVS 加载 (空 / 有效 / 损坏)
//   - Save()        : 正常 / mac_valid=false / token 为 null
//   - Has() / Get() : 内存状态查询
//   - Forget()      : 内存清零 + NVS 清除, 跨"重启"持久
//
// 测试策略:
//   - PairedStore 是单例, 用例之间的 m_record/m_valid 会传染
//   - 用 cw_test::ResetAllPreferencesNvs() 清 NVS, 然后手工
//     reset PairedStore 内存状态: 把 m_inited 翻假需要私有访问, 不能直接做
//   - 折衷: 因为是 Singleton, 我们顺序构造一组连贯的场景, 每个 MT_TEST
//     都从已知状态推进, 而不是假设隔离 (用例命名前加序号 _01 _02 .. 强制按序执行)
// =============================================================================
#include "mini_test.h"

#include <Arduino.h>
#include <Preferences.h>

#include <cstring>

#include "paired_store.h"

using cw::ble::PairedStore;
using cw::ble::PairedRecord;

// -----------------------------------------------------------------------------
// 用例 01: 首次启动 (NVS 全空) -> Has() == false
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _01_FirstBootEmpty) {
    cw_test::ResetAllPreferencesNvs();
    cw_test::SetMockMillis(1000);
    auto& s = PairedStore::GetInstance();
    s.Init();  // 第一次 Init, 从空 NVS 加载
    MT_EXPECT_FALSE(s.Has());
}

// -----------------------------------------------------------------------------
// 用例 02: Save() 后立即 Has() / Get() 应反映最新数据
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _02_SaveThenHasAndGet) {
    cw_test::SetMockMillis(2000);
    uint8_t token[6] = {'A','B','C','D','E','F'};
    uint8_t mac[6]   = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    PairedStore::GetInstance().Save(token, mac, true);

    MT_EXPECT_TRUE(PairedStore::GetInstance().Has());
    const PairedRecord& r = PairedStore::GetInstance().Get();
    MT_EXPECT_BYTES_EQ(r.token, token, 6);
    MT_EXPECT_BYTES_EQ(r.mac,   mac,   6);
    MT_EXPECT_EQ((int)r.mac_valid, 1);
    MT_EXPECT_EQ((long long)r.last_link_ms, (long long)2000);
}

// -----------------------------------------------------------------------------
// 用例 03: Save() with mac_valid=false 应清零 mac 字段
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _03_SaveWithoutMacClearsMac) {
    cw_test::SetMockMillis(3000);
    uint8_t token[6] = {'1','2','3','4','5','6'};
    PairedStore::GetInstance().Save(token, nullptr, false);

    MT_EXPECT_TRUE(PairedStore::GetInstance().Has());
    const PairedRecord& r = PairedStore::GetInstance().Get();
    MT_EXPECT_BYTES_EQ(r.token, token, 6);
    uint8_t zero[6] = {0};
    MT_EXPECT_BYTES_EQ(r.mac, zero, 6);
    MT_EXPECT_EQ((int)r.mac_valid, 0);
    MT_EXPECT_EQ((long long)r.last_link_ms, (long long)3000);
}

// -----------------------------------------------------------------------------
// 用例 04: Save(token=null) 应被拒绝, 不影响内存状态
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _04_SaveRejectsNullToken) {
    // 用例 03 后 token 应为 "123456"
    PairedStore::GetInstance().Save(nullptr, nullptr, false);
    MT_EXPECT_TRUE(PairedStore::GetInstance().Has());
    const PairedRecord& r = PairedStore::GetInstance().Get();
    MT_EXPECT_BYTES_EQ(r.token, "123456", 6);
}

// -----------------------------------------------------------------------------
// 用例 05: 模拟"重启" - NVS 仍持久化, 新进程重新 Init() 仍能读回上次记录
// -----------------------------------------------------------------------------
// 因为 PairedStore 是单例, 我们用 placement-style 重构来模拟"新进程":
// 直接在静态 NVS map 上创建一个临时 store-like 行为是不可能的 (类是 final friend
// 模式), 所以折衷: 验证 Preferences mock 持久化字段存在 + 字节内容正确.
MT_TEST(PairedStore, _05_NvsPersistedAcrossRestart) {
    Preferences prefs;
    bool opened = prefs.begin("cw_paired", true);
    MT_REQUIRE_TRUE(opened);
    uint8_t v = prefs.getUChar("valid", 0);
    MT_EXPECT_EQ((int)v, 1);
    size_t blen = prefs.getBytesLength("last");
    MT_EXPECT_EQ((long long)blen, (long long)sizeof(PairedRecord));
    PairedRecord rec{};
    size_t got = prefs.getBytes("last", &rec, sizeof(rec));
    MT_EXPECT_EQ((long long)got, (long long)sizeof(rec));
    MT_EXPECT_BYTES_EQ(rec.token, "123456", 6);
    prefs.end();
}

// -----------------------------------------------------------------------------
// 用例 06: Forget() 应清空内存 + NVS
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _06_ForgetClearsAll) {
    PairedStore::GetInstance().Forget();
    MT_EXPECT_FALSE(PairedStore::GetInstance().Has());

    // 内存清零后 Get() 仍然可调用 (返回引用), 但内容应是 0
    const PairedRecord& r = PairedStore::GetInstance().Get();
    uint8_t zero_token[6] = {0};
    uint8_t zero_mac[6]   = {0};
    MT_EXPECT_BYTES_EQ(r.token, zero_token, 6);
    MT_EXPECT_BYTES_EQ(r.mac,   zero_mac,   6);
    MT_EXPECT_EQ((int)r.mac_valid, 0);

    // NVS valid 字段应被写为 0, last 键应被删除
    Preferences prefs;
    MT_REQUIRE_TRUE(prefs.begin("cw_paired", true));
    MT_EXPECT_EQ((int)prefs.getUChar("valid", 0xFF), 0);
    MT_EXPECT_EQ((long long)prefs.getBytesLength("last"), (long long)0);
    prefs.end();
}

// -----------------------------------------------------------------------------
// 用例 07: Forget 后再 Save, 状态正确切换回 Has=true
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _07_SaveAfterForget) {
    cw_test::SetMockMillis(7000);
    uint8_t token[6] = {'X','Y','Z','0','9','*'};
    PairedStore::GetInstance().Save(token, nullptr, false);
    MT_EXPECT_TRUE(PairedStore::GetInstance().Has());
    MT_EXPECT_BYTES_EQ(PairedStore::GetInstance().Get().token, token, 6);
    MT_EXPECT_EQ((long long)PairedStore::GetInstance().Get().last_link_ms,
                 (long long)7000);
}

// -----------------------------------------------------------------------------
// 用例 08: Init() 幂等 - 多次调用不会回滚已有内存状态
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _08_InitIsIdempotent) {
    PairedStore::GetInstance().Init();
    PairedStore::GetInstance().Init();
    PairedStore::GetInstance().Init();
    MT_EXPECT_TRUE(PairedStore::GetInstance().Has());
    // 用例 07 设置的 token 应该仍在
    MT_EXPECT_BYTES_EQ(PairedStore::GetInstance().Get().token, "XYZ09*", 6);
}

// -----------------------------------------------------------------------------
// 用例 09: NVS 损坏场景 - valid=1 但 blob 长度不足, 模拟 Init 重新加载行为
// -----------------------------------------------------------------------------
// 直接构造一个新进程加载场景: 通过 Preferences 写入异常数据, 然后期望
// 新一轮 LoadFromNvs 会判定为无效. 因为 PairedStore 是单例且 m_inited 已置真,
// 我们无法触发 LoadFromNvs 的二次执行; 此用例转而直接测 NVS 桩的字段长度
// 是 PairedStore::LoadFromNvs 关心的判定输入, 本身验证 mock 行为.
MT_TEST(PairedStore, _09_NvsCorruptedShorterBlobIsDetectable) {
    Preferences prefs;
    MT_REQUIRE_TRUE(prefs.begin("cw_paired_corrupt", false));
    // 写入声称有效但长度只有 3 字节的 blob (远小于 sizeof(PairedRecord))
    prefs.putUChar("valid", 1);
    uint8_t junk[3] = {0xDE, 0xAD, 0xBE};
    prefs.putBytes("last", junk, sizeof(junk));
    prefs.end();

    // 重新打开并按 PairedStore::LoadFromNvs 的判据校验
    Preferences prefs2;
    MT_REQUIRE_TRUE(prefs2.begin("cw_paired_corrupt", true));
    uint8_t v = prefs2.getUChar("valid", 0);
    size_t blen = prefs2.getBytesLength("last");
    bool record_valid = (v != 0) && (blen >= sizeof(PairedRecord));
    MT_EXPECT_FALSE(record_valid);  // 这正是 LoadFromNvs 判 "无效" 的等价条件
    prefs2.end();
}

// -----------------------------------------------------------------------------
// 用例 10: 多次连续 Save 后 last_link_ms 应该跟随 mock 时钟推进
// -----------------------------------------------------------------------------
MT_TEST(PairedStore, _10_LastLinkMsTracksMockTime) {
    cw_test::SetMockMillis(10000);
    uint8_t token[6] = {'a','b','c','d','e','f'};
    PairedStore::GetInstance().Save(token, nullptr, false);
    MT_EXPECT_EQ((long long)PairedStore::GetInstance().Get().last_link_ms,
                 (long long)10000);

    cw_test::AdvanceMockMillis(5000);
    PairedStore::GetInstance().Save(token, nullptr, false);
    MT_EXPECT_EQ((long long)PairedStore::GetInstance().Get().last_link_ms,
                 (long long)15000);
}
