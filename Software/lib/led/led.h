// =============================================================================
// led.h —— WS2812B 智能 LED 驱动 (替代 v3 时期的 PWM/digitalWrite 实现)
// -----------------------------------------------------------------------------
// 硬件:   LED1 / LED_OUT 是 WS2812B 单线串行智能 LED, 不能用 digitalWrite +
//         delay 模拟时序 (±150ns 容差, 必须 RMT 外设).
// 驱动:   Adafruit NeoPixel 库, 内部走 ESP32 RMT 通道, 单颗 LED show() ~30us.
// 接口:   尽量保留旧 LedManager 的 LedType / LedMode 语义, 让 main.cpp 业务
//         代码改动最小; 同时新增颜色感知的 SetMode 重载与 SetColor 接口.
// 关键差异 (相对旧 PWM 版本):
//   - AddLed 删除 active_level 参数 (智能 LED 不存在低电平有效的概念),
//     新增 num_leds 参数 (默认 1, 留扩展; 板上 LED_OUT 可级联多颗).
//   - 模式语义不变: Off / On / BlinkSlow / BlinkFast / Breathe.
//   - 颜色由 LedManager 内部状态保存; 不指定颜色的 SetMode 沿用上次设的颜色.
// =============================================================================
#pragma once
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <vector>
#include <memory>
#include "led_event.h"

namespace cw::led {

class LedManager {
 private:
    // 单组逻辑灯位 (一颗 WS2812 或一串级联).
    // 用 unique_ptr 持有, 因为 Adafruit_NeoPixel 内部含 calloc 缓冲不可平凡拷贝.
    struct LedContext {
        LedType type;
        uint16_t num_leds;
        Adafruit_NeoPixel strip;

        // 当前期望的颜色 (0xRRGGBB) 与全局亮度上限 (0~255).
        // SetMode/SetColor 改这两个值, RunTask 按 mode 调制后写到硬件.
        uint32_t color;
        uint8_t brightness;

        LedMode current_mode;
        uint32_t mode_start_time;   // millis() 时刻
        uint32_t duration_ms;       // 0 表示永久, 非 0 表示到点切 fallback
        LedMode fallback_mode;
        uint32_t fallback_color;

        LedContext(uint8_t pin, uint16_t n, LedType t);
    };

    std::vector<std::unique_ptr<LedContext>> leds;

    static const uint32_t blink_slow_period_ms = 1000;
    static const uint32_t blink_fast_period_ms = 200;
    static const uint32_t breathe_period_ms = 2000;

    LedManager() = default;
    ~LedManager() = default;

    static void TaskWrapper(void* context);
    void RunTask();

    // 把 (color, brightness) 应用到一组 LED 的所有灯珠并 show().
    static void ApplyAllPixels(LedContext& led, uint32_t color, uint8_t brightness);
    // 按 brightness/255 比例缩放每个通道, 用于呼吸 / 闪烁.
    static uint32_t ScaleColor(uint32_t color, uint8_t brightness);

 public:
    LedManager(const LedManager&) = delete;
    LedManager& operator=(const LedManager&) = delete;

    static LedManager& GetInstance();

    // 注册一组 WS2812 灯位.
    //   pin       : WS2812 数据线 GPIO (= board_config.h 的 kPinLed1Data 等)
    //   num_leds  : 串中颗数 (默认 1, 当前布板 1 颗主灯)
    //   t         : 业务语义标签 (Status / Warning / Network)
    void AddLed(uint8_t pin, uint16_t num_leds = 1, LedType t = LedType::Status);

    // 启动后台刷新任务 (FreeRTOS task, 周期 20ms).
    void Begin(UBaseType_t priority = 1, BaseType_t coreId = 1);

    // 仅切模式, 沿用上次的颜色 (兼容旧调用方).
    //   duration_ms = 0 表示永久; >0 时到点自动回到 fallback (颜色也回到 fallback_color).
    void SetMode(LedType t, LedMode mode,
                 uint32_t duration_ms = 0,
                 LedMode fallback = LedMode::Off);

    // 颜色感知重载: 同时设颜色与模式.
    //   fallback_color = 0 表示与 color 相同 (即 fallback 时不换色).
    void SetMode(LedType t, LedMode mode, uint32_t color,
                 uint32_t duration_ms = 0,
                 LedMode fallback = LedMode::Off,
                 uint32_t fallback_color = 0);

    // 单独换色, 不改 mode (例如录制中由白变红表示警告).
    void SetColor(LedType t, uint32_t color);
};

}  // namespace cw::led
