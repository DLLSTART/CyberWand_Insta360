// =============================================================================
// 测试主入口
// -----------------------------------------------------------------------------
// 启动方式:
//   ./cw_ble_tests              # 跑全部用例
//
// 命令行参数当前未实现过滤功能 (mini_test 框架保持极简).
// 如果用例增多需要做 --gtest_filter 之类的过滤, 再扩展 mini_test::Run.
// =============================================================================
#include "mini_test.h"

#include <Arduino.h>

int main(int argc, char** argv) {
    // 测试用例之间不应共享 millis/Serial 状态; 这里给个干净起点.
    cw_test::SetMockMillis(0);
    cw_test::EnableSerialEcho(false);
    return mini_test::Run(argc, argv);
}
