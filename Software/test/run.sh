#!/usr/bin/env bash
# =============================================================================
# CyberWand BLE 模块本地单元测试 一键脚本
# -----------------------------------------------------------------------------
# 用法:
#   bash Software/test/run.sh
#
# 行为:
#   1) 在 Software/test/build/ 目录执行 cmake configure
#   2) 多线程编译 cw_ble_tests
#   3) 运行可执行, 透传退出码 (0 = 全部通过)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"

echo "[run.sh] configure -> ${BUILD_DIR}"
cmake -S "${SCRIPT_DIR}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE=Debug

echo "[run.sh] build"
cmake --build "${BUILD_DIR}" -j

echo "[run.sh] run"
"${BUILD_DIR}/cw_ble_tests"
