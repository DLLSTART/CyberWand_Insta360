#pragma once
#include <stdint.h>

namespace cw {
namespace button {

enum class ButtonType {
    Power,
    JoystickBtn,
    Menu
};

enum class ButtonEvent {
    PressDown,
    Release,
    SingleClick,
    DoubleClick,
    LongPress
};

struct ButtonMessage {
    ButtonType type;
    ButtonEvent event;
};

}  // namespace button
}  // namespace cw
