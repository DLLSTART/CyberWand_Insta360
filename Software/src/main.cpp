extern "C" {
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_sleep.h"
#include "nvs_flash.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
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
// Debug switches — set to true during development, false for production
// =============================================================================
static constexpr bool kDebugImuMonitor  = false;  // print IMU data every 10 frames
static constexpr bool kDebugAcquisition = false;  // double-click to enter dump-to-serial mode

static constexpr uint16_t kModelInputFrames = 150;

// =============================================================================
// System work mode (only used when kDebugAcquisition == true)
// =============================================================================
enum class SystemWorkMode {
    Application,
    Acquisition
};
static SystemWorkMode kWorkMode = SystemWorkMode::Application;

// =============================================================================
// Recording mode (LED-only state, independent of kDebugAcquisition).
// 已连接相机后, 用户在 wand 上双击触摸键, 在 "普通(蓝)" 与 "录制模式(黄)" 之间
// 切换. 该状态只影响 LED 颜色, 不改变 BLE 派发 / CNN 识别行为.
// 未连接相机时强制视为 false, 灯永远白.
// =============================================================================
static bool g_recording_mode = false;

// =============================================================================
// Gesture -> BLE dispatch
// =============================================================================
static void dispatch_gesture_to_ble(cw::cnn::ActionType action) {
    using cw::cnn::ActionType;
    using cw::ble::BleRemote;
    auto& ble = BleRemote::GetInstance();

    if (!ble.IsConnected()) {
        // 需求3: 未连接时应将手势放入 BLE 广播包 Manufacturer Data 供周围扫描者读取.
        // TODO: 实现广播包手势播报路径 (BleRemote::SetAdvGesturePayload)
        // 当前暂时记 log; 非阻塞, 不影响已连接路径.
        ESP_LOGI(TAG, "gesture %d: no GATT conn, adv-broadcast path not yet implemented",
                 (int)action);
        return;
    }

    bool sent = false;
    const char* gname = "unknown";
    switch (action) {
        case ActionType::kCircle_Cw:
        case ActionType::kCircle_Aw:
            // Circle 手势 = 录像键 (BUTTON state=RECORD).
            // Peer toggles start/stop recording based on current state.
            gname = "circle";
            sent = ble.SendRecordToggle();
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
// Double click handler (only compiled when kDebugAcquisition == true)
// =============================================================================
static void double_click_handler(void) {
    if (!kDebugAcquisition) return;

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

    // 长按 + 已连接 = 正在检测手势, 切绿; 未连接时 main_loop 会立即恢复白.
    // 不论是否处在录制模式 (黄), 检测期间都切绿覆盖之.
    if (cw::ble::BleRemote::GetInstance().IsConnected()) {
        led.SetMode(cw::led::LedType::Status, cw::led::LedMode::SolidGreen);
    }

    uint16_t n = 0;
    CaptureExitReason reason = CaptureExitReason::HitMaxFrames;
    ButtonMessage msg{};

    bool fallback_to_polling = !imu.IsInterruptModeActive();

    while (n < buf_capacity) {
        if (fallback_to_polling) {
            vTaskDelay(pdMS_TO_TICKS(cw::board::kImuPollFallbackMs));
        } else if (!imu.WaitForDataReady(cw::board::kImuIntWaitMs)) {
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
                if (kDebugAcquisition) {
                    if (msg.event == ButtonEvent::DoubleClick) {
                        reason = CaptureExitReason::UserDoubleClicked;
                        break;
                    }
                }
            }
        }
    }

    // 不在这里改 LED: 让 main_loop 的 apply_idle_led_color() 把灯恢复到
    // 当前空闲色 (未连接=白 / 录制模式=黄 / 普通模式=蓝).
    out_n = n;
    return reason;
}

// =============================================================================
// Acquisition mode: dump IMU data to serial (only when kDebugAcquisition)
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
// CNN inference + BLE dispatch
// =============================================================================
static void recognize_and_dispatch(const cw::common::IMU* buf, uint16_t n) {
    if (buf == nullptr || n == 0) return;

    static cw::common::IMU normalized[kModelInputFrames]; // BSS, not stack
    cw::cnn::ImuResampler::Resample(buf, n, normalized, kModelInputFrames);

    auto action_type = cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(
        normalized, kModelInputFrames);
    ESP_LOGI(TAG, "action type: %d (from %u raw frames)", (int)action_type, n);

    dispatch_gesture_to_ble(action_type);
}

// =============================================================================
// Handle button press
// =============================================================================
static void handle_button_press(void) {
    cw::common::IMU* buf = nullptr;
    uint16_t n = 0;

    CaptureExitReason reason = capture_press_to_release(buf, n);

    ESP_LOGI(TAG, "capture: n=%u reason=%d", n, (int)reason);

    if (kDebugAcquisition) {
        if (reason == CaptureExitReason::UserDoubleClicked) {
            ESP_LOGI(TAG, "double-click during capture, switching mode");
            double_click_handler();
            return;
        }
    }

    if (n < cw::imu::kContinuousMinFrames) {
        ESP_LOGI(TAG, "gesture too short (%u < %u), discarded",
                 n, cw::imu::kContinuousMinFrames);
        return;
    }

    if (kDebugAcquisition) {
        if (kWorkMode == SystemWorkMode::Acquisition) {
            dump_capture_for_training(buf, n);
            return;
        }
    }

    recognize_and_dispatch(buf, n);
}

// =============================================================================
// IMU monitor task (only when kDebugImuMonitor)
// =============================================================================
static void imu_monitor_task(void* /*arg*/) {
    auto& imu = cw::imu::Mpu6050IMU::GetInstance();
    uint32_t cnt = 0;

    vTaskDelay(pdMS_TO_TICKS(100));

    ESP_LOGI(TAG, "IMU monitor started (print every 10 frames)");

    while (imu.IsInterruptModeActive()) {
        if (!imu.WaitForDataReady(cw::board::kImuIntWaitMs)) {
            vTaskDelay(pdMS_TO_TICKS(cw::board::kImuPollFallbackMs));
        }

        cw::common::IMU frame;
        imu.SampleOneFrame(frame);
        cnt++;

        if (cnt % 10 == 0) {
            ESP_LOGI(TAG, "IMU[%lu] acc=(%+.3f,%+.3f,%+.3f) gyro=(%+.3f,%+.3f,%+.3f)",
                     (unsigned long)cnt,
                     frame.acc.x, frame.acc.y, frame.acc.z,
                     frame.gyro.roll, frame.gyro.pitch, frame.gyro.yaw);
        }
    }

    ESP_LOGW(TAG, "IMU monitor stopped");
    vTaskDelete(nullptr);
}

// =============================================================================
// Power button: triple-click to enter deep sleep, long-press 2s to wake up.
// -----------------------------------------------------------------------------
// 关机:  main loop 收到 ButtonEvent::TripleClick 时调用 enter_deep_sleep().
//        ESP32-S3 进入 deep sleep, 整机电流降到 ~10µA, USB 充电宝若不会因
//        小电流自动断电就能维持供电直至下次唤醒.
// 唤醒:  EXT1 (任意 HIGH) 监听触摸开关 -> 任意一击都会唤醒主 CPU.
//        但 app_main 进来第一件事是 verify_wake_long_press_or_sleep_back():
//        轮询 GPIO 2 秒确认用户确实在长按, 中途松手就立刻配回 EXT1 + 再次
//        deep sleep, 用户感觉到的就是"短按没反应". 满 2 秒才继续正常启动.
// 注意:
//   - kPinTouchSwitch 必须落在 ESP32-S3 的 RTC GPIO 范围 (GPIO0~GPIO21),
//     否则 EXT1 不能监听; GPIO4 落在范围内, OK.
//   - 长按确认是软件层面实现, 主 CPU 短暂上电 (~2s 满载约 200mA);
//     真正的"硬件级长按唤醒"需要 ULP 协处理器, 这里不做.
// =============================================================================
static constexpr uint32_t kWakeVerifyHoldMs = 2000;
// 上电 / 断开后开始广播, 若 kAdvIdleSleepMs 内仍未建立连接 -> 自动 deep sleep,
// 避免长时间空载消耗电池. 用户长按 2s 即可重新唤醒并再次广播.
static constexpr uint32_t kAdvIdleSleepMs = 120 * 1000;

static void enter_deep_sleep(const char* reason) {
    ESP_LOGW(TAG, "deep sleep (%s)", reason ? reason : "unknown");

    cw::led::LedManager::GetInstance().SetMode(
        cw::led::LedType::Status, cw::led::LedMode::Off);

    // 等触摸开关松手再睡, 否则刚睡下就立刻被自己触发醒
    while (gpio_get_level((gpio_num_t)cw::board::kPinTouchSwitch) == 1) {
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    vTaskDelay(pdMS_TO_TICKS(200));

    const uint64_t wake_mask = 1ULL << cw::board::kPinTouchSwitch;
    esp_sleep_enable_ext1_wakeup(wake_mask, ESP_EXT1_WAKEUP_ANY_HIGH);

    rtc_gpio_init((gpio_num_t)cw::board::kPinTouchSwitch);
    rtc_gpio_set_direction((gpio_num_t)cw::board::kPinTouchSwitch,
                           RTC_GPIO_MODE_INPUT_ONLY);
    rtc_gpio_pulldown_en((gpio_num_t)cw::board::kPinTouchSwitch);
    rtc_gpio_pullup_dis((gpio_num_t)cw::board::kPinTouchSwitch);

    ESP_LOGI(TAG, "wake source: GPIO%u (any HIGH, will require %u ms hold)",
             (unsigned)cw::board::kPinTouchSwitch,
             (unsigned)kWakeVerifyHoldMs);

    esp_deep_sleep_start();
}

// 唤醒后调用, 验证用户确实长按了 kWakeVerifyHoldMs.
// 不通过就直接重新进入 deep sleep, 函数不返回.
// 通过则等用户松手 + 100ms 防抖再返回, 让 ButtonManager 拿到一个干净的引脚状态.
static void verify_wake_long_press_or_sleep_back() {
    const gpio_num_t pin = (gpio_num_t)cw::board::kPinTouchSwitch;

    // RTC GPIO 已 deinit, 重新配成普通输入
    gpio_config_t io = {};
    io.pin_bit_mask  = 1ULL << pin;
    io.mode          = GPIO_MODE_INPUT;
    io.pull_up_en    = GPIO_PULLUP_DISABLE;
    io.pull_down_en  = GPIO_PULLDOWN_ENABLE;
    io.intr_type     = GPIO_INTR_DISABLE;
    gpio_config(&io);

    const uint32_t step_ms = 20;
    uint32_t elapsed = 0;

    ESP_LOGI(TAG, "wake-verify: hold touch for %u ms to confirm boot",
             (unsigned)kWakeVerifyHoldMs);

    while (elapsed < kWakeVerifyHoldMs) {
        if (gpio_get_level(pin) == 0) {
            ESP_LOGW(TAG, "wake-verify: released early at %u ms -> back to sleep",
                     (unsigned)elapsed);
            // 配回 EXT1 + 重新进入 deep sleep (不返回)
            const uint64_t wake_mask = 1ULL << pin;
            esp_sleep_enable_ext1_wakeup(wake_mask, ESP_EXT1_WAKEUP_ANY_HIGH);
            rtc_gpio_init(pin);
            rtc_gpio_set_direction(pin, RTC_GPIO_MODE_INPUT_ONLY);
            rtc_gpio_pulldown_en(pin);
            rtc_gpio_pullup_dis(pin);
            esp_deep_sleep_start();
        }
        vTaskDelay(pdMS_TO_TICKS(step_ms));
        elapsed += step_ms;
    }

    ESP_LOGI(TAG, "wake-verify: passed, waiting for release");
    while (gpio_get_level(pin) == 1) {
        vTaskDelay(pdMS_TO_TICKS(20));
    }
    vTaskDelay(pdMS_TO_TICKS(100));
    ESP_LOGI(TAG, "wake-verify: released, continuing boot");
}

// =============================================================================
// Idle LED color: 4 种状态 ——
//   未连接                       -> 白
//   已连接 + 普通模式 + 空闲      -> 蓝
//   已连接 + 录制模式 + 空闲      -> 黄
//   已连接 + 按住触摸键检测手势   -> 绿 (capture_press_to_release() 切绿后,
//                                    main_loop 阻塞在 handle_button_press 中,
//                                    本函数自然不会被调用; 一旦松手返回,
//                                    下一轮 tick 这里就把灯刷回 蓝/黄/白.)
// =============================================================================
static void apply_idle_led_color() {
    bool connected = cw::ble::BleRemote::GetInstance().IsConnected();
    cw::led::LedMode want;
    if (!connected) {
        if (g_recording_mode) g_recording_mode = false;  // 断开自动退出录制模式
        want = cw::led::LedMode::SolidWhite;
    } else if (g_recording_mode) {
        want = cw::led::LedMode::SolidYellow;
    } else {
        want = cw::led::LedMode::SolidBlue;
    }
    auto cur = cw::led::LedManager::GetInstance().GetMode(cw::led::LedType::Status);
    if (cur != want) {
        cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status, want);
    }
}

// =============================================================================
// Main loop task
// =============================================================================
static void main_loop_task(void* /*arg*/) {
    using namespace cw::button;

    while (true) {
        cw::ble::BleRemote::GetInstance().SwitchAdvByTick();
        apply_idle_led_color();

        // Peer sends SHUTDOWN command -> deep sleep
        if (cw::ble::BleRemote::GetInstance().ConsumeShutdownRequest()) {
            enter_deep_sleep("peer SHUTDOWN");
        }

        // 广播超过 kAdvIdleSleepMs 仍未建立连接 -> 自动 deep sleep, 省电
        uint32_t adv_idle_ms =
            cw::ble::BleRemote::GetInstance().GetUnconnectedAdvertisingMs();
        if (adv_idle_ms >= kAdvIdleSleepMs) {
            enter_deep_sleep("adv idle timeout");
        }

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
                } else if (ButtonEvent::TripleClick == message.event) {
                    enter_deep_sleep("triple-click");
                } else if (ButtonEvent::DoubleClick == message.event) {
                    // 已连接才切录制模式 (黄); 未连接时双击忽略 (灯永远白).
                    if (cw::ble::BleRemote::GetInstance().IsConnected()) {
                        g_recording_mode = !g_recording_mode;
                        ESP_LOGI(TAG, "recording mode -> %s",
                                 g_recording_mode ? "ON (yellow)" : "OFF (blue)");
                    }
                    if (kDebugAcquisition) {
                        double_click_handler();
                    }
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

    esp_sleep_wakeup_cause_t wake = esp_sleep_get_wakeup_cause();
    if (wake == ESP_SLEEP_WAKEUP_EXT1) {
        uint64_t mask = esp_sleep_get_ext1_wakeup_status();
        ESP_LOGI(TAG, "wakeup: EXT1 mask=0x%llx (touch switch)",
                 (unsigned long long)mask);
        // 退出 RTC GPIO 模式, 把引脚交还给普通 GPIO 驱动
        rtc_gpio_deinit((gpio_num_t)cw::board::kPinTouchSwitch);
        // 必须长按 kWakeVerifyHoldMs 才算真唤醒, 否则原路返回 deep sleep
        verify_wake_long_press_or_sleep_back();
    } else if (wake != ESP_SLEEP_WAKEUP_UNDEFINED) {
        ESP_LOGI(TAG, "wakeup: cause=%d", (int)wake);
    } else {
        ESP_LOGI(TAG, "wakeup: cold boot");
    }

    // NVS init
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    // IMU init
    bool imu_ok = cw::imu::Mpu6050IMU::GetInstance().Init();
    if (imu_ok) {
        ESP_LOGI(TAG, "[selftest] MPU6050: PASS");
        bool int_ok = cw::imu::Mpu6050IMU::GetInstance().EnableDataReadyInterrupt(
            cw::board::kPinImuInt);
        ESP_LOGI(TAG, "[selftest] DRDY interrupt: %s",
                 int_ok ? "ENABLED" : "FAILED");
        if (kDebugImuMonitor) {
            if (int_ok) {
                xTaskCreatePinnedToCore(imu_monitor_task, "imuMon", 4096,
                                        nullptr, 2, nullptr, 1);
            }
        }
    } else {
        ESP_LOGW(TAG, "[selftest] MPU6050: FAIL");
    }

    // CNN init
    cw::cnn::ActionRecognitionCNN::GetInstance().Init();

    // Button (touch switch) init
    cw::button::ButtonManager::GetInstance().AddButton(
        (gpio_num_t)cw::board::kPinTouchSwitch,
        cw::button::ButtonType::JoystickBtn, true);
    cw::button::ButtonManager::GetInstance().Begin();

    // LED init: 板载 WS2812B (GPIO48) 用 RMT 驱动
    cw::led::LedManager::GetInstance().AddRgbLed(
        (gpio_num_t)cw::board::kPinRgbLed, cw::led::LedType::Status);
    cw::led::LedManager::GetInstance().Begin();

    // BLE init
    cw::ble::BleRemote::GetInstance().Init();

    // Summary
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "  IMU:   %s", imu_ok ? "OK" : "FAIL");
    ESP_LOGI(TAG, "  BLE:   %s", cw::ble::cfg::kRemoteGapName);
    ESP_LOGI(TAG, "========================================");

    // Blink LED to signal boot complete
    cw::led::LedManager::GetInstance().SetMode(
        cw::led::LedType::Status, cw::led::LedMode::BlinkSlow);

    // Start main loop
    xTaskCreatePinnedToCore(main_loop_task, "mainLoop", 4096,
                            nullptr, 3, nullptr, 1);
}