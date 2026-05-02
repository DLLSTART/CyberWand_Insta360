# CyberWand BLE 模块本地单元测试

> 用 **普通 g++/clang++** 在本机直接编译运行 `lib/ble/` 的纯逻辑模块,
> 不依赖 ESP32 / Arduino / FreeRTOS / NimBLE 任何嵌入式工具链.

## 目录结构

```
Software/test/
├── CMakeLists.txt              # 本地构建入口 (CMake >= 3.16)
├── run.sh                      # 一键 configure + build + run
├── README.md                   # 本文件
├── framework/
│   └── mini_test.h             # 自写零依赖极简测试框架 (含 MT_TEST 宏)
├── mocks/                      # ESP32 库桩 — 让生产代码原样编译
│   ├── Arduino.h / .cpp        #  millis() / Serial 等
│   ├── Preferences.h / .cpp    #  内存 std::map 模拟 NVS
│   └── base.h                  #  剥掉 FreeRTOS 的 base.h 替身
└── src/
    ├── test_main.cpp           # 测试入口 (调用 mini_test::Run)
    ├── test_remote_frame.cpp   # RemoteFrame  全 API 覆盖 (帧 codec)
    ├── test_paired_store.cpp   # PairedStore  全 API 覆盖 (NVS 持久化)
    └── test_command_codec.cpp  # CommandCodec / ModeRotator 全 API 覆盖
                                # (业务命令 -> BLE 字节流 协议契约)
```

## 一键运行

```bash
bash Software/test/run.sh
```

输出示例:

```
[==========] Running 24 tests from 2 suites.
[ RUN      ] RemoteFrame.HeaderLengthMatchesConfig
[       OK ] RemoteFrame.HeaderLengthMatchesConfig (0 ms)
...
[==========] 24 tests from 2 suites ran. (3 ms total)
[  PASSED  ] 24 tests.
```

## 手动分步

```bash
cd Software/test
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
./build/cw_ble_tests
# 或者用 ctest
cd build && ctest --output-on-failure
```

## 覆盖范围

| 模块                                     | 覆盖率 | 测试文件                  |
|------------------------------------------|--------|---------------------------|
| `cw::ble::RemoteFrame`  (帧 codec)       | 100%   | `test_remote_frame.cpp`   |
| `cw::ble::PairedStore`  (NVS 持久化)     | 100%   | `test_paired_store.cpp`   |
| `cw::ble::CommandCodec` (业务命令编码)   | 100%   | `test_command_codec.cpp`  |
| `cw::ble::ModeRotator`  (模式循环)       | 100%   | `test_command_codec.cpp`  |
| `cw::ble::BleRemote`    (BLE 协议栈集成) | 不覆盖 | (依赖 NimBLE, 应做 HIL)   |

### 协议契约覆盖

`test_command_codec.cpp` 把 "魔杖业务侧动作 -> BLE 字节流" 这条契约
完整固化下来, 任何会破坏协议规范的代码改动都会被立即暴露:

| 业务函数                           | 字节流断言                                                 |
|------------------------------------|------------------------------------------------------------|
| `BleRemote::SendRecordStart`       | `[3]==kCmdTxRecordStart`, payload=空, END 位置位           |
| `BleRemote::SendRecordStop`        | `[3]==kCmdTxRecordStop`,  payload=空                       |
| `BleRemote::SendHighlightMark`     | `[3]==kCmdTxMark`,        payload=空                       |
| `BleRemote::CycleToNextSubMode`    | `[3]==kCmdTxSetMode`,     payload=`[sub_mode_id]`          |
| `BleRemote::SendButton(d,b,s)`     | `[3]==kCmdTxButton`,      payload=`[d,b,s]` 顺序保留       |
| 唤醒广播 `manufacturer-data`       | `[prefix][token 6B][suffix]` 三段字节级一致, token 段隔离  |
| 子模式循环顺序                     | 第 N 次 = `kModeSwitchSeq[N % len]`, 失序立即失败           |

所有断言都走 `cfg::*` 常量, 不在测试代码里硬编码 0xA3 等具体协议值,
因此协议升级 (改 protocol.json) 无需改测试; 但任何写错命令字 / 改坏
字节顺序 / 模式循环失序的代码改动都会被立即暴露.

### 不覆盖的部分

`BleRemote` 涉及 ESP32 NimBLE 协议栈、回调注册、`BLE2902` 等 50+ 类,
要在本地完整桩接需要重写半个 BLE 库, 不符合"单元测试"的成本/收益.
其字节流拼装逻辑已经全部抽到 `CommandCodec` (本地 100% 覆盖),
`BleRemote` 的剩余风险面只剩 GATT 集成与回调时序, 适合 HIL 测试.

## 添加新测试

```cpp
// 1. 在 src/ 新建 test_foo.cpp
#include "mini_test.h"
#include "foo.h"

MT_TEST(Foo, BasicCase) {
    MT_EXPECT_EQ(Foo::Bar(1), 2);
    MT_EXPECT_BYTES_EQ("abc", "abc", 3);
}

// 2. 在 CMakeLists.txt 的 TEST_SOURCES 列表里追加 test_foo.cpp
// 3. 重新 cmake --build build 即可
```

支持的断言宏 (全部失败累计后继续, 不会立即终止):

| 宏                              | 语义                          |
|---------------------------------|-------------------------------|
| `MT_EXPECT_TRUE(cond)`          | 期望为 true                   |
| `MT_EXPECT_FALSE(cond)`         | 期望为 false                  |
| `MT_EXPECT_EQ(a, b)`            | 期望 a == b (整数语义)        |
| `MT_EXPECT_NE(a, b)`            | 期望 a != b                   |
| `MT_EXPECT_BYTES_EQ(p, q, n)`   | 期望两段内存前 n 字节相等     |
| `MT_REQUIRE_TRUE(cond)`         | 失败立即 return 本用例        |

## 注意事项

1. **协议描述符**: 测试期望 `Software/include/protocol_config.h` 已存在.
   若不存在, CMake 会自动调用 `Software/scripts/gen_protocol_config.py`
   从 `protocol.json` (优先) 或 `protocol.example.json` (fallback) 生成.
2. **PairedStore / RemoteFrame 是单例 / 静态计数器**, 用例间状态会传染.
   `test_paired_store.cpp` 的用例命名以 `_NN_` 开头, 利用 mini_test 注册顺序
   保证按序执行. 添加新用例时请保持顺序约定.
3. **mock 时钟**: `cw_test::SetMockMillis(v)` / `cw_test::AdvanceMockMillis(n)`
   控制 `millis()` 返回值, 让 `PairedStore::Save` 等依赖时间戳的逻辑可测.
4. **mock NVS**: `cw_test::ResetAllPreferencesNvs()` 清空所有命名空间数据.
