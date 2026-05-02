// =============================================================================
// mini_test.h — 极简单元测试框架 (零依赖, header-only)
// -----------------------------------------------------------------------------
// 设计目标:
//   - 不引入任何第三方库 (Catch2/doctest/gtest 都不需要)
//   - 单 header 直接包含即可使用
//   - 兼容 g++ -std=c++14 及以上
//   - 用法直观:
//       MT_TEST(suite, name) { ... MT_EXPECT_EQ(a, b); ... }
//       int main() { return mini_test::Run(); }
//
// 提供的断言宏:
//   - MT_EXPECT_TRUE(cond)        : 期望 cond 为 true,  失败计数 +1 但不停
//   - MT_EXPECT_FALSE(cond)       : 期望 cond 为 false, 失败计数 +1 但不停
//   - MT_EXPECT_EQ(a, b)          : 期望 a == b
//   - MT_EXPECT_NE(a, b)          : 期望 a != b
//   - MT_EXPECT_BYTES_EQ(p,q,n)   : 期望两段内存前 n 字节相等
//   - MT_REQUIRE_TRUE(cond)       : 同 EXPECT 但失败立即结束本用例
//
// 测试用例自注册 (类似 gtest 的 TEST 宏):
//   MT_TEST(PairedStore, FirstBootIsEmpty) {
//       PairedStore s;
//       MT_EXPECT_FALSE(s.Has());
//   }
//
// 运行:
//   int main(int argc, char** argv) { return mini_test::Run(argc, argv); }
//
// 输出格式 (PASS 走 stdout, FAIL 走 stderr 便于 CI 抓取):
//   [ RUN      ] PairedStore.FirstBootIsEmpty
//   [       OK ] PairedStore.FirstBootIsEmpty (0 ms)
//   ...
//   [==========] 12 tests from 2 suites ran. (3 ms total)
//   [  PASSED  ] 12 tests.
// =============================================================================
#pragma once
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace mini_test {

struct TestCase {
    const char* suite;
    const char* name;
    void (*fn)(int& fail_count);
};

inline std::vector<TestCase>& Registry() {
    static std::vector<TestCase> g;
    return g;
}

struct AutoRegister {
    AutoRegister(const char* suite, const char* name, void (*fn)(int&)) {
        Registry().push_back({suite, name, fn});
    }
};

inline int Run(int /*argc*/ = 0, char** /*argv*/ = nullptr) {
    using clock = std::chrono::steady_clock;
    auto t_all = clock::now();

    int total = static_cast<int>(Registry().size());
    int passed = 0, failed = 0;
    std::vector<std::string> failed_names;

    // 统计共有多少 suite (按 suite 字段去重)
    std::vector<const char*> suites;
    for (auto& tc : Registry()) {
        bool found = false;
        for (auto* s : suites) {
            if (std::strcmp(s, tc.suite) == 0) { found = true; break; }
        }
        if (!found) suites.push_back(tc.suite);
    }

    std::printf("[==========] Running %d tests from %d suites.\n",
                total, static_cast<int>(suites.size()));

    for (auto& tc : Registry()) {
        std::printf("[ RUN      ] %s.%s\n", tc.suite, tc.name);
        std::fflush(stdout);

        auto t0 = clock::now();
        int fail_in_case = 0;
        try {
            tc.fn(fail_in_case);
        } catch (const std::exception& e) {
            std::fprintf(stderr, "    EXCEPTION: %s\n", e.what());
            fail_in_case++;
        } catch (...) {
            std::fprintf(stderr, "    UNKNOWN EXCEPTION\n");
            fail_in_case++;
        }
        auto t1 = clock::now();
        long ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();

        if (fail_in_case == 0) {
            std::printf("[       OK ] %s.%s (%ld ms)\n", tc.suite, tc.name, ms);
            passed++;
        } else {
            std::fprintf(stderr,
                         "[  FAILED  ] %s.%s (%ld ms, %d assert failures)\n",
                         tc.suite, tc.name, ms, fail_in_case);
            failed++;
            failed_names.push_back(std::string(tc.suite) + "." + tc.name);
        }
    }

    auto t_end = clock::now();
    long total_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t_end - t_all).count();
    std::printf("[==========] %d tests from %d suites ran. (%ld ms total)\n",
                total, static_cast<int>(suites.size()), total_ms);
    std::printf("[  PASSED  ] %d tests.\n", passed);
    if (failed > 0) {
        std::fprintf(stderr, "[  FAILED  ] %d tests, listed below:\n", failed);
        for (auto& n : failed_names) {
            std::fprintf(stderr, "[  FAILED  ] %s\n", n.c_str());
        }
        return 1;
    }
    return 0;
}

}  // namespace mini_test

