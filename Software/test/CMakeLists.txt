# =============================================================================
# CyberWand BLE 模块本地单元测试 CMake 入口
# -----------------------------------------------------------------------------
# 设计目标:
#   - 在 *Linux/macOS 本机* 用普通 g++ / clang++ 编译, 不依赖 ESP32 工具链
#   - 不依赖任何第三方测试框架 (使用 framework/mini_test.h 自写极简框架)
#   - 不依赖任何 Arduino / FreeRTOS / NimBLE 库 (用 mocks/ 桩代替)
#
# 用法:
#   cd Software/test
#   cmake -S . -B build
#   cmake --build build -j
#   ./build/cw_ble_tests
#
# 或者直接:
#   bash Software/test/run.sh
# =============================================================================

cmake_minimum_required(VERSION 3.16)
project(cw_ble_tests CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "" FORCE)
endif()

# 严格的告警, 防止 mock 与生产代码偏离
add_compile_options(
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-format
    -Wno-narrowing
    -fno-omit-frame-pointer
)

# 把生产代码的 lib/base/base.h FreeRTOS 路径完全屏蔽 — 我们用 mocks/base.h 替身
# 通过把 mocks/ 路径放在最前面, 让 #include "base.h" 优先解析到桩.
# 同样 #include <Arduino.h> / #include <Preferences.h> 也走 mocks/.
set(REPO_ROOT     "${CMAKE_CURRENT_SOURCE_DIR}/../..")
set(SW_ROOT       "${REPO_ROOT}/Software")
set(TEST_ROOT     "${CMAKE_CURRENT_SOURCE_DIR}")
set(MOCKS_DIR     "${TEST_ROOT}/mocks")
set(FRAMEWORK_DIR "${TEST_ROOT}/framework")
set(BLE_DIR       "${SW_ROOT}/lib/ble")
set(CNN_DIR       "${SW_ROOT}/lib/cnn")
set(COMMON_DIR    "${SW_ROOT}/lib/common")

# -----------------------------------------------------------------------------
# 步骤 1: 确保 protocol_config.h 已生成
# -----------------------------------------------------------------------------
# 该文件由 Software/scripts/gen_protocol_config.py 从 protocol.json
# (优先) 或 protocol.example.json (fallback) 生成, 平时由 PlatformIO 钩子触发.
# 本地测试如果未跑过 PIO 构建, 这里手动调用一次, 让脚本 fallback 用 example.
# -----------------------------------------------------------------------------
set(PROTOCOL_HEADER "${SW_ROOT}/include/protocol_config.h")
if(NOT EXISTS "${PROTOCOL_HEADER}")
    message(STATUS "protocol_config.h not found, generating via python script ...")
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${SW_ROOT}/scripts/gen_protocol_config.py"
        WORKING_DIRECTORY "${SW_ROOT}"
        RESULT_VARIABLE _gen_rc
        OUTPUT_VARIABLE _gen_out
        ERROR_VARIABLE  _gen_err
    )
    if(NOT _gen_rc EQUAL 0)
        message(FATAL_ERROR
            "Failed to generate protocol_config.h:\n"
            "stdout: ${_gen_out}\n"
            "stderr: ${_gen_err}")
    endif()
    message(STATUS "${_gen_out}")
endif()

# -----------------------------------------------------------------------------
# 步骤 2: include 路径顺序 — mocks 必须在最前面
# -----------------------------------------------------------------------------
include_directories(
    "${MOCKS_DIR}"           # Arduino.h / Preferences.h / base.h 桩
    "${FRAMEWORK_DIR}"       # mini_test.h
    "${SW_ROOT}/include"     # protocol_config.h (脚本生成)
    "${BLE_DIR}"             # ble_remote.h / paired_store.h / remote_frame.h / command_codec.h
    "${CNN_DIR}"             # imu_resampler.h
    "${COMMON_DIR}"          # common.h (cw::common::IMU 数据结构)
)

# -----------------------------------------------------------------------------
# 步骤 3: 收集源文件
# -----------------------------------------------------------------------------
# 注意: 不编译 ble_remote.cpp - 它依赖 ESP32 NimBLE 头, 本地无法替身完整的
#       BLEDevice/BLEServer 等 50+ 类. 测 BLE 回调状态机是 "硬件在环" 的事,
#       本地单元测试聚焦在纯逻辑模块 (RemoteFrame + PairedStore + CommandCodec).
set(PRODUCTION_SOURCES
    "${BLE_DIR}/remote_frame.cpp"
    "${BLE_DIR}/paired_store.cpp"
    "${BLE_DIR}/command_codec.cpp"
    "${CNN_DIR}/imu_resampler.cpp"
)

set(MOCK_SOURCES
    "${MOCKS_DIR}/Arduino.cpp"
    "${MOCKS_DIR}/Preferences.cpp"
)

set(TEST_SOURCES
    "${TEST_ROOT}/src/test_main.cpp"
    "${TEST_ROOT}/src/test_remote_frame.cpp"
    "${TEST_ROOT}/src/test_paired_store.cpp"
    "${TEST_ROOT}/src/test_command_codec.cpp"
    "${TEST_ROOT}/src/test_imu_resampler.cpp"
)

# -----------------------------------------------------------------------------
# 步骤 4: 构建测试可执行
# -----------------------------------------------------------------------------
add_executable(cw_ble_tests
    ${PRODUCTION_SOURCES}
    ${MOCK_SOURCES}
    ${TEST_SOURCES}
)

# 让 ctest 也能调度
enable_testing()
add_test(NAME cw_ble_tests COMMAND cw_ble_tests)

message(STATUS "")
message(STATUS "=== CyberWand BLE local unit tests ===")
message(STATUS "  Build type   : ${CMAKE_BUILD_TYPE}")
message(STATUS "  Source files : ${PRODUCTION_SOURCES}")
message(STATUS "  Build with   : cmake --build ${CMAKE_BINARY_DIR} -j")
message(STATUS "  Run with     : ${CMAKE_BINARY_DIR}/cw_ble_tests")
message(STATUS "")
