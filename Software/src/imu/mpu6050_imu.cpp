#include "mpu6050_imu.h"
#include <stdint.h>
#include <string.h>
#include "base.h"
#include "common.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "driver/i2c.h"
#include "driver/gpio.h"
#include "board_config.h"

static const char* TAG = "imu";

namespace cw {
namespace imu {

// I2C port and MPU6050 address
static constexpr i2c_port_t kI2cPort = I2C_NUM_0;
static constexpr uint8_t kMPU6050_ADDR = 0x68;

// MPU6050 register addresses
static constexpr uint8_t REG_SMPLRT_DIV   = 0x19;
static constexpr uint8_t REG_CONFIG       = 0x1A;
static constexpr uint8_t REG_GYRO_CONFIG  = 0x1B;
static constexpr uint8_t REG_ACCEL_CONFIG = 0x1C;
static constexpr uint8_t REG_INT_PIN_CFG  = 0x37;
static constexpr uint8_t REG_INT_ENABLE   = 0x38;
static constexpr uint8_t REG_ACCEL_XOUT_H = 0x3B;
static constexpr uint8_t REG_PWR_MGMT_1   = 0x6B;
static constexpr uint8_t REG_WHO_AM_I     = 0x75;

// DRDY interrupt state
static SemaphoreHandle_t s_drdy_sem    = nullptr;
static volatile bool     s_int_mode_on = false;

static void IRAM_ATTR drdy_isr(void* /*arg*/) {
    BaseType_t hpw = pdFALSE;
    if (s_drdy_sem != nullptr) {
        xSemaphoreGiveFromISR(s_drdy_sem, &hpw);
    }
    if (hpw == pdTRUE) {
        portYIELD_FROM_ISR();
    }
}

// --- ESP-IDF I2C register operations ---

static bool i2c_write_reg(uint8_t reg, uint8_t val) {
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (kMPU6050_ADDR << 1) | 0, true);  // write
    i2c_master_write_byte(cmd, reg, true);
    i2c_master_write_byte(cmd, val, true);
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(50));
    i2c_cmd_link_delete(cmd);
    return ret == ESP_OK;
}

static bool i2c_read_reg(uint8_t reg, uint8_t* val) {
    // Step 1: Write register address (STOP after write)
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (kMPU6050_ADDR << 1) | 0, true);
    i2c_master_write_byte(cmd, reg, true);
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    if (ret != ESP_OK) return false;

    // Step 2: Read data byte (separate transaction, STOP after read)
    cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (kMPU6050_ADDR << 1) | 1, true);
    i2c_master_read_byte(cmd, val, I2C_MASTER_NACK);
    i2c_master_stop(cmd);
    ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    return ret == ESP_OK;
}

static bool i2c_read_motion6(int16_t* ax, int16_t* ay, int16_t* az,
                              int16_t* gx, int16_t* gy, int16_t* gz) {
    uint8_t buf[14];

    // Step 1: Write register address (REG_ACCEL_XOUT_H = 0x3B), STOP
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (kMPU6050_ADDR << 1) | 0, true);
    i2c_master_write_byte(cmd, REG_ACCEL_XOUT_H, true);
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);
    if (ret != ESP_OK) return false;

    // Step 2: Read 14 bytes (separate transaction, STOP)
    cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (kMPU6050_ADDR << 1) | 1, true);
    i2c_master_read(cmd, buf, 14, I2C_MASTER_LAST_NACK);
    i2c_master_stop(cmd);
    ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(100));
    i2c_cmd_link_delete(cmd);

    if (ret != ESP_OK) return false;

    *ax = (int16_t)((buf[0] << 8) | buf[1]);
    *ay = (int16_t)((buf[2] << 8) | buf[3]);
    *az = (int16_t)((buf[4] << 8) | buf[5]);
    // buf[6..7] = temperature, skip
    *gx = (int16_t)((buf[8]  << 8) | buf[9]);
    *gy = (int16_t)((buf[10] << 8) | buf[11]);
    *gz = (int16_t)((buf[12] << 8) | buf[13]);
    return true;
}

// --- I2C bus scan ---

static void i2c_bus_scan() {
    ESP_LOGI(TAG, "I2C bus scan:");
    uint8_t found = 0;
    for (uint8_t addr = 0x03; addr < 0x78; ++addr) {
        i2c_cmd_handle_t cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (addr << 1) | 0, true);
        i2c_master_stop(cmd);
        esp_err_t ret = i2c_master_cmd_begin(kI2cPort, cmd, pdMS_TO_TICKS(10));
        i2c_cmd_link_delete(cmd);
        if (ret == ESP_OK) {
            uint8_t whoami = 0xFF;
            i2c_read_reg(REG_WHO_AM_I, &whoami);
            const char* chip = "unknown";
            switch (whoami) {
                case 0x68: chip = "MPU-6050"; break;
                case 0x70: chip = "MPU-6000/clone"; break;
                case 0x71: chip = "MPU-6500"; break;
                case 0x74: chip = "MPU-9250"; break;
                case 0x12: chip = "ICM-20602"; break;
                case 0x60: chip = "MPU-6050 clone / ICM-42688"; break;
            }
            ESP_LOGI(TAG, "  device at 0x%02X  WHO_AM_I=0x%02X (%s)", addr, whoami, chip);
            ++found;
        }
    }
    if (found == 0) {
        ESP_LOGW(TAG, "  NO devices found!");
    }
}

