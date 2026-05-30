extern "C" {
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"
}

#include "board_config.h"
#include "protocol_config.h"
#include "mpu6050_imu.h"
#include "cnn.h"
#include "imu_resampler.h"
#include "button.h"
#include "led.h"
#include "ble_remote.h"

static const char* TAG = "main";

// =============================================================================
// System work mode
// =============================================================================
enum class SystemWorkMode {
    Application,
    Acquisition
};
static SystemWorkMode kWorkMode = SystemWorkMode::Application;
static constexpr uint16_t kModelInputFrames = 150;

// =============================================================================
// Gesture -> BLE dispatch
// =============================================================================
static void dispatch_gesture_to_ble(cw::cnn::ActionType action) {
    using cw::cnn::ActionType;
    using cw::ble::BleRemote;
    auto& ble = BleRemote::GetInstance();

    if (!ble.IsConnected()) {
        ESP_LOGI(TAG, "gesture %d ignored: not connected", (int)action);
        return;
    }

    bool sent = false;
    const char* gname = "unknown";
    switch (action) {
        case ActionType::kCircle_Cw:
        case ActionType::kCircle_Aw:
            gname = "circle";
            sent = ble.SendRecordStart();
            break;
        case ActionType::kCheck:
            gname = "check";
            sent = ble.CycleToNextSubMode();
            break;
        case ActionType::kCross_Left:
        case ActionType::kCross_Right:
            gname = "cross";
            sent = ble.SendHighlightMark();
            break;
        case ActionType::kUnknown:
        default:
            ESP_LOGI(TAG, "unknown gesture %d, ignored", (int)action);
            return;
    }

    if (sent) {
        ESP_LOGI(TAG, "gesture %s -> cmd OK", gname);
    } else {
        ESP_LOGW(TAG, "gesture %s -> cmd FAILED", gname);
    }
}

// =============================================================================
// Double click handler
// =============================================================================
static void double_click_handler(void) {
    if (kWorkMode == SystemWorkMode::Application) {
        kWorkMode = SystemWorkMode::Acquisition;
        cw::led::LedManager::GetInstance().SetMode(
            cw::led::LedType::Status, cw::led::LedMode::BlinkFast,
            2000, cw::led::LedMode::Off);
        ESP_LOGI(TAG, "mode -> Acquisition");
    } else {
        kWorkMode = SystemWorkMode::Application;
        cw::led::LedManager::GetInstance().SetMode(
            cw::led::LedType::Status, cw::led::LedMode::On,
            3000, cw::led::LedMode::Off);
        ESP_LOGI(TAG, "mode -> Application");
    }
}

// =============================================================================
// Capture exit reason
// =============================================================================
enum class CaptureExitReason {
    UserReleased,
    UserDoubleClicked,
    HitMaxFrames,
};

// =============================================================================
// Capture press-to-release with interrupt-driven IMU sampling
// =============================================================================
static CaptureExitReason capture_press_to_release(cw::common::IMU*& out_buf,
                                                   uint16_t& out_n) {
    using cw::button::ButtonEvent;
    using cw::button::ButtonMessage;
    using cw::button::ButtonType;

    auto& imu = cw::imu::Mpu6050IMU::GetInstance();
    auto& btn = cw::button::ButtonManager::GetInstance();
    auto& led = cw::led::LedManager::GetInstance();

    uint16_t buf_capacity = 0;
    out_buf = imu.GetContinuousBuffer(buf_capacity);
    if (buf_capacity > cw::imu::kContinuousMaxFrames) {
        buf_capacity = cw::imu::kContinuousMaxFrames;
    }

    led.SetMode(cw::led::LedType::Status, cw::led::LedMode::On);

    uint16_t n = 0;
    CaptureExitReason reason = CaptureExitReason::HitMaxFrames;
    ButtonMessage msg{};

    bool fallback_to_polling = !imu.IsInterruptModeActive();

    while (n < buf_capacity) {
        if (fallback_to_polling) {
            vTaskDelay(pdMS_TO_TICKS(cw::board::kImuPollFallbackMs));
        } else if (!imu.WaitForDataReady(cw::board::kImuIntWaitMs)) {
            ESP_LOGW(TAG, "DRDY timeout at frame %u, fallback to polling", n);
            fallback_to_polling = true;
            vTaskDelay(pdMS_TO_TICKS(cw::board::kImuPollFallbackMs));
        }

        imu.SampleOneFrame(out_buf[n]);
        ++n;

        if (btn.GetEvent(msg, 0)) {
            if (msg.type == ButtonType::JoystickBtn) {
                if (msg.event == ButtonEvent::Release) {
                    reason = CaptureExitReason::UserReleased;
                    break;
                }
                if (msg.event == ButtonEvent::DoubleClick) {
                    reason = CaptureExitReason::UserDoubleClicked;
                    break;
                }
            }
        }
    }

    led.SetMode(cw::led::LedType::Status, cw::led::LedMode::Off);
    out_n = n;
    return reason;
}

// =============================================================================
// Acquisition mode: dump IMU data to serial
// =============================================================================
static void dump_capture_for_training(const cw::common::IMU* buf, uint16_t n) {
    if (buf == nullptr || n == 0) return;
    ESP_LOGI(TAG, "capture begin, %u frames", n);
    for (uint16_t i = 0; i < n; ++i) {
        ESP_LOGI(TAG, "%f\t%f\t%f\t%f\t%f\t%f",
                 buf[i].acc.x, buf[i].acc.y, buf[i].acc.z,
                 buf[i].gyro.roll, buf[i].gyro.pitch, buf[i].gyro.yaw);
    }
    ESP_LOGI(TAG, "capture end");
}

