#pragma once
#include <vector>
#include "driver/gpio.h"
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

 public:
    LedManager(const LedManager&) = delete;
    LedManager& operator=(const LedManager&) = delete;

    static LedManager& GetInstance();

    void AddLed(gpio_num_t pin, LedType t = LedType::Status);
    void Begin(UBaseType_t priority = 1, BaseType_t coreId = 1);

    void SetMode(LedType t, LedMode mode,
                 uint32_t duration_ms = 0,
                 LedMode fallback = LedMode::Off);
};

}
