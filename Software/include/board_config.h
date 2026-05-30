// =============================================================================
// board_config.h —— CyberWand 硬件相关常量集中定义
// -----------------------------------------------------------------------------
// snake_temp 分支: ESP32-S3 N16R8 开发板 + MPU6050 模块 + 触摸开关 (临时验证方案)
// snake_master 分支: 自制 PCB (ESP32-S3 + IMU + 按键 + WS2812B + 充电管理)
//
// 本文件是软件层与硬件之间的"单一接口". 板子换了 / 引脚改了, 只需改这一处,
// 所有模块自动跟随. 不要在其它源文件里硬编码引脚号.
//
// ⚠️ 关键约束 - N16R8 内置 Octal PSRAM (当前临时禁用)
//   ESP32-S3 N16R8 的 8MB Octal PSRAM 占用 IO33~IO37 (SPI 数据 + WP + HD)
//   外加 IO26~IO32 (SPI 总线 + CS), 即 IO26~IO37 共 12 个 IO 完全被 PSRAM
//   占用, 软件代码访问会让 PSRAM 通信失败甚至导致崩溃 / 看门狗重启.
//   本文件结尾用 static_assert 防止误用这些引脚.
//   ⚠️ 临时分支已禁用 PSRAM (platformio.ini 未配置 memory_type),
//      IO26~IO37 理论上可做 GPIO, 但 static_assert 保留约束以兼容主分支.
// =============================================================================
#pragma once
#include <stdint.h>

namespace cw {
namespace board {

// ===========================================================================
// 1. GPIO 引脚映射 (snake_temp 临时开发板接线)
// ---------------------------------------------------------------------------
//   MPU6050 SCL  -> GPIO17
//   MPU6050 SDA  -> GPIO18
//   MPU6050 INT  -> GPIO16
//   触摸开关信号  -> GPIO4  (active HIGH, 触摸时输出高电平)
//
//   以下引脚来自主分支 PCB 定义, 临时分支未使用但保留编译兼容:
//   kPinKey1       = GPIO2  (原 SW1 按键, 临时分支改为触摸开关)
//   kPinLed1Data   = GPIO42 (WS2812B, 临时开发板未接)
//   kPinChargeStat = GPIO5  (充电状态, 临时开发板未接)
// ===========================================================================

// --- 主按键 (SW1, 仅主分支 PCB 使用; 临时分支用触摸开关代替) ------------
constexpr uint8_t kPinKey1            = 2;

// --- 主指示灯 (LED1, WS2812B, 仅主分支 PCB 使用) ------------------------
constexpr uint8_t kPinLed1Data        = 42;
constexpr uint16_t kLed1Count         = 1;

// --- IMU (MPU6050, I2C) --------------------------------------------------
//   SCL -> GPIO17, SDA -> GPIO18, INT -> GPIO16
constexpr uint8_t kPinI2cSda          = 18;
constexpr uint8_t kPinI2cScl          = 17;
//   IMU DRDY 中断: 正常由硬件触发采样, 超时自动回退到轮询模式
constexpr uint8_t kPinImuInt          = 16;

// --- 触摸开关 (snake_temp 临时方案) --------------------------------------
//   信号引脚 -> GPIO4, active HIGH
//   触摸=开始采样手势, 松开=停止采样并识别
constexpr uint8_t kPinTouchSwitch     = 4;

// --- 充电状态 (仅主分支 PCB 使用) ----------------------------------------
constexpr uint8_t kPinChargeStat      = 5;

// --- I2C 总线频率 -------------------------------------------------------
constexpr uint32_t kI2cClockHz        = 400000;   // 400 kHz Fast Mode, IMU datasheet 上限

// --- IMU 中断驱动参数 ---------------------------------------------------
//   采用"中断为主 + 轮询兜底"策略, 节省 MCU 在采样间隙的 CPU 占用:
//     正常情况: IMU DRDY -> ESP32 GPIO RISING -> 信号量 -> 业务任务唤醒
//     R5 触发:  N 次连续没收到中断 -> 一次性切到固定周期 vTaskDelay 兜底
//   IMU 端配置:
//     SMPLRT_DIV = 9 -> 100 Hz (= 1kHz / (1+9), 与 kContinuousFramePeriodMs=10ms 对齐)
//     INT_LEVEL = 0 (active high), INT_OPEN = 0 (推挽), LATCH_INT_EN = 0 (50us 脉冲)
//     INT_RD_CLEAR = 1 (任意状态读清除)
//   ESP32 端配置:
//     pinMode(INT, INPUT) — 不内部上拉 (IMU push-pull 已经驱动)
//     attachInterrupt(INT, isr, RISING)
constexpr uint8_t kImuSampleRateDiv   = 9;        // SMPLRT_DIV, 100 Hz
constexpr uint32_t kImuIntWaitMs      = 15;       // 单帧中断等待超时 (理论 10ms, 留 50% 余量)
constexpr uint32_t kImuPollFallbackMs = 7;        // R5 兜底: 每帧 vTaskDelay 时长 (= 10ms - 3ms 通信)


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
static_assert(IsSafeGpioForN16R8(kPinTouchSwitch),
              "kPinTouchSwitch conflicts with N16R8 PSRAM/missing pins (IO22~37)");
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
// strapping pin 接外设本身可能符合设计 (如 IO0 接 BOOT 电路),
// 但接按键/触摸开关等用户触发的 IO 必须避开, 否则影响上电时序.
static_assert(!IsStrappingPin(kPinKey1),
              "kPinKey1 must not be a strapping pin (would corrupt boot mode)");
static_assert(!IsStrappingPin(kPinTouchSwitch),
              "kPinTouchSwitch must not be a strapping pin");

}  // namespace board
}  // namespace cw
