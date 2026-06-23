#include "button.h"
#include "base.h"
#include "esp_timer.h"

namespace cw::button {

ButtonManager::ButtonContext::ButtonContext(gpio_num_t p, ButtonType t, bool level)
    : pin(p), type(t), active_level(level), state(ButtonState::Idle),
      press_time(0), release_time(0), is_press_emitted(false), click_count(0) {}

ButtonManager::ButtonManager() {
    message_queue = xQueueCreate(10, sizeof(ButtonMessage));
}

ButtonManager::~ButtonManager() {
    if (message_queue != nullptr) {
        vQueueDelete(message_queue);
    }
}

void ButtonManager::SendEvent(ButtonType t, ButtonEvent e) {
    if (message_queue != nullptr) {
        ButtonMessage message = {t, e};
        xQueueSend(message_queue, &message, 0);
    }
}

void ButtonManager::TaskWrapper(void* context) {
    static_cast<ButtonManager*>(context)->RunTask();
}

static uint32_t millis() {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

void ButtonManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& btn : buttons) {
            bool is_pressed = (gpio_get_level(btn.pin) == (int)btn.active_level);

            switch (btn.state) {
                case ButtonState::Idle:
                    if (is_pressed) {
                        btn.press_time = now;
                        btn.is_press_emitted = false;
                        btn.click_count = 1;
                        btn.state = ButtonState::Pressed;
                    }
                    break;

                case ButtonState::Pressed:
                    if (is_pressed) {
                        if (!btn.is_press_emitted && (now - btn.press_time >= debounce_ms)) {
                            SendEvent(btn.type, ButtonEvent::PressDown);
                            btn.is_press_emitted = true;
                        }
                        // 长按只对第 1 次按下生效, 避免连击中途升级为长按
                        if (btn.click_count == 1 &&
                            now - btn.press_time >= long_press_ms) {
                            SendEvent(btn.type, ButtonEvent::LongPress);
                            btn.state = ButtonState::WaitForRelease;
                        }
                    } else {
                        if (now - btn.press_time >= debounce_ms) {
                            btn.release_time = now;
                            SendEvent(btn.type, ButtonEvent::Release);

                            // 第 N 次松手, 决定下一步等待还是直接派发
                            if (btn.click_count == 2) {
                                // 双击的"派发"边沿放在第 2 次按下时已经发过 DoubleClick
                                // 这里只决定: 等第 3 击 or 收尾
                                btn.state = ButtonState::WaitForTripleClick;
                            } else if (btn.click_count == 3) {
                                // 第 3 次松手 -> TripleClick (押后到松手, 让上层
                                // 已经因 Release 退出阻塞操作)
                                SendEvent(btn.type, ButtonEvent::TripleClick);
                                btn.state = ButtonState::Idle;
                                btn.click_count = 0;
                            } else {
                                // 单击候选: 等 double_click_ms 看是否升级成双击
                                btn.state = ButtonState::WaitForDoubleClick;
                            }
                        } else {
                            btn.state = ButtonState::Idle;
                            btn.click_count = 0;
                        }
                    }
                    break;

                case ButtonState::WaitForDoubleClick:
                    if (is_pressed) {
                        if (now - btn.release_time <= double_click_ms) {
                            // 第 2 次按下: 立即发 PressDown + DoubleClick
                            // (兼容现有行为: 上层在收到 DoubleClick 时切到调试模式)
                            SendEvent(btn.type, ButtonEvent::PressDown);
                            SendEvent(btn.type, ButtonEvent::DoubleClick);
                            btn.press_time = now;
                            btn.is_press_emitted = true;
                            btn.click_count = 2;
                            btn.state = ButtonState::Pressed;
                        }
                    } else {
                        if (now - btn.release_time > double_click_ms) {
                            SendEvent(btn.type, ButtonEvent::SingleClick);
                            btn.state = ButtonState::Idle;
                            btn.click_count = 0;
                        }
                    }
                    break;

                case ButtonState::WaitForTripleClick:
                    if (is_pressed) {
                        if (now - btn.release_time <= triple_click_ms) {
                            // 第 3 次按下: 只发 PressDown, TripleClick 等到松手再发
                            SendEvent(btn.type, ButtonEvent::PressDown);
                            btn.press_time = now;
                            btn.is_press_emitted = true;
                            btn.click_count = 3;
                            btn.state = ButtonState::Pressed;
                        }
                    } else {
                        if (now - btn.release_time > triple_click_ms) {
                            // 没有第 3 击: DoubleClick 已经发过, 收尾
                            btn.state = ButtonState::Idle;
                            btn.click_count = 0;
                        }
                    }
                    break;

                case ButtonState::WaitForRelease:
                    if (!is_pressed) {
                        SendEvent(btn.type, ButtonEvent::Release);
                        btn.state = ButtonState::Idle;
                        btn.click_count = 0;
                    }
                    break;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

ButtonManager& ButtonManager::GetInstance() {
    static ButtonManager instance;
    return instance;
}

void ButtonManager::AddButton(gpio_num_t pin, ButtonType t, bool active_level) {
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << pin);
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pull_up_en = active_level ? GPIO_PULLUP_DISABLE : GPIO_PULLUP_ENABLE;
    io_conf.pull_down_en = active_level ? GPIO_PULLDOWN_ENABLE : GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&io_conf);
    buttons.emplace_back(pin, t, active_level);
}

void ButtonManager::Begin(UBaseType_t priority, BaseType_t coreId) {
    if (message_queue == nullptr || buttons.empty()) return;

    xTaskCreatePinnedToCore(
        ButtonManager::TaskWrapper,
        "BtnMgrTask",
        2048,
        this,
        priority,
        nullptr,
        coreId
    );
}

bool ButtonManager::GetEvent(ButtonMessage& message, TickType_t waitTicks) {
    if (message_queue == nullptr) return false;
    return xQueueReceive(message_queue, &message, waitTicks) == pdPASS;
}

}