// =============================================================================
// Application mode: resample + CNN inference + BLE dispatch
// =============================================================================
static void recognize_and_dispatch(const cw::common::IMU* buf, uint16_t n) {
    if (buf == nullptr || n == 0) return;

    cw::common::IMU normalized[kModelInputFrames];
    cw::cnn::ImuResampler::Resample(buf, n, normalized, kModelInputFrames);

    auto action_type = cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(
        normalized, kModelInputFrames);
    ESP_LOGI(TAG, "action type: %d (from %u raw frames)",
             (int)action_type, n);

    dispatch_gesture_to_ble(action_type);
}

// =============================================================================
// Handle button press
// =============================================================================
static void handle_button_press(void) {
    cw::common::IMU* buf = nullptr;
    uint16_t n = 0;

    CaptureExitReason reason = capture_press_to_release(buf, n);

    ESP_LOGI(TAG, "capture: buf=%p n=%u reason=%d",
             (void*)buf, n, (int)reason);

    if (reason == CaptureExitReason::UserDoubleClicked) {
        ESP_LOGI(TAG, "double-click during capture, switching mode");
        double_click_handler();
        return;
    }

    if (n < cw::imu::kContinuousMinFrames) {
        ESP_LOGI(TAG, "gesture too short (%u < %u), discarded",
                 n, cw::imu::kContinuousMinFrames);
        return;
    }

    if (kWorkMode == SystemWorkMode::Application) {
        recognize_and_dispatch(buf, n);
    } else {
        dump_capture_for_training(buf, n);
    }
}

// =============================================================================
// Main loop task (runs as FreeRTOS task from app_main)
// =============================================================================
static void main_loop_task(void* /*arg*/) {
    using namespace cw::button;

    while (true) {
        cw::ble::BleRemote::GetInstance().SwitchAdvByTick();

        ButtonMessage message{};
        if (!ButtonManager::GetInstance().GetEvent(message, pdMS_TO_TICKS(20))) {
            continue;
        }

        switch (message.type) {
            case ButtonType::Power:
                ESP_LOGI(TAG, "power button");
                break;
            case ButtonType::JoystickBtn:
                if (ButtonEvent::PressDown == message.event) {
                    handle_button_press();
                } else if (ButtonEvent::DoubleClick == message.event) {
                    double_click_handler();
                }
                break;
            case ButtonType::Menu:
                ESP_LOGI(TAG, "menu button");
                break;
        }
    }
}

// =============================================================================
// app_main: ESP-IDF entry point
// =============================================================================
extern "C" void app_main() {
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "  CyberWand Boot Self-Test (ESP-IDF)");
    ESP_LOGI(TAG, "========================================");

    // NVS init (required for BLE and PairedStore)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    // IMU init (includes I2C bus scan and MPU6050 self-test)
    bool imu_ok = cw::imu::Mpu6050IMU::GetInstance().Init();
    if (imu_ok) {
        ESP_LOGI(TAG, "[selftest] MPU6050: PASS");
        bool int_ok = cw::imu::Mpu6050IMU::GetInstance().EnableDataReadyInterrupt(
            cw::board::kPinImuInt);
        ESP_LOGI(TAG, "[selftest] DRDY interrupt: %s",
                 int_ok ? "ENABLED" : "FAILED");
    } else {
        ESP_LOGW(TAG, "[selftest] MPU6050: FAIL");
    }

    // CNN init
    cw::cnn::ActionRecognitionCNN::GetInstance().Init();
    ESP_LOGI(TAG, "[selftest] CNN: initialized");

    // Button (touch switch) init
    cw::button::ButtonManager::GetInstance().AddButton(
        (gpio_num_t)cw::board::kPinTouchSwitch,
        cw::button::ButtonType::JoystickBtn, true /* active HIGH */);
    cw::button::ButtonManager::GetInstance().Begin();
    ESP_LOGI(TAG, "[selftest] Touch switch: GPIO%d (active HIGH)",
             cw::board::kPinTouchSwitch);

    // LED init (simple GPIO)
    cw::led::LedManager::GetInstance().AddLed(
        (gpio_num_t)cw::board::kPinStatusLed, cw::led::LedType::Status);
    cw::led::LedManager::GetInstance().Begin();
    ESP_LOGI(TAG, "[selftest] LED: GPIO%d", cw::board::kPinStatusLed);

    // BLE init
    cw::ble::BleRemote::GetInstance().Init();
    ESP_LOGI(TAG, "[selftest] BLE: advertising as \"%s\"",
             cw::ble::cfg::kRemoteGapName);

    // Summary
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "  IMU:   %s", imu_ok ? "OK" : "FAIL");
    ESP_LOGI(TAG, "  Touch: GPIO%d", cw::board::kPinTouchSwitch);
    ESP_LOGI(TAG, "  LED:   GPIO%d", cw::board::kPinStatusLed);
    ESP_LOGI(TAG, "  BLE:   %s", cw::ble::cfg::kRemoteGapName);
    ESP_LOGI(TAG, "========================================");

    // Blink LED to signal boot complete
    cw::led::LedManager::GetInstance().SetMode(
        cw::led::LedType::Status, cw::led::LedMode::BlinkSlow);

    // Start main loop task
    xTaskCreatePinnedToCore(main_loop_task, "mainLoop", 4096,
                            nullptr, 3, nullptr, 1);
}