// --- Constructor ---

Mpu6050IMU::Mpu6050IMU() : BaseIMU() {
    SetSamplePeriod(IMU_SAMPLING_TIME_MS);
    SetSampleCount(IMU_SEQUENCE_LENGTH_MAX);
}

// --- Init ---

bool Mpu6050IMU::Init() {
    // Configure I2C master
    i2c_config_t conf = {};
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = (gpio_num_t)(int)cw::board::kPinI2cSda;
    conf.scl_io_num = (gpio_num_t)(int)cw::board::kPinI2cScl;
    conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
    conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
    conf.master.clk_speed = cw::board::kI2cClockHz;
    esp_err_t ret = i2c_param_config(kI2cPort, &conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2c_param_config failed: %s", esp_err_to_name(ret));
        return false;
    }
    ret = i2c_driver_install(kI2cPort, conf.mode, 0, 0, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2c_driver_install failed: %s", esp_err_to_name(ret));
        return false;
    }

    ESP_LOGI(TAG, "I2C init OK (SDA=GPIO%d, SCL=GPIO%d, %dkHz)",
             cw::board::kPinI2cSda, cw::board::kPinI2cScl,
             cw::board::kI2cClockHz / 1000);

    // Prime I2C: simple address probe (START+addr+STOP) to wake the bus.
    // The bus scan does this before every successful WHO_AM_I read, and
    // clone chips often fail on the very first transaction without it.
    {
        i2c_cmd_handle_t probe = i2c_cmd_link_create();
        i2c_master_start(probe);
        i2c_master_write_byte(probe, (kMPU6050_ADDR << 1) | 0, true);
        i2c_master_stop(probe);
        esp_err_t probe_ret = i2c_master_cmd_begin(kI2cPort, probe, pdMS_TO_TICKS(100));
        i2c_cmd_link_delete(probe);
        if (probe_ret != ESP_OK) {
            ESP_LOGE(TAG, "No device at I2C address 0x%02X", kMPU6050_ADDR);
            return false;
        }
    }
    ESP_LOGI(TAG, "Device found at I2C address 0x%02X", kMPU6050_ADDR);

    // Read WHO_AM_I — may fail on clone chips; non-fatal, we wake the chip anyway
    uint8_t whoami = 0xFF;
    if (i2c_read_reg(REG_WHO_AM_I, &whoami)) {
        ESP_LOGI(TAG, "WHO_AM_I = 0x%02X", whoami);
    } else {
        ESP_LOGW(TAG, "WHO_AM_I read failed — clone chip? waking anyway");
    }

    // I2C bus scan (informational)
    i2c_bus_scan();

    // Wake up: THIS IS THE CRITICAL STEP. Without it the chip stays in sleep
    // mode and all motion-data reads return zero.
    if (!i2c_write_reg(REG_PWR_MGMT_1, 0x00)) {
        ESP_LOGW(TAG, "PWR_MGMT_1 write failed, continuing anyway");
    }
    vTaskDelay(pdMS_TO_TICKS(100));

    // DLPF: 44Hz bandwidth (setting 3)
    i2c_write_reg(REG_CONFIG, 0x03);

    // Accel range: ±4g (setting 1) -> 8192 LSB/g
    i2c_write_reg(REG_ACCEL_CONFIG, 0x08);

    // Gyro range: ±500dps (setting 1) -> 65.5 LSB/dps
    i2c_write_reg(REG_GYRO_CONFIG, 0x08);

    // Verify motion data (retry once on failure)
    int16_t ax, ay, az, gx, gy, gz;
    if (!i2c_read_motion6(&ax, &ay, &az, &gx, &gy, &gz)) {
        ESP_LOGW(TAG, "Motion data read failed, retrying after delay...");
        vTaskDelay(pdMS_TO_TICKS(100));
        if (!i2c_read_motion6(&ax, &ay, &az, &gx, &gy, &gz)) {
            ESP_LOGE(TAG, "Motion data read failed (2 attempts)");
            return false;
        }
    }
    ESP_LOGI(TAG, "Raw: ax=%d ay=%d az=%d gx=%d gy=%d gz=%d", ax, ay, az, gx, gy, gz);

    if (ax == 0 && ay == 0 && az == 0 && gx == 0 && gy == 0 && gz == 0) {
        ESP_LOGW(TAG, "All zeros — chip may need different init; continuing anyway");
    }

    ESP_LOGI(TAG, "MPU6050 init OK");
    i2c_ready_ = true;
    return true;
}

