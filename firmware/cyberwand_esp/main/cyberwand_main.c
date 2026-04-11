/**
 * CyberWand v3.0 - 手势遥控器
 * 主程序 - ESP-IDF 版本
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "driver/i2c.h"

#include "mpu6050.h"
#include "usb_serial.h"
#include "ble_comm.h"
#include "button.h"
#include "led.h"
#include "pose_model.h"

static const char* TAG = "CyberWand";

// 模式定义
typedef enum {
    MODE_RECORD = 0,
    MODE_CONTROL
} work_mode_t;

static work_mode_t current_mode = MODE_RECORD;
static bool continuous_mode = false;
static imu_data_t last_imu = {0};
static pose_type_t last_pose = POSE_IDLE;

void app_main(void)
{
    ESP_LOGI(TAG, "CyberWand v3.0 Starting...");
    
    // 1. 初始化 MPU6050
    ESP_ERROR_CHECK(mpu6050_init());
    ESP_LOGI(TAG, "MPU6050 initialized");
    
    // 2. 初始化 USB 串口
    ESP_ERROR_CHECK(usb_serial_init());
    ESP_LOGI(TAG, "USB Serial initialized");
    
    // 3. 初始化蓝牙
    ESP_ERROR_CHECK(ble_comm_init());
    ESP_LOGI(TAG, "Bluetooth initialized");
    
    // 4. 初始化按键和 LED
    button_init();
    led_init();
    led_set(LED_IDLE);
    
    ESP_LOGI(TAG, "Starting main loop (MODE_RECORD)...");
    
    // 5. 主循环 (100Hz)
    while (1) {
        // 读取 IMU 数据
        imu_data_t imu;
        if (mpu6050_read(&imu) == ESP_OK) {
            last_imu = imu;
        }
        
        // 检测按键事件
        key_event_t key = button_get_event();
        
        // 状态机处理
        switch (current_mode) {
            case MODE_RECORD:
                if (key == KEY_SHORT_PRESS) {
                    current_mode = MODE_CONTROL;
                    led_set(LED_CONTROL);
                    ESP_LOGI(TAG, "Mode: RECORD → CONTROL");
                } else if (key == KEY_LONG_PRESS) {
                    continuous_mode = true;
                    led_set(LED_TRANSFER);
                } else if (key == KEY_LONG_RELEASE) {
                    continuous_mode = false;
                    led_set(LED_RECORD);
                }
                
                // 发送 IMU 数据到 USB
                if (continuous_mode || key == KEY_SHORT_PRESS) {
                    usb_serial_send_imu(&imu);
                }
                break;
                
            case MODE_CONTROL:
                if (key == KEY_SHORT_PRESS) {
                    current_mode = MODE_RECORD;
                    led_set(LED_RECORD);
                    ESP_LOGI(TAG, "Mode: CONTROL → RECORD");
                } else if (key == KEY_LONG_PRESS) {
                    continuous_mode = true;
                    led_set(LED_TRANSFER);
                } else if (key == KEY_LONG_RELEASE) {
                    continuous_mode = false;
                    led_set(LED_CONTROL);
                }
                
                // 姿态识别
                pose_type_t pose = pose_recognize(&imu, &last_imu);
                
                // 发送蓝牙消息
                if (continuous_mode || pose != last_pose) {
                    ble_comm_send_pose(pose);
                    last_pose = pose;
                    ESP_LOGD(TAG, "Pose: %d", pose);
                }
                break;
        }
        
        last_imu = imu;
        vTaskDelay(10 / portTICK_PERIOD_MS); // 100Hz
    }
}