// ========== 注册宏 ==========
#define MT_TEST(suite, name)                                                   \
    static void mt_##suite##_##name(int& __mt_fail);                           \
    static ::mini_test::AutoRegister mt_reg_##suite##_##name(                  \
        #suite, #name, &mt_##suite##_##name);                                  \
    static void mt_##suite##_##name(int& __mt_fail)

// ========== 断言宏 ==========
#define MT_EXPECT_TRUE(cond)                                                   \
    do {                                                                       \
        bool __c = (bool)(cond);                                               \
        if (!__c) {                                                            \
            std::fprintf(stderr,                                               \
                "    [FAIL] %s:%d: expected TRUE: %s\n",                       \
                __FILE__, __LINE__, #cond);                                    \
            __mt_fail++;                                                       \
        }                                                                      \
    } while (0)

#define MT_EXPECT_FALSE(cond)                                                  \
    do {                                                                       \
        bool __c = (bool)(cond);                                               \
        if (__c) {                                                             \
            std::fprintf(stderr,                                               \
                "    [FAIL] %s:%d: expected FALSE: %s\n",                      \
                __FILE__, __LINE__, #cond);                                    \
            __mt_fail++;                                                       \
        }                                                                      \
    } while (0)

#define MT_EXPECT_EQ(a, b)                                                     \
    do {                                                                       \
        auto __a = (a);                                                        \
        auto __b = (b);                                                        \
        if (!(__a == __b)) {                                                   \
            std::fprintf(stderr,                                               \
                "    [FAIL] %s:%d: expected %s == %s, got lhs=%lld rhs=%lld\n",\
                __FILE__, __LINE__, #a, #b,                                    \
                (long long)__a, (long long)__b);                               \
            __mt_fail++;                                                       \
        }                                                                      \
    } while (0)

#define MT_EXPECT_NE(a, b)                                                     \
    do {                                                                       \
        auto __a = (a);                                                        \
        auto __b = (b);                                                        \
        if ((__a == __b)) {                                                    \
            std::fprintf(stderr,                                               \
                "    [FAIL] %s:%d: expected %s != %s, both = %lld\n",          \
                __FILE__, __LINE__, #a, #b, (long long)__a);                   \
            __mt_fail++;                                                       \
        }                                                                      \
    } while (0)

#define MT_EXPECT_BYTES_EQ(p, q, n)                                            \
    do {                                                                       \
        const uint8_t* __p = (const uint8_t*)(p);                              \
        const uint8_t* __q = (const uint8_t*)(q);                              \
        size_t __n = (size_t)(n);                                              \
        if (__p == nullptr || __q == nullptr) {                                \
            std::fprintf(stderr,                                               \
                "    [FAIL] %s:%d: BYTES_EQ null ptr (p=%p q=%p)\n",           \
                __FILE__, __LINE__, (void*)__p, (void*)__q);                   \
            __mt_fail++;                                                       \
            break;                                                             \
        }                                                                      \
        size_t __i;                                                            \
        for (__i = 0; __i < __n; __i++) {                                      \
            if (__p[__i] != __q[__i]) {                                        \
                std::fprintf(stderr,                                           \
                    "    [FAIL] %s:%d: byte mismatch at idx %zu "              \
                    "(lhs=0x%02X rhs=0x%02X)\n",                               \
                    __FILE__, __LINE__, __i, __p[__i], __q[__i]);              \
                __mt_fail++;                                                   \
                break;                                                         \
            }                                                                  \
        }                                                                      \
    } while (0)

#define MT_REQUIRE_TRUE(cond)                                                  \
    do {                                                                       \
        bool __c = (bool)(cond);                                               \
        if (!__c) {                                                            \
            std::fprintf(stderr,                                               \
                "    [FATAL] %s:%d: REQUIRE FAILED: %s\n",                     \
                __FILE__, __LINE__, #cond);                                    \
            __mt_fail++;                                                       \
            return;                                                            \
        }                                                                      \
    } while (0)
