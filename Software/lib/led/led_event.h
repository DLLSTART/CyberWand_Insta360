#pragma once
#include <Arduino.h>

namespace cw::led {
// ==========================================
// LED 公共数据结构定义
// ==========================================

// LED 类型 (PascalCase)
enum class LedType {
    Status,     // 状态指示灯
    Warning,    // 警告指示灯
    Network     // 网络指示灯
};

// LED 显示模式 (PascalCase)
enum class LedMode {
    Off,        // 常灭
    On,         // 常亮
    BlinkSlow,  // 慢闪 (例如 1Hz)
    BlinkFast,  // 快闪 (例如 5Hz)
    Breathe     // 呼吸灯模式
};
}