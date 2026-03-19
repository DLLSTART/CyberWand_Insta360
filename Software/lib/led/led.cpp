#include "led.h"

namespace cw::led {

// 构造函数初始化新增的计时变量
LedManager::LedContext::LedContext(uint8_t p, LedType t, bool level) 
    : pin(p), type(t), active_level(level), current_mode(LedMode::Off),
      mode_start_time(0), duration_ms(0), fallback_mode(LedMode::Off) {}

LedManager& LedManager::GetInstance() {
    static LedManager instance;
    return instance;
}

void LedManager::AddLed(uint8_t pin, LedType t, bool active_level) {
    pinMode(pin, OUTPUT);
    leds.emplace_back(pin, t, active_level);
    SetMode(t, LedMode::Off); 
}

void LedManager::Begin(UBaseType_t priority, BaseType_t coreId) {
    if (leds.empty()) return;

    xTaskCreatePinnedToCore(LedManager::TaskWrapper, "LedMgrTask", 2048, this, priority, nullptr, coreId);
}

// 设置模式时，记录当前时间戳
void LedManager::SetMode(LedType t, LedMode mode, uint32_t duration_ms, LedMode fallback) {
    for (auto& led : leds) {
        if (led.type == t) {
            led.current_mode = mode;
            led.mode_start_time = millis(); // 记录起步时间
            led.duration_ms = duration_ms;  // 记录持续时间
            led.fallback_mode = fallback;   // 记录回退模式
        }
    }
}

void LedManager::SetLedPwm(const LedContext& led, uint8_t brightness) {
    uint8_t duty = (led.active_level == HIGH) ? brightness : (255 - brightness);
    analogWrite(led.pin, duty); 
}

void LedManager::TaskWrapper(void* context) {
    static_cast<LedManager*>(context)->RunTask();
}

void LedManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& led : leds) {
            
            // =====================================
            // 新增核心逻辑：检查当前模式是否已超时
            // =====================================
            if (led.duration_ms > 0 && (now - led.mode_start_time >= led.duration_ms)) {
                // 时间到，切换到回退模式，并清除定时器
                led.current_mode = led.fallback_mode;
                led.duration_ms = 0; 
            }

            // 原有的状态机逻辑保持不变
            switch (led.current_mode) {
                case LedMode::Off:
                    SetLedPwm(led, 0); 
                    break;
                case LedMode::On:
                    SetLedPwm(led, 255); 
                    break;
                case LedMode::BlinkSlow: {
                    bool is_on = (now % blink_slow_period_ms) < (blink_slow_period_ms / 2);
                    SetLedPwm(led, is_on ? 255 : 0);
                    break;
                }
                case LedMode::BlinkFast: {
                    bool is_on = (now % blink_fast_period_ms) < (blink_fast_period_ms / 2);
                    SetLedPwm(led, is_on ? 255 : 0);
                    break;
                }
                case LedMode::Breathe: {
                    uint32_t cycle_pos = now % breathe_period_ms;
                    uint32_t half_period = breathe_period_ms / 2;
                    uint8_t brightness = (cycle_pos < half_period) ? 
                        map(cycle_pos, 0, half_period, 0, 255) : 
                        map(cycle_pos, half_period, breathe_period_ms, 255, 0);
                    SetLedPwm(led, brightness);
                    break;
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20)); 
    }
}
}