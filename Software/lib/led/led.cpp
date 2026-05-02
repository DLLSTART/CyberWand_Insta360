// =============================================================================
// led.cpp —— WS2812B 智能 LED 驱动实现
// 见 led.h 顶部说明.
// =============================================================================
#include "led.h"
#include "board_config.h"

namespace cw::led {

LedManager::LedContext::LedContext(uint8_t pin, uint16_t n, LedType t)
    : type(t),
      num_leds(n),
      strip(n, pin, NEO_GRB + NEO_KHZ800),
      color(cw::board::kLedColorWhite),
      brightness(cw::board::kLedDefaultBrightness),
      current_mode(LedMode::Off),
      mode_start_time(0),
      duration_ms(0),
      fallback_mode(LedMode::Off),
      fallback_color(cw::board::kLedColorWhite) {}

LedManager& LedManager::GetInstance() {
    static LedManager instance;
    return instance;
}

void LedManager::AddLed(uint8_t pin, uint16_t num_leds, LedType t) {
    auto ctx = std::unique_ptr<LedContext>(new LedContext(pin, num_leds, t));
    // NeoPixel 必须在用 setPixelColor / show 之前调一次 begin() 注册 RMT 通道.
    ctx->strip.begin();
    ctx->strip.clear();
    ctx->strip.show();
    leds.push_back(std::move(ctx));
}

void LedManager::Begin(UBaseType_t priority, BaseType_t coreId) {
    if (leds.empty()) return;
    // Stack 3KB: NeoPixel show() 内部临时变量 + 中断保护用; 旧 2KB 偶有溢出风险.
    xTaskCreatePinnedToCore(LedManager::TaskWrapper, "LedMgrTask", 3072,
                            this, priority, nullptr, coreId);
}

void LedManager::SetMode(LedType t, LedMode mode,
                         uint32_t duration_ms, LedMode fallback) {
    for (auto& led : leds) {
        if (led->type == t) {
            led->current_mode = mode;
            led->mode_start_time = millis();
            led->duration_ms = duration_ms;
            led->fallback_mode = fallback;
            // 颜色不变, 沿用上次; fallback_color 同步保持当前 color, 避免回退后色变.
            led->fallback_color = led->color;
        }
    }
}

void LedManager::SetMode(LedType t, LedMode mode, uint32_t color,
                         uint32_t duration_ms, LedMode fallback,
                         uint32_t fallback_color) {
    for (auto& led : leds) {
        if (led->type == t) {
            led->current_mode = mode;
            led->color = color;
            led->mode_start_time = millis();
            led->duration_ms = duration_ms;
            led->fallback_mode = fallback;
            led->fallback_color = (fallback_color != 0) ? fallback_color : color;
        }
    }
}

void LedManager::SetColor(LedType t, uint32_t color) {
    for (auto& led : leds) {
        if (led->type == t) {
            led->color = color;
        }
    }
}

uint32_t LedManager::ScaleColor(uint32_t color, uint8_t brightness) {
    if (brightness == 0) return 0;
    uint16_t r = (color >> 16) & 0xFF;
    uint16_t g = (color >>  8) & 0xFF;
    uint16_t b =  color        & 0xFF;
    r = (r * brightness) / 255;
    g = (g * brightness) / 255;
    b = (b * brightness) / 255;
    return (static_cast<uint32_t>(r) << 16) |
           (static_cast<uint32_t>(g) <<  8) |
            static_cast<uint32_t>(b);
}

void LedManager::ApplyAllPixels(LedContext& led, uint32_t color, uint8_t brightness) {
    uint32_t scaled = ScaleColor(color, brightness);
    uint8_t r = (scaled >> 16) & 0xFF;
    uint8_t g = (scaled >>  8) & 0xFF;
    uint8_t b =  scaled        & 0xFF;
    for (uint16_t i = 0; i < led.num_leds; ++i) {
        led.strip.setPixelColor(i, r, g, b);
    }
    led.strip.show();
}

void LedManager::TaskWrapper(void* context) {
    static_cast<LedManager*>(context)->RunTask();
}

void LedManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& led_uptr : leds) {
            auto& led = *led_uptr;

            // 限时模式到点 -> 切回 fallback (mode + color 一并切换).
            if (led.duration_ms > 0 &&
                (now - led.mode_start_time >= led.duration_ms)) {
                led.current_mode = led.fallback_mode;
                led.color = led.fallback_color;
                led.duration_ms = 0;
            }

            switch (led.current_mode) {
                case LedMode::Off:
                    ApplyAllPixels(led, 0, 0);
                    break;
                case LedMode::On:
                    ApplyAllPixels(led, led.color, led.brightness);
                    break;
                case LedMode::BlinkSlow: {
                    bool is_on = (now % blink_slow_period_ms) < (blink_slow_period_ms / 2);
                    ApplyAllPixels(led,
                                   is_on ? led.color : 0,
                                   is_on ? led.brightness : 0);
                    break;
                }
                case LedMode::BlinkFast: {
                    bool is_on = (now % blink_fast_period_ms) < (blink_fast_period_ms / 2);
                    ApplyAllPixels(led,
                                   is_on ? led.color : 0,
                                   is_on ? led.brightness : 0);
                    break;
                }
                case LedMode::Breathe: {
                    uint32_t cycle_pos = now % breathe_period_ms;
                    uint32_t half_period = breathe_period_ms / 2;
                    uint8_t b = (cycle_pos < half_period)
                        ? map(cycle_pos, 0, half_period, 0, led.brightness)
                        : map(cycle_pos, half_period, breathe_period_ms,
                              led.brightness, 0);
                    ApplyAllPixels(led, led.color, b);
                    break;
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

}  // namespace cw::led
