#pragma once
#include <vector>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "button_event.h"

namespace cw::button {

class ButtonManager {
private:
    enum class ButtonState {
        Idle,
        Pressed,
        WaitForDoubleClick,
        WaitForTripleClick,
        WaitForRelease
    };

    struct ButtonContext {
        gpio_num_t pin;
        ButtonType type;
        bool active_level;
        ButtonState state;
        uint32_t press_time;
        uint32_t release_time;
        bool is_press_emitted;
        uint8_t click_count;  // 当前正在判定的连击计数: 1=单击, 2=双击中, 3=三击中

        ButtonContext(gpio_num_t p, ButtonType t, bool level);
    };

    std::vector<ButtonContext> buttons;
    QueueHandle_t message_queue;

    static const uint32_t debounce_ms = 20;
    static const uint32_t long_press_ms = 1000;
    static const uint32_t double_click_ms = 250;
    static const uint32_t triple_click_ms = 250;

    ButtonManager();
    ~ButtonManager();

    void SendEvent(ButtonType t, ButtonEvent e);
    static void TaskWrapper(void* context);
    void RunTask();

public:
    ButtonManager(const ButtonManager&) = delete;
    ButtonManager& operator=(const ButtonManager&) = delete;

    static ButtonManager& GetInstance();

    void AddButton(gpio_num_t pin, ButtonType t, bool active_level = false);
    void Begin(UBaseType_t priority = 1, BaseType_t coreId = 1);
    bool GetEvent(ButtonMessage& message, TickType_t waitTicks = portMAX_DELAY);
};

}
