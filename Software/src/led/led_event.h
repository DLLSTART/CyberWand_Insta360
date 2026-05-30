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
    Breathe
};

}
