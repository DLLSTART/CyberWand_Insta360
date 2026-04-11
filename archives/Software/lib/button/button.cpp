#include "button.h"

namespace cw::button {

// 构造函数：初始化时状态为 Idle，标志位设为 false
ButtonManager::ButtonContext::ButtonContext(uint8_t p, ButtonType t, bool level) 
    : pin(p), type(t), active_level(level), state(ButtonState::Idle), 
      press_time(0), release_time(0), is_press_emitted(false) {}

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

// 核心状态机实现 (消除魔法数字)
void ButtonManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& btn : buttons) {
            bool is_pressed = (digitalRead(btn.pin) == btn.active_level);

            switch (btn.state) {
                case ButtonState::Idle:
                    if (is_pressed) {
                        btn.press_time = now;
                        btn.is_press_emitted = false; // 重置按下标志
                        btn.state = ButtonState::Pressed;
                    }
                    break;

                case ButtonState::Pressed:
                    if (is_pressed) {
                        // 1. 经过消抖时间后，发送一次 PressDown 事件
                        if (!btn.is_press_emitted && (now - btn.press_time >= debounce_ms)) {
                            SendEvent(btn.type, ButtonEvent::PressDown);
                            btn.is_press_emitted = true;
                        }
                        // 2. 超过长按时间，发送 LongPress 事件
                        if (now - btn.press_time >= long_press_ms) {
                            SendEvent(btn.type, ButtonEvent::LongPress);
                            btn.state = ButtonState::WaitForRelease;
                        }
                    } else {
                        // 物理释放
                        if (now - btn.press_time >= debounce_ms) {
                            btn.release_time = now;
                            SendEvent(btn.type, ButtonEvent::Release); // 发送 Release 事件
                            btn.state = ButtonState::WaitForDoubleClick; 
                        } else {
                            // 时间太短，判定为抖动，回退状态
                            btn.state = ButtonState::Idle; 
                        }
                    }
                    break;

                case ButtonState::WaitForDoubleClick:
                    if (is_pressed) {
                        // 在等待间隔内再次按下，判定为双击
                        if (now - btn.release_time <= double_click_ms) {
                            SendEvent(btn.type, ButtonEvent::PressDown);
                            SendEvent(btn.type, ButtonEvent::DoubleClick);
                            btn.state = ButtonState::WaitForRelease; 
                        }
                    } else {
                        // 超时没有再次按下，判定为单击
                        if (now - btn.release_time > double_click_ms) {
                            SendEvent(btn.type, ButtonEvent::SingleClick);
                            btn.state = ButtonState::Idle;
                        }
                    }
                    break;

                case ButtonState::WaitForRelease:
                    if (!is_pressed) {
                        // 发送最后一次释放事件，并回到空闲
                        SendEvent(btn.type, ButtonEvent::Release);
                        btn.state = ButtonState::Idle;
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

void ButtonManager::AddButton(uint8_t pin, ButtonType t, bool active_level) {
    pinMode(pin, INPUT_PULLUP); 
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