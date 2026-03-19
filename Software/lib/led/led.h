#pragma once
#include <Arduino.h>
#include <vector>
#include "led_event.h"

namespace cw::led {

class LedManager {
private:
    struct LedContext {
        uint8_t pin;             
        LedType type;            
        bool active_level;       
        LedMode current_mode;    
        
        // 新增：定时控制相关的上下文
        uint32_t mode_start_time; // snake_case: 模式开始时间
        uint32_t duration_ms;     // snake_case: 持续时间 (0表示永久)
        LedMode fallback_mode;    // snake_case: 超时后的回退模式
        
        LedContext(uint8_t p, LedType t, bool level);
    };

    std::vector<LedContext> leds;  

    static const uint32_t blink_slow_period_ms = 1000; 
    static const uint32_t blink_fast_period_ms = 200;  
    static const uint32_t breathe_period_ms = 2000;    

    LedManager() = default;
    ~LedManager() = default;

    static void TaskWrapper(void* context);
    void RunTask();
    void SetLedPwm(const LedContext& led, uint8_t brightness);

public:
    LedManager(const LedManager&) = delete;
    LedManager& operator=(const LedManager&) = delete;

    static LedManager& GetInstance();

    void AddLed(uint8_t pin, LedType t, bool active_level = HIGH);
    void Begin(UBaseType_t priority = 4, BaseType_t coreId = 1);
    
    // 修改：支持传入持续时间(毫秒)和回退模式。默认 duration_ms=0 表示永久运行
    void SetMode(LedType t, LedMode mode, uint32_t duration_ms = 0, LedMode fallback = LedMode::Off);
};

}