#pragma once
#include <Arduino.h>
#include <vector>
#include "button_event.h"

namespace cw::button {

class ButtonManager {
private:
    // 内部按键状态枚举 (PascalCase)，取代魔法数字
    enum class ButtonState {
        Idle,               // 空闲状态
        Pressed,            // 按下状态 (判定短按/长按)
        WaitForDoubleClick, // 等待双击状态
        WaitForRelease      // 等待物理释放状态
    };

    // 内部按键上下文结构体
    struct ButtonContext {
        uint8_t pin;             // snake_case
        ButtonType type;         // snake_case
        bool active_level;       // snake_case
        ButtonState state;       // snake_case (使用枚举代替 uint8_t)
        uint32_t press_time;     // snake_case
        uint32_t release_time;   // snake_case
        bool is_press_emitted;   // snake_case (防止抖动导致重复发送PressDown)
        
        ButtonContext(uint8_t p, ButtonType t, bool level);
    };

    std::vector<ButtonContext> buttons;     // snake_case
    QueueHandle_t message_queue;            // snake_case

    // 时间参数配置
    static const uint32_t debounce_ms = 20;
    static const uint32_t long_press_ms = 1000;
    static const uint32_t double_click_ms = 250;

    // 单例模式约束
    ButtonManager();
    ~ButtonManager();

    // 内部方法
    void SendEvent(ButtonType t, ButtonEvent e);
    static void TaskWrapper(void* context);
    void RunTask();

public:
    ButtonManager(const ButtonManager&) = delete;
    ButtonManager& operator=(const ButtonManager&) = delete;

    static ButtonManager& GetInstance();

    void AddButton(uint8_t pin, ButtonType t, bool active_level = LOW);
    void Begin(UBaseType_t priority = 5, BaseType_t coreId = 1);
    bool GetEvent(ButtonMessage& message, TickType_t waitTicks = portMAX_DELAY);
};

}