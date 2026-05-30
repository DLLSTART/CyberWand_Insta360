#include "led.h"
#include "base.h"
#include "esp_timer.h"

namespace cw::led {

static uint32_t millis() {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

LedManager::LedContext::LedContext(gpio_num_t p, LedType t)
    : type(t), pin(p), current_mode(LedMode::Off),
      mode_start_time(0), duration_ms(0), fallback_mode(LedMode::Off) {}

LedManager& LedManager::GetInstance() {
    static LedManager instance;
    return instance;
}

void LedManager::AddLed(gpio_num_t pin, LedType t) {
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << pin);
    io_conf.mode = GPIO_MODE_OUTPUT;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&io_conf);
    gpio_set_level(pin, 0);
    leds.emplace_back(pin, t);
}

void LedManager::Begin(UBaseType_t priority, BaseType_t coreId) {
    if (leds.empty()) return;
    xTaskCreatePinnedToCore(LedManager::TaskWrapper, "LedMgrTask", 2048,
                            this, priority, nullptr, coreId);
}

void LedManager::SetMode(LedType t, LedMode mode,
                         uint32_t duration_ms, LedMode fallback) {
    for (auto& led : leds) {
        if (led.type == t) {
            led.current_mode = mode;
            led.mode_start_time = millis();
            led.duration_ms = duration_ms;
            led.fallback_mode = fallback;
        }
    }
}

void LedManager::ApplyLed(LedContext& led, bool on) {
    gpio_set_level(led.pin, on ? 1 : 0);
}

void LedManager::TaskWrapper(void* context) {
    static_cast<LedManager*>(context)->RunTask();
}

void LedManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& led : leds) {
            if (led.duration_ms > 0 &&
                (now - led.mode_start_time >= led.duration_ms)) {
                led.current_mode = led.fallback_mode;
                led.duration_ms = 0;
            }

            switch (led.current_mode) {
                case LedMode::Off:
                    ApplyLed(led, false);
                    break;
                case LedMode::On:
                    ApplyLed(led, true);
                    break;
                case LedMode::BlinkSlow: {
                    bool is_on = (now % blink_slow_period_ms) < (blink_slow_period_ms / 2);
                    ApplyLed(led, is_on);
                    break;
                }
                case LedMode::BlinkFast: {
                    bool is_on = (now % blink_fast_period_ms) < (blink_fast_period_ms / 2);
                    ApplyLed(led, is_on);
                    break;
                }
                case LedMode::Breathe:
                    ApplyLed(led, true);
                    break;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

}