void Mpu6050IMU::Init(uint16_t sample_period_ms, uint16_t sample_count) {
    SetSamplePeriod(sample_period_ms);
    SetSampleCount(sample_count);
    Init();
}

// --- Sampling ---

const common::IMU* Mpu6050IMU::GetSamplData(uint16_t& sampled_count) {
    uint16_t sampled_index = 0;
    int16_t ax, ay, az, gx, gy, gz;
    if (GetStatus() != IMUStatus::kIdle) {
        while (GetStatus() != IMUStatus::kIdle) {
            SleepMs(50);
        }
    }
    StartSampl();
    memset(imus_, 0, sizeof(imus_));
    auto period = GetSamplePeriod();
    // 防止整数除法截断导致 sleep_ms 下溢: 每帧间隔必须 >= 1ms
    uint16_t frame_interval_ms = (period / GetSampleCount());
    uint16_t sleep_ms = (frame_interval_ms > IMU_SAMPLE_NEED_TIME_MS)
                        ? (frame_interval_ms - IMU_SAMPLE_NEED_TIME_MS)
                        : 1;

    ESP_LOGI(TAG, "Sampling %d frames", GetSampleCount());
    while (sampled_index < GetSampleCount()) {
        i2c_read_motion6(&ax, &ay, &az, &gx, &gy, &gz);
        imus_[sampled_index].acc.x = ax / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.y = ay / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.z = az / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].gyro.roll  = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.yaw   = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        sampled_index++;
        SleepMs(sleep_ms);
    }
    sampled_count = sampled_index;
    StopSampl();
    return imus_;
}

void Mpu6050IMU::SampleOneFrame(common::IMU& out) {
    int16_t ax, ay, az, gx, gy, gz;
    i2c_read_motion6(&ax, &ay, &az, &gx, &gy, &gz);

    out.acc.x = ax / IMU_ACC_TRANS_CONSTANT;
    out.acc.y = ay / IMU_ACC_TRANS_CONSTANT;
    out.acc.z = az / IMU_ACC_TRANS_CONSTANT;
    out.gyro.roll  = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
    out.gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
    out.gyro.yaw   = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;
}

common::IMU* Mpu6050IMU::GetContinuousBuffer(uint16_t& out_capacity) {
    out_capacity = kIMUMaxCount;
    return imus_;
}

bool Mpu6050IMU::EnableDataReadyInterrupt(uint8_t int_pin) {
    // SMPLRT_DIV = 9 -> 100Hz
    i2c_write_reg(REG_SMPLRT_DIV, cw::board::kImuSampleRateDiv);

    // INT_PIN_CFG: active high, push-pull, 50us pulse, read-clear
    i2c_write_reg(REG_INT_PIN_CFG, 0x30);

    // INT_ENABLE: data ready enabled
    i2c_write_reg(REG_INT_ENABLE, 0x01);

    // Create semaphore
    if (s_drdy_sem == nullptr) {
        s_drdy_sem = xSemaphoreCreateBinary();
        if (s_drdy_sem == nullptr) {
            ESP_LOGE(TAG, "DRDY semaphore create failed");
            return false;
        }
    }

    // Configure GPIO interrupt
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << int_pin);
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pull_up_en = GPIO_PULLUP_DISABLE;
    io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf.intr_type = GPIO_INTR_POSEDGE;
    gpio_config(&io_conf);

    gpio_install_isr_service(0);
    gpio_isr_handler_add((gpio_num_t)int_pin, drdy_isr, nullptr);

    s_int_mode_on = true;
    ESP_LOGI(TAG, "DRDY interrupt enabled on GPIO%d", int_pin);
    return true;
}

bool Mpu6050IMU::WaitForDataReady(uint32_t timeout_ms) {
    if (!s_int_mode_on || s_drdy_sem == nullptr) {
        return false;
    }
    return xSemaphoreTake(s_drdy_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

bool Mpu6050IMU::IsInterruptModeActive() const {
    return s_int_mode_on;
}

const common::IMU* Mpu6050IMU::GetSamplData(uint16_t& sampled_count, uint16_t timeout_ms) {
    const uint8_t loop_interval = 10;
    uint16_t sampled_index = 0;
    int16_t timeout_loop = timeout_ms / loop_interval;
    int16_t ax, ay, az, gx, gy, gz;
    if (GetStatus() != IMUStatus::kIdle) {
        while (GetStatus() != IMUStatus::kIdle && timeout_loop--) {
            SleepMs(loop_interval);
        }
    }
    if (timeout_loop <= 0) {
        ESP_LOGW(TAG, "GetImu timeout");
        return nullptr;
    }
    StartSampl();
    memset(imus_, 0, sizeof(imus_));

    while (sampled_index < GetSampleCount()) {
        i2c_read_motion6(&ax, &ay, &az, &gx, &gy, &gz);
        imus_[sampled_index].acc.x = ax / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.y = ay / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.z = az / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].gyro.roll  = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.yaw   = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        sampled_index++;
    }

    StopSampl();
    return imus_;
}

}
}
