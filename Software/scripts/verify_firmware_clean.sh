#!/usr/bin/env bash
# =============================================================================
# verify_firmware_clean.sh
# -----------------------------------------------------------------------------
# 验证 "Software/test/ 下的单元测试代码绝对不会进入烧录到 ESP32 的固件" 这一契约.
#
# 检查点:
#   1) Software/.pio/build/ 下不存在 test_*.o / mocks/* / mini_test* 任何对象文件
#   2) firmware.elf 中不存在 mini_test / cw_test / HardwareSerialMock 任何符号
#   3) ble 模块的 4 个 .o (ble_remote / remote_frame / paired_store / command_codec)
#      都已被链接进固件
#   4) 旧名 paired_peer_store / bond_store 没有任何残留
#
# 用法:
#   cd Software
#   pio run                          # 先确保固件已编译
#   bash scripts/verify_firmware_clean.sh
#
# 退出码:
#   0  全部检查通过
#   非 0  有违反契约的项
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
# PIO build dir 由 platformio.ini 中 [env:NAME] 决定, 当前 env 名 = "cyberwand"
# (硬件 board 已切换到 esp32-s3-devkitc-1, 但 env 名保持 "cyberwand").
BUILD_DIR="${PROJ_DIR}/.pio/build/cyberwand"
ELF="${BUILD_DIR}/firmware.elf"

fail=0
pass() { printf "  \e[32m[PASS]\e[0m  %s\n" "$1"; }
warn() { printf "  \e[33m[WARN]\e[0m  %s\n" "$1"; }
err()  { printf "  \e[31m[FAIL]\e[0m  %s\n" "$1"; fail=1; }

echo "==> Verify: test code never leaks into ESP32 firmware"
echo "    Build dir : ${BUILD_DIR}"
echo

if [[ ! -f "${ELF}" ]]; then
    err "${ELF} not found. Run \`pio run\` first."
    exit 2
fi

# -----------------------------------------------------------------------------
# 1) .o 文件不可包含任何测试源
# -----------------------------------------------------------------------------
echo "[1/4] Object file pollution check"
contam=$(find "${BUILD_DIR}" \( \
            -name "test_*.o" -o \
            -name "mini_test*.o" -o \
            -path "*mocks*" -o \
            -path "*test/*Arduino.cpp.o" -o \
            -path "*test/*Preferences.cpp.o" \
         \) 2>/dev/null || true)
if [[ -z "${contam}" ]]; then
    pass "no test_*.o / mocks/* / mini_test* in build dir"
else
    err "FOUND test object files in firmware build:"
    echo "${contam}" | sed 's/^/         /'
fi

# -----------------------------------------------------------------------------
# 2) firmware.elf 中不可有任何测试框架/桩符号
# -----------------------------------------------------------------------------
echo "[2/4] ELF symbol pollution check"
# ESP32-S3 工具链 (xtensa-esp32s3-elf-nm) 优先, 老 ESP32 (xtensa-esp32-elf-nm) 兜底,
# 都没有则用通用 nm (足以解析 ELF 符号表).
NM=""
for cand in \
    "${HOME}/.platformio/packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-nm" \
    "${HOME}/.platformio/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-nm" \
    "$(command -v nm)"; do
    if [[ -x "${cand}" ]]; then NM="${cand}"; break; fi
done
if [[ -z "${NM}" ]]; then
    warn "no nm tool found, skip ELF symbol check"
else
    bad_syms=$("${NM}" "${ELF}" 2>/dev/null \
        | grep -E "mini_test|MT_TEST|cw_test|HardwareSerialMock|mt_reg_" || true)
    if [[ -z "${bad_syms}" ]]; then
        pass "0 mini_test / cw_test / HardwareSerialMock symbols in firmware.elf"
    else
        err "FOUND test framework symbols in firmware.elf:"
        echo "${bad_syms}" | sed 's/^/         /'
    fi
fi

# -----------------------------------------------------------------------------
# 3) 业务模块的核心 .o 都必须存在 (反向证明 LDF 工作正常)
# -----------------------------------------------------------------------------
echo "[3/4] Required production module objects present"
# ble/* : 蓝牙协议栈
for mod in ble_remote remote_frame paired_store command_codec; do
    if find "${BUILD_DIR}" -path "*/ble/${mod}.cpp.o" -print -quit | grep -q "${mod}"; then
        pass "ble/${mod}.cpp.o linked into firmware"
    else
        err "ble/${mod}.cpp.o MISSING — LDF didn't pick it up"
    fi
done
# cnn/imu_resampler : "按下到松开" 可变长 IMU 序列归一化模块
if find "${BUILD_DIR}" -path "*/cnn/imu_resampler.cpp.o" -print -quit | grep -q "imu_resampler"; then
    pass "cnn/imu_resampler.cpp.o linked into firmware"
else
    err "cnn/imu_resampler.cpp.o MISSING — LDF didn't pick it up"
fi

# -----------------------------------------------------------------------------
# 4) 旧名残留检查
# -----------------------------------------------------------------------------
echo "[4/4] Stale renamed-away objects"
stale=$(find "${BUILD_DIR}" \( \
            -name "paired_peer_store*" -o \
            -name "bond_store*" \
         \) 2>/dev/null || true)
if [[ -z "${stale}" ]]; then
    pass "no paired_peer_store / bond_store stale objects"
else
    err "FOUND stale objects (run \`pio run -t clean\` first):"
    echo "${stale}" | sed 's/^/         /'
fi

echo
if [[ "${fail}" -eq 0 ]]; then
    printf "\e[32m==> ALL CHECKS PASSED — firmware is clean.\e[0m\n"
    exit 0
else
    printf "\e[31m==> CONTRACT VIOLATIONS FOUND.\e[0m\n"
    exit 1
fi
