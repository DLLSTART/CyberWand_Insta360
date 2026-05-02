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
// 1. GPIO 引脚映射 (与原理图 P1 / MCU.png 严格一致)
// ---------------------------------------------------------------------------
// 引脚号通过仔细阅读 enclosure/MCU.png + IMU.png + 充电.png 的网络标号确定:
//   左侧 pin 3..14   (EN / IO4 / IO5 / ... / IO20)
//   右侧 pin 27..38  (IO0 / IO35..42 / RXD0 / TXD0 / IO2)
//   底部 pin 15..26  (大量 NC + IO47 引出 SDA)
// 实物焊好首板后, 用万用表对照原理图任意一条 IO 网络回测, 不准时**只改这里**.
// ===========================================================================

// --- 主按键 (SW1) -------------------------------------------------------
//   原理图 (MCU.png): SW1 一端接 GND, 另一端 KEY_1 网络
//                    经 R2=10K 上拉到 +3V3, 接到模组 pin 38 = IO2
//   软件:   pinMode(INPUT_PULLUP) + 按下读到 LOW (内部弱上拉做冗余)
constexpr uint8_t kPinKey1            = 2;

// --- 主指示灯 (LED1, WS2812B) ------------------------------------------
//   原理图 (MCU.png): LED1 DIN <- MCU pin 35 = IO42 (LED_IN 网络)
//                    LED1 DOUT -> H1 跳线 (3 pin: +3V3 / LED_OUT / GND, 预留级联)
//   驱动:   必须用 RMT / Adafruit NeoPixel, 不能 digitalWrite
constexpr uint8_t kPinLed1Data        = 42;
constexpr uint16_t kLed1Count         = 1;    // 当前布板 1 颗主灯, 后续如级联多颗就改这个

// --- IMU (U4, I2C) ------------------------------------------------------
//   原理图 (MCU.png + IMU.png):
//     SDA -> MCU pin 24 = IO47 (从模组底部引出)
//     SCL -> MCU pin 14 = IO20
//     INT -> MCU pin 4  = IO4 (注: IMU 端 pin 11 标 "FSYNC" 但接到 INT 网络,
//                              pin 12 标 "INT" 但悬空 - 可能是丝印误标,
//                              实物以 PCB 走线为准, 本字段必须对应实际中断输出)
//   ⚠️ 风险: 原理图上 SDA/SCL 没看到外部上拉电阻, 仅靠内部弱上拉.
//             首板若 I2C scanner 看不到 0x68, 优先飞 4.7K 上拉到 +3V3.
constexpr uint8_t kPinI2cSda          = 47;
constexpr uint8_t kPinI2cScl          = 20;
constexpr uint8_t kPinImuInt          = 4;   // 软件目前未使用, 预留给 DRDY 中断

// --- 充电状态 (CHRG) ----------------------------------------------------
//   原理图 (充电.png + MCU.png): 充电 IC U3 pin 1 (CHRG 开漏输出)
//     -> R3=10K + LED2 (充电指示) -> +5V
//     -> 同时回到 MCU pin 5 = IO5
//   软件: pinMode(INPUT_PULLUP); LOW 表示充电中, 高阻表示充满 / 未插 USB
constexpr uint8_t kPinChargeStat      = 5;

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
