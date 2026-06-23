#pragma once
#include <vector>
#include "driver/gpio.h"
#include "driver/rmt.h"
#include "led_event.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace cw::led {

class LedManager {
 private:
    struct LedContext {
        LedType type;
        gpio_num_t pin;

        LedMode current_mode;
        uint32_t mode_start_time;
        uint32_t duration_ms;
        LedMode fallback_mode;

        // RGB (WS2812B) 模式: is_rgb=true 时用 RMT 写 24-bit 颜色;
        // is_rgb=false 时退化为单色 GPIO 高低电平.
        bool       is_rgb;
        rmt_channel_t rmt_channel;   // 仅 is_rgb=true 时有效
        uint32_t   last_rgb_color;   // 上次写入的 GRB-packed 24-bit, 用于去重

        LedContext(gpio_num_t p, LedType t);
    };

    std::vector<LedContext> leds;

    static const uint32_t blink_slow_period_ms = 1000;
    static const uint32_t blink_fast_period_ms = 200;

    LedManager() = default;
    ~LedManager() = default;

    static void TaskWrapper(void* context);
    void RunTask();

    static void ApplyLed(LedContext& led, bool on);
    // 写 24-bit RGB (按 0xRRGGBB 输入). 内部转 GRB 字节序后用 RMT 推一次.
    static void ApplyRgb(LedContext& led, uint32_t rgb);

 public:
    LedManager(const LedManager&) = delete;
    LedManager& operator=(const LedManager&) = delete;

    static LedManager& GetInstance();

    void AddLed(gpio_num_t pin, LedType t = LedType::Status);
    // 注册一颗 WS2812B (单灯). channel 默认 RMT_CHANNEL_0; 多灯/多通道时由
    // 调用方分配, 避免冲突.
    void AddRgbLed(gpio_num_t pin, LedType t = LedType::Status,
                   rmt_channel_t channel = RMT_CHANNEL_0);
    void Begin(UBaseType_t priority = 1, BaseType_t coreId = 1);

    void SetMode(LedType t, LedMode mode,
                 uint32_t duration_ms = 0,
                 LedMode fallback = LedMode::Off);

    // 取当前 mode (找到第一个 type 匹配的灯). 主要供主循环判断"是否处在
    // 手势活动色中, 不要被 idle 色覆盖".
    LedMode GetMode(LedType t) const;
};

}
