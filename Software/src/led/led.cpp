#include "led.h"
#include "base.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "board_config.h"

#include <string.h>

namespace cw::led {

static const char* TAG = "led";

// =============================================================================
// WS2812B 时序 (data rate ~800 kHz, T = 1.25us per bit):
//   '0' bit: HIGH 0.40us + LOW 0.85us
//   '1' bit: HIGH 0.80us + LOW 0.45us
//   reset : LOW > 50us
// 用 RMT 10MHz tick (1 tick = 100ns) 编码:
//   '0': HIGH=4 LOW=8
//   '1': HIGH=8 LOW=4
// =============================================================================
static constexpr uint32_t kRmtClkDivider = 8;        // 80MHz / 8 = 10 MHz
static constexpr uint32_t kT0H = 4;                  // 0.4us
static constexpr uint32_t kT0L = 8;                  // 0.8us
static constexpr uint32_t kT1H = 8;                  // 0.8us
static constexpr uint32_t kT1L = 4;                  // 0.4us
static constexpr uint32_t kResetTicks = 600;         // 60us LOW

// 全局亮度系数: 0~255, 256 = 100%, 128 = 50%.
// WS2812B 高亮度下功耗显著, 且板载灯紧贴外壳容易发热; 50% 已经很醒目.
static constexpr uint16_t kRgbBrightness = 128;

static uint32_t millis() {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

LedManager::LedContext::LedContext(gpio_num_t p, LedType t)
    : type(t), pin(p), current_mode(LedMode::Off),
      mode_start_time(0), duration_ms(0), fallback_mode(LedMode::Off),
      is_rgb(false), rmt_channel(RMT_CHANNEL_0), last_rgb_color(0xFFFFFFFFu) {}

LedManager& LedManager::GetInstance() {
    static LedManager instance;
    return instance;
}

void LedManager::AddLed(gpio_num_t pin, LedType t) {
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << pin);
    io_conf.mode = GPIO_MODE_OUTPUT;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_DISABLE;
    gpio_config(&io_conf);
    gpio_set_level(pin, 0);
    leds.emplace_back(pin, t);
}

void LedManager::AddRgbLed(gpio_num_t pin, LedType t, rmt_channel_t channel) {
    rmt_config_t cfg = RMT_DEFAULT_CONFIG_TX(pin, channel);
    cfg.clk_div = kRmtClkDivider;
    esp_err_t r = rmt_config(&cfg);
    if (r != ESP_OK) {
        ESP_LOGE(TAG, "rmt_config GPIO%d failed: %s", (int)pin, esp_err_to_name(r));
        return;
    }
    r = rmt_driver_install(channel, 0, 0);
    if (r != ESP_OK) {
        ESP_LOGE(TAG, "rmt_driver_install ch=%d failed: %s",
                 (int)channel, esp_err_to_name(r));
        return;
    }
    LedContext ctx(pin, t);
    ctx.is_rgb = true;
    ctx.rmt_channel = channel;
    leds.push_back(ctx);
    // 初始关灯
    LedContext& back = leds.back();
    ApplyRgb(back, 0x000000);
    ESP_LOGI(TAG, "RGB LED registered on GPIO%d (rmt ch=%d)",
             (int)pin, (int)channel);
}

void LedManager::Begin(UBaseType_t priority, BaseType_t coreId) {
    if (leds.empty()) return;
    xTaskCreatePinnedToCore(LedManager::TaskWrapper, "LedMgrTask", 2048,
                            this, priority, nullptr, coreId);
}

void LedManager::SetMode(LedType t, LedMode mode,
                         uint32_t duration_ms, LedMode fallback) {
    for (auto& led : leds) {
        if (led.type == t) {
            led.current_mode = mode;
            led.mode_start_time = millis();
            led.duration_ms = duration_ms;
            led.fallback_mode = fallback;
        }
    }
}

LedMode LedManager::GetMode(LedType t) const {
    for (const auto& led : leds) {
        if (led.type == t) return led.current_mode;
    }
    return LedMode::Off;
}

void LedManager::ApplyLed(LedContext& led, bool on) {
    if (led.is_rgb) {
        ApplyRgb(led, on ? cw::board::kLedColorWhite : 0x000000);
    } else {
        gpio_set_level(led.pin, on ? 1 : 0);
    }
}

// 24-bit 颜色 (0xRRGGBB) -> 24 个 RMT item -> WS2812B (高位先送, GRB 顺序)
void LedManager::ApplyRgb(LedContext& led, uint32_t rgb) {
    if (!led.is_rgb) return;
    if (rgb == led.last_rgb_color) return;  // 去重避免高频重写
    led.last_rgb_color = rgb;

    // 应用全局亮度: 每个分量 × kRgbBrightness / 256
    uint8_t R = ((((rgb >> 16) & 0xFF) * kRgbBrightness) >> 8) & 0xFF;
    uint8_t G = ((((rgb >>  8) & 0xFF) * kRgbBrightness) >> 8) & 0xFF;
    uint8_t B = ((((rgb >>  0) & 0xFF) * kRgbBrightness) >> 8) & 0xFF;
    uint8_t grb[3] = { G, R, B };  // WS2812B 字节序

    rmt_item32_t items[24] = {};
    for (int byte = 0; byte < 3; ++byte) {
        for (int bit = 7; bit >= 0; --bit) {
            int idx = byte * 8 + (7 - bit);
            bool one = ((grb[byte] >> bit) & 0x1) != 0;
            items[idx].level0 = 1;
            items[idx].duration0 = one ? kT1H : kT0H;
            items[idx].level1 = 0;
            items[idx].duration1 = one ? kT1L : kT0L;
        }
    }
    rmt_write_items(led.rmt_channel, items, 24, true /* wait done */);
    // reset latch: 把通道空闲拉低维持 >50us; rmt 默认 idle low + tx_done 后
    // 总线已经是 LOW, 这里再短延时给 latch 留余量.
    ets_delay_us(60);
}

void LedManager::TaskWrapper(void* context) {
    static_cast<LedManager*>(context)->RunTask();
}

void LedManager::RunTask() {
    while (true) {
        uint32_t now = millis();

        for (auto& led : leds) {
            if (led.duration_ms > 0 &&
                (now - led.mode_start_time >= led.duration_ms)) {
                led.current_mode = led.fallback_mode;
                led.duration_ms = 0;
            }

            switch (led.current_mode) {
                case LedMode::Off:
                    if (led.is_rgb) ApplyRgb(led, 0x000000);
                    else            ApplyLed(led, false);
                    break;
                case LedMode::On:
                    if (led.is_rgb) ApplyRgb(led, cw::board::kLedColorWhite);
                    else            ApplyLed(led, true);
                    break;
                case LedMode::BlinkSlow: {
                    bool is_on = (now % blink_slow_period_ms) < (blink_slow_period_ms / 2);
                    // RGB 灯闪烁使用白色 (启动/就绪提示); 单色灯直接开/关
                    if (led.is_rgb) ApplyRgb(led, is_on ? cw::board::kLedColorWhite : 0x000000);
                    else            ApplyLed(led, is_on);
                    break;
                }
                case LedMode::BlinkFast: {
                    bool is_on = (now % blink_fast_period_ms) < (blink_fast_period_ms / 2);
                    // RGB 灯快闪使用黄色 (采集模式提示, 与 SolidYellow 语义对齐)
                    if (led.is_rgb) ApplyRgb(led, is_on ? 0xFFA000 : 0x000000);
                    else            ApplyLed(led, is_on);
                    break;
                }
                case LedMode::Breathe:
                    ApplyLed(led, true);
                    break;

                // ===== 状态色: RGB 走对应颜色; 单色 GPIO 灯按 On 处理 =====
                case LedMode::SolidWhite:
                    if (led.is_rgb) ApplyRgb(led, cw::board::kLedColorWhite);
                    else            ApplyLed(led, true);
                    break;
                case LedMode::SolidBlue:
                    if (led.is_rgb) ApplyRgb(led, 0x0000FF);
                    else            ApplyLed(led, true);
                    break;
                case LedMode::SolidGreen:
                    if (led.is_rgb) ApplyRgb(led, 0x00FF00);
                    else            ApplyLed(led, true);
                    break;
                case LedMode::SolidYellow:
                    if (led.is_rgb) ApplyRgb(led, 0xFFA000);  // 暖黄, 纯 0xFFFF00 偏白
                    else            ApplyLed(led, true);
                    break;
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

}
