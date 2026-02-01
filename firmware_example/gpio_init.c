/**
 * ESP32-S3 未使用GPIO初始化配置
 * 用途：防止悬空引脚导致的噪声、误触发和功耗增加
 * 
 * 文件：gpio_init.c
 * 日期：2026-02-01
 */

#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "GPIO_INIT";

/**
 * @brief 初始化所有未使用的GPIO引脚
 * 
 * 策略：
 * 1. IO46（纯输入）：硬件已添加10kΩ下拉电阻
 * 2. 双向GPIO：配置为输出低电平，降低功耗
 * 3. RXD0/TXD0：保留用于USB串口调试
 */
void init_unused_gpio(void)
{
    ESP_LOGI(TAG, "Initializing unused GPIO pins...");

    // ============================================================
    // 1. 输入引脚配置（IO1, IO2）
    // ============================================================
    // 这些引脚配置为输入+内部下拉，防止悬空噪声
    gpio_config_t input_conf = {
        .pin_bit_mask = (1ULL << GPIO_NUM_1) | (1ULL << GPIO_NUM_2),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,  // 使能内部下拉
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&input_conf);
    ESP_LOGI(TAG, "Configured IO1, IO2 as input with pulldown");

    // ============================================================
    // 2. 未使用的双向GPIO配置为输出低电平
    // ============================================================
    // 目的：降低功耗，避免悬空引脚震荡消耗电流
    const gpio_num_t unused_gpios[] = {
        GPIO_NUM_38,  // 引脚31
        GPIO_NUM_39,  // 引脚32
        GPIO_NUM_40,  // 引脚33
        GPIO_NUM_41,  // 引脚34
        GPIO_NUM_42,  // 引脚35
        GPIO_NUM_45,  // 引脚26
        GPIO_NUM_47,  // 引脚24
        GPIO_NUM_48   // 引脚25
    };

    for (int i = 0; i < sizeof(unused_gpios) / sizeof(gpio_num_t); i++) {
        gpio_set_direction(unused_gpios[i], GPIO_MODE_OUTPUT);
        gpio_set_level(unused_gpios[i], 0);  // 输出低电平
    }
    ESP_LOGI(TAG, "Configured %d unused GPIOs as output-low", 
             sizeof(unused_gpios) / sizeof(gpio_num_t));

    // ============================================================
    // 3. 调试串口引脚（可选配置）
    // ============================================================
    #ifdef DISABLE_DEBUG_UART
    // 如果不使用USB串口调试，也应配置为输出低电平
    gpio_set_direction(GPIO_NUM_43, GPIO_MODE_OUTPUT);  // TXD0
    gpio_set_level(GPIO_NUM_43, 0);
    gpio_set_direction(GPIO_NUM_44, GPIO_MODE_OUTPUT);  // RXD0
    gpio_set_level(GPIO_NUM_44, 0);
    ESP_LOGI(TAG, "Debug UART pins configured as output-low");
    #else
    ESP_LOGI(TAG, "Debug UART pins (TXD0/RXD0) kept for USB debugging");
    #endif

    // ============================================================
    // 4. IO46 - 纯输入引脚（硬件已处理）
    // ============================================================
    // IO46在PCB上已连接10kΩ下拉电阻到GND
    // ESP32-S3的IO46只能配置为输入，无法通过软件使能内部上下拉
    // 因此必须通过硬件电阻处理
    ESP_LOGI(TAG, "IO46 handled by hardware pulldown resistor");

    ESP_LOGI(TAG, "All unused GPIO pins initialized successfully");
}

/**
 * @brief 深度睡眠前的GPIO配置（低功耗优化）
 * 
 * 在进入深度睡眠前，将所有GPIO配置为低功耗状态
 */
void prepare_deep_sleep_gpio(void)
{
    ESP_LOGI(TAG, "Preparing GPIOs for deep sleep...");

    // 配置RTC GPIO的上下拉状态
    // 在深度睡眠期间保持有效
    rtc_gpio_pulldown_en(GPIO_NUM_1);
    rtc_gpio_pulldown_en(GPIO_NUM_2);
    
    // 其他未使用的GPIO已经是输出低电平，无需额外配置
    
    ESP_LOGI(TAG, "GPIOs prepared for deep sleep");
}

/**
 * @brief 获取未使用GPIO的状态（用于诊断）
 * 
 * @return 返回未使用GPIO的配置状态字符串
 */
const char* get_unused_gpio_status(void)
{
    static char status[256];
    
    snprintf(status, sizeof(status),
        "Unused GPIO Status:\n"
        "  IO1:  %s (Level: %d)\n"
        "  IO2:  %s (Level: %d)\n"
        "  IO38: %s (Level: %d)\n"
        "  IO39: %s (Level: %d)\n"
        "  IO40: %s (Level: %d)\n"
        "  IO41: %s (Level: %d)\n"
        "  IO42: %s (Level: %d)\n"
        "  IO45: %s (Level: %d)\n"
        "  IO46: INPUT (HW pulldown)\n"
        "  IO47: %s (Level: %d)\n"
        "  IO48: %s (Level: %d)",
        gpio_get_direction(GPIO_NUM_1) == GPIO_MODE_INPUT ? "INPUT" : "OUTPUT",
        gpio_get_level(GPIO_NUM_1),
        gpio_get_direction(GPIO_NUM_2) == GPIO_MODE_INPUT ? "INPUT" : "OUTPUT",
        gpio_get_level(GPIO_NUM_2),
        gpio_get_direction(GPIO_NUM_38) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_38),
        gpio_get_direction(GPIO_NUM_39) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_39),
        gpio_get_direction(GPIO_NUM_40) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_40),
        gpio_get_direction(GPIO_NUM_41) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_41),
        gpio_get_direction(GPIO_NUM_42) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_42),
        gpio_get_direction(GPIO_NUM_45) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_45),
        gpio_get_direction(GPIO_NUM_47) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_47),
        gpio_get_direction(GPIO_NUM_48) == GPIO_MODE_OUTPUT ? "OUTPUT" : "INPUT",
        gpio_get_level(GPIO_NUM_48)
    );
    
    return status;
}

/**
 * @brief 主函数中的调用示例
 */
void app_main(void)
{
    // ... 其他初始化代码 ...
    
    // 初始化未使用的GPIO（应在所有GPIO配置完成后调用）
    init_unused_gpio();
    
    // 打印GPIO状态（用于调试）
    ESP_LOGI(TAG, "%s", get_unused_gpio_status());
    
    // ... 应用程序主循环 ...
}
