// =============================================================================
// board_config.h —— CyberWand 硬件相关常量集中定义
// -----------------------------------------------------------------------------
// 板硬件: ESP32-S3-WROOM-1-N16R8 (16 MB Flash + 8 MB Octal PSRAM)
//        + WS2812B 智能 LED + InvenSense 系列 IMU (I2C) + USB→CH340 转串口
// 原理图: HardWare/schematic/P1.Schematic1
// 硬件文档: HardWare/cyberwand_hardware_v3.md (v4.0)
//
// 本文件是软件层与 PCB 之间的"单一接口". 板子换了 / 引脚改了, 只需改这一处,
// 所有模块自动跟随. 不要在其它源文件里硬编码引脚号.
//
// ⚠️ 关键约束 - N16R8 内置 Octal PSRAM
//   ESP32-S3 N16R8 的 8MB Octal PSRAM 占用 IO33~IO37 (SPI 数据 + WP + HD)
//   外加 IO26~IO32 (SPI 总线 + CS), 即 IO26~IO37 共 12 个 IO 完全被 PSRAM
//   占用, 软件代码访问会让 PSRAM 通信失败甚至导致崩溃 / 看门狗重启.
//   本文件结尾用 static_assert 防止误用这些引脚.
// =============================================================================
#pragma once
#include <stdint.h>

namespace cw {
namespace board {

// ===========================================================================
// 1. GPIO 引脚映射
// ---------------------------------------------------------------------------
// 信号网络名取自原理图; 数值是基于原理图最佳判断 + ESP32-S3 工程惯例.
// 实物焊好首板后, 对照原理图核对一遍, 不准时**只改这里**就够了.
// ===========================================================================

// --- 主按键 (SW1) -------------------------------------------------------
//   原理图: SW1 一端接 GND, 另一端 KEY_1 网络经 R2=10K 上拉到 +3V3
//   软件:   pinMode(INPUT_PULLUP) + 按下读到 LOW
//   选择理由: IO4 是 ESP32-S3 安全引脚 (非 strapping, 非 PSRAM, 非 USB),
//            外部 10K 上拉够强, 内部弱上拉作为冗余
constexpr uint8_t kPinKey1            = 4;

// --- 主指示灯 (LED1, WS2812B) ------------------------------------------
//   原理图: LED1 LED_IN ← MCU; LED_OUT → H1 跳线 (预留可级联多颗)
//   驱动:   必须用 RMT / Adafruit NeoPixel, 不能 digitalWrite
//   选择理由: IO48 在很多 ESP32-S3 开发板上就是板载 RGB LED 引脚,
//            驱动能力强 (40mA), 时序完整性好, 不占 strapping
constexpr uint8_t kPinLed1Data        = 48;
constexpr uint16_t kLed1Count         = 1;    // 当前布板 1 颗主灯, 后续如级联多颗就改这个

// --- IMU (U4, I2C) ------------------------------------------------------
//   原理图: U4 SDA/SCL 接 MCU, INT 接 MCU 中断脚
//   注:     I2C 总线已在 IMU 端就近上拉到 +3V3
constexpr uint8_t kPinI2cSda          = 8;
constexpr uint8_t kPinI2cScl          = 9;
constexpr uint8_t kPinImuInt          = 10;   // 软件目前未使用, 预留给 DRDY 中断

// --- 充电状态 (CHRG) ----------------------------------------------------
//   原理图: 充电芯片 CHRG 开漏输出, 充电中拉低, 充满 / 未插 USB 高阻
//   软件:   pinMode(INPUT_PULLUP); LOW 表示充电中
constexpr uint8_t kPinChargeStat      = 11;

// --- I2C 总线频率 -------------------------------------------------------
constexpr uint32_t kI2cClockHz        = 400000;   // 400 kHz Fast Mode, IMU datasheet 上限


// ===========================================================================
// 2. WS2812 颜色 / 亮度参数
// ---------------------------------------------------------------------------
// 用于 LedManager 把 LedMode 语义映射为具体灯效.
// 颜色是 24-bit GRB (NEO_GRB), 高 8 位预留.
// ===========================================================================

constexpr uint8_t kLedDefaultBrightness = 60;   // 0~255, 60 ≈ 24% 占空, 兼顾亮度与续航
constexpr uint8_t kLedActiveBrightness  = 120;  // 用户交互时短暂调亮

// 颜色: 0xRRGGBB (LedManager 内部转 GRB)
constexpr uint32_t kLedColorOff       = 0x000000;
constexpr uint32_t kLedColorWhite     = 0xFFFFFF;   // 一般状态 (替代原"On")
constexpr uint32_t kLedColorRecording = 0xFF0000;   // 录制中: 红
constexpr uint32_t kLedColorMode      = 0x0000FF;   // 模式切换: 蓝
constexpr uint32_t kLedColorReady     = 0x00FF00;   // 就绪 / 配对成功: 绿


// ===========================================================================
// 3. 编译期安全检查 (N16R8 PSRAM 占用约束)
// ---------------------------------------------------------------------------
// 任何外部 GPIO 都不能落在 IO26~IO37 范围, 否则 PSRAM 通信失败.
// ===========================================================================

constexpr bool IsSafeGpioForN16R8(uint8_t pin) {
    // ESP32-S3 N16R8: IO26~IO37 被 Octal PSRAM 占用 (12 根线)
    // 同时 IO22~IO25 在 ESP32-S3 上不存在
    return !((pin >= 22 && pin <= 25) || (pin >= 26 && pin <= 37));
}

static_assert(IsSafeGpioForN16R8(kPinKey1),
              "kPinKey1 conflicts with N16R8 PSRAM/missing pins (IO22~37)");
static_assert(IsSafeGpioForN16R8(kPinLed1Data),
              "kPinLed1Data conflicts with N16R8 PSRAM/missing pins (IO22~37)");
static_assert(IsSafeGpioForN16R8(kPinI2cSda),
              "kPinI2cSda conflicts with N16R8 PSRAM/missing pins (IO22~37)");
static_assert(IsSafeGpioForN16R8(kPinI2cScl),
              "kPinI2cScl conflicts with N16R8 PSRAM/missing pins (IO22~37)");
static_assert(IsSafeGpioForN16R8(kPinImuInt),
              "kPinImuInt conflicts with N16R8 PSRAM/missing pins (IO22~37)");
static_assert(IsSafeGpioForN16R8(kPinChargeStat),
              "kPinChargeStat conflicts with N16R8 PSRAM/missing pins (IO22~37)");

// 同时检查不和 strapping pin 上 (上电瞬间不能被外部强拉)
//   IO0  : BOOT 选择 (上电默认必须高)
//   IO3  : JTAG 选择
//   IO45 : VDD_SPI 电压
//   IO46 : Log Print 控制
// 这里只对外部 GPIO 做 informative assertion, 不阻断编译 (有时设计上不可避免)
constexpr bool IsStrappingPin(uint8_t pin) {
    return pin == 0 || pin == 3 || pin == 45 || pin == 46;
}
// strapping pin 上接外设是 OK 的 (例如 IO0 接 BOOT 控制电路本身就符合设计),
// 但接按键 / LED 这种用户随手触发的 IO 必须避开 - 否则上电时序坏掉.
static_assert(!IsStrappingPin(kPinKey1),
              "kPinKey1 must not be a strapping pin (would corrupt boot mode)");

}  // namespace board
}  // namespace cw
