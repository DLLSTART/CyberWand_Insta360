#pragma once
#include <Arduino.h>

namespace cw::button {
// ==========================================
// 按键公共数据结构定义
// ==========================================

// 按键类型 (PascalCase)
enum class ButtonType {
    Power,
    JoystickBtn,
    Menu
};

// 按键事件 (PascalCase)
enum class ButtonEvent {
    PressDown,    // 新增：按键按下 (消抖后触发)
    Release,      // 新增：按键松开
    SingleClick,  // 单击
    DoubleClick,  // 双击
    LongPress     // 长按
};

// 消息队列传输结构体
struct ButtonMessage {
    ButtonType type;   // snake_case
    ButtonEvent event; // snake_case
};
}