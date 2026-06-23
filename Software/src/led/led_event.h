#pragma once

namespace cw::led {

enum class LedType {
    Status,
    Warning,
    Network
};

enum class LedMode {
    Off,
    On,
    BlinkSlow,
    BlinkFast,
    Breathe,
    // ===== 状态色 (仅对 WS2812B/RGB 灯有效, 对单色 GPIO 灯按 On 处理) =====
    SolidWhite,    // 已开机 + 广播中, 未连接
    SolidBlue,     // 已连接相机, 空闲
    SolidGreen,    // 手势识别 (跑 CNN) 中
    SolidYellow,   // 手势录制 (按住采样 IMU) 中
};

}
