#include "mpu6050_imu.h"
#include <stdint.h>
#include "base.h"
#include "common.h"
#include "esp_timer.h"
#include "board_config.h"   // kPinI2cSda / kPinI2cScl / kI2cClockHz / kImuSampleRateDiv

namespace cw { 
namespace imu {

// =============================================================================
// IMU DRDY 中断驱动: 模块内私有状态
// -----------------------------------------------------------------------------
// 信号量在 ISR 里 give, 在业务任务里 take. 文件局部的 static + 单例的 IMU
// 保证全局只有一个 ISR 一个 taker, 不会出现多消费者竞争.
// IRAM_ATTR 是 ESP32 必须的属性: 中断处理代码必须放在 IRAM, 否则 cache miss
// 时 (尤其 N16R8 启用 PSRAM 后频繁 cache 操作) 会让 ISR 严重抖动甚至死锁.
// =============================================================================
static SemaphoreHandle_t s_drdy_sem      = nullptr;
static volatile bool     s_int_mode_on   = false;

static void IRAM_ATTR drdy_isr(void) {
    BaseType_t hpw = pdFALSE;
    if (s_drdy_sem != nullptr) {
        xSemaphoreGiveFromISR(s_drdy_sem, &hpw);
    }
    if (hpw == pdTRUE) {
        portYIELD_FROM_ISR();
    }
}
Mpu6050IMU::Mpu6050IMU() : BaseIMU() {
    SetSamplePeriod(IMU_SAMPLING_TIME_MS);
    SetSampleCount(IMU_SEQUENCE_LENGTH_MAX);
}
bool Mpu6050IMU::Init() {
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    // 幂等: 如果 Wire 已被外部 (main 自检 / I2C scanner) 初始化, 跳过重复 begin.
    if (!i2c_ready_) {
        Wire.begin(cw::board::kPinI2cSda, cw::board::kPinI2cScl);
        Wire.setClock(cw::board::kI2cClockHz);
    }
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(static_cast<uint16_t>(cw::board::kI2cClockHz / 1000), true);
    #endif

    mpu.initialize();
    if (mpu.testConnection() == false) {
        Serial.println("[imu] MPU6050 connection FAILED (check wiring: SDA/SCL/pullup)");
        return false;
    }
    Serial.println("[imu] MPU6050 connection OK");

    i2c_ready_ = true;

    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);

    return true;
}

void Mpu6050IMU::Init(uint16_t sample_period_ms, uint16_t sample_count) {
    SetSamplePeriod(sample_period_ms);
    SetSampleCount(sample_count);
    Init();
}



const common::IMU* Mpu6050IMU::GetSamplData(uint16_t& sampled_count) {
    uint16_t sampled_index = 0;
    int16_t ax, ay, az;
    int16_t gx, gy, gz;
    if (GetStatus() != IMUStatus::kIdle) {
        while(GetStatus() != IMUStatus::kIdle) {
            SleepMs(50);
        }
    }
    StartSampl();
    memset(imus_,0,sizeof(imus_));
    auto period = GetSamplePeriod();
    uint16_t sleep_ms = (period / GetSampleCount()) - IMU_SAMPLE_NEED_TIME_MS;

    int64_t start_time_ms = esp_timer_get_time() / 1000;

    ILOGN("Sampleing");
    while (sampled_index < GetSampleCount()) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        imus_[sampled_index].acc.x = ax / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.y = ay / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.z = az / IMU_ACC_TRANS_CONSTANT;

        imus_[sampled_index].gyro.roll = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.yaw = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;

        // #if defined(CY_DEBUG)
        // ILOGT("[%d] %f",sampled_index, imus_[sampled_index].acc.x); ILOGT("\t");
            ILOGT("%f",imus_[sampled_index].acc.x); ILOGT("\t");
            ILOGT("%f",imus_[sampled_index].acc.y); ILOGT("\t");
            ILOGT("%f",imus_[sampled_index].acc.z); ILOGT("\t");
            ILOGT("%f",imus_[sampled_index].gyro.roll); ILOGT("\t");
            ILOGT("%f",imus_[sampled_index].gyro.pitch); ILOGT("\t");
            ILOGT("%f\n",imus_[sampled_index].gyro.yaw);
        // #endif

        sampled_index++;
        SleepMs(sleep_ms);
    }
    sampled_count = sampled_index;

    int64_t end_time_ms = esp_timer_get_time() / 1000;
    // ILOGT("period: %ld ms\n", end_time_ms - start_time_ms);

    StopSampl();
    return imus_;
}

// -----------------------------------------------------------------------------
// SampleOneFrame: 同步采一帧 IMU (~3ms), 用于 "按下到松开" 连续采样路径.
//   - 不操作 status_, 不持锁, 调用方自己保证不与 GetSamplData 并发
//   - 单位换算与 GetSamplData 完全一致 (acc 除以 8192.0, gyro 除以 4213.359738)
// -----------------------------------------------------------------------------
void Mpu6050IMU::SampleOneFrame(common::IMU& out) {
    int16_t ax, ay, az;
    int16_t gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    out.acc.x = ax / IMU_ACC_TRANS_CONSTANT;
    out.acc.y = ay / IMU_ACC_TRANS_CONSTANT;
    out.acc.z = az / IMU_ACC_TRANS_CONSTANT;

    out.gyro.roll  = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
    out.gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
    out.gyro.yaw   = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;
}

// -----------------------------------------------------------------------------
// GetContinuousBuffer: 暴露 BaseIMU 内部 imus_ 缓冲首地址与容量.
//   - 调用方在 PressDown 收到时获取 buf, 然后循环 SampleOneFrame(buf[i++])
//   - 容量上限由 kIMUMaxCount = 300 决定, 与 kContinuousMaxFrames 对齐
// -----------------------------------------------------------------------------
common::IMU* Mpu6050IMU::GetContinuousBuffer(uint16_t& out_capacity) {
    out_capacity = kIMUMaxCount;
    return imus_;
}

// -----------------------------------------------------------------------------
// EnableDataReadyInterrupt: 一次性配置 "IMU 端寄存器 + ESP32 端中断挂载",
//   让业务侧的 SampleOneFrame 可以由硬件触发驱动, 而不是固定 vTaskDelay 轮询.
// 时序:
//   IMU 内部 -> 100Hz 数据就绪 -> INT 引脚 50us 高脉冲 -> ESP32 GPIO RISING
//   -> drdy_isr -> xSemaphoreGiveFromISR -> 业务任务 WaitForDataReady 返回
// -----------------------------------------------------------------------------
bool Mpu6050IMU::EnableDataReadyInterrupt(uint8_t int_pin) {
    // 1) IMU 寄存器配置
    mpu.setRate(cw::board::kImuSampleRateDiv);  // SMPLRT_DIV = 9 -> 100Hz
    mpu.setInterruptMode(false);                // INT_LEVEL = 0 -> active high
    mpu.setInterruptDrive(false);               // INT_OPEN  = 0 -> push-pull
    mpu.setInterruptLatch(false);               // LATCH_INT_EN = 0 -> 50us pulse
    mpu.setInterruptLatchClear(true);           // INT_RD_CLEAR = 1 -> 任意状态读清除
    mpu.setIntDataReadyEnabled(true);           // DATA_RDY_EN = 1

    // 2) 创建二值信号量 (lazy init, 重复调用安全)
    if (s_drdy_sem == nullptr) {
        s_drdy_sem = xSemaphoreCreateBinary();
        if (s_drdy_sem == nullptr) {
            ILOGN("[imu] DRDY semaphore create failed");
            return false;
        }
    }

    // 3) 挂 ESP32 GPIO 中断
    //    INPUT (不内部上拉): IMU 是 push-pull 强驱动, 内部上拉只会拖累边沿斜率.
    pinMode(int_pin, INPUT);
    attachInterrupt(int_pin, drdy_isr, RISING);

    s_int_mode_on = true;
    ILOGN("[imu] DRDY interrupt enabled");
    return true;
}

// -----------------------------------------------------------------------------
// WaitForDataReady: 阻塞等待一次 DRDY 中断. 该函数把 CPU 完全让出,
//   FreeRTOS 调度器在等待期间会运行 BLE / button / LED 等其他任务.
//   - 中断未启用 -> 直接 false (调用方自然走轮询路径)
//   - 中断启用但 timeout 内没来 -> false (R5 风险触发, 调用方应该日志告警)
// -----------------------------------------------------------------------------
bool Mpu6050IMU::WaitForDataReady(uint32_t timeout_ms) {
    if (!s_int_mode_on || s_drdy_sem == nullptr) {
        return false;
    }
    return xSemaphoreTake(s_drdy_sem, pdMS_TO_TICKS(timeout_ms)) == pdTRUE;
}

bool Mpu6050IMU::IsInterruptModeActive() const {
    return s_int_mode_on;
}

const common::IMU* Mpu6050IMU::GetSamplData(uint16_t& sampled_count ,uint16_t timeout_ms) {
    const uint8_t loop_interval = 10;
    uint16_t sampled_index = 0;
    int16_t timeout_loop = timeout_ms / loop_interval;
    int16_t ax, ay, az;
    int16_t gx, gy, gz;
    if (GetStatus() != IMUStatus::kIdle) {
        while(GetStatus() != IMUStatus::kIdle && timeout_loop--) {
            SleepMs(loop_interval);
        }
    }
    if(timeout_loop <= 0) {
        ILOGN("GetImu Timeout");
        return nullptr;
    }
    StartSampl();
    memset(imus_,0,sizeof(imus_));

    while (sampled_index < GetSampleCount()) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        imus_[sampled_index].acc.x = ax / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.y = ay / IMU_ACC_TRANS_CONSTANT;
        imus_[sampled_index].acc.z = az / IMU_ACC_TRANS_CONSTANT;

        imus_[sampled_index].gyro.roll = gx / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.pitch = gy / IMU_GYRO_TRANS_RADIAN_CONSTANT;
        imus_[sampled_index].gyro.yaw = gz / IMU_GYRO_TRANS_RADIAN_CONSTANT;

        // 修正笔误: 原 "#ifndef defined(CY_DEBUG)" 是错的 - #ifndef 后只能跟
        // 标识符, defined() 只能用在 #if. 编译器把 "defined" 当成未定义的宏 ->
        // 整段 #ifndef 永远为真, 导致 release 模式每帧也在打 6 次 Serial.printf,
        // 直接抵消 IMU 中断驱动节能 (100Hz x 6 prints/帧 ~= 60ms/秒 阻塞串口).
        // 现在改为 #ifdef CY_DEBUG: release 不打, 想看数据时去 common.h 取消注释.
        #ifdef CY_DEBUG
        ILOGT("a/g:\t");
        ILOGT("%f",imus_[sampled_index].acc.x); ILOGT("\t");
        ILOGT("%f",imus_[sampled_index].acc.y); ILOGT("\t");
        ILOGT("%f",imus_[sampled_index].acc.z); ILOGT("\t");
        ILOGT("%f",imus_[sampled_index].gyro.roll); ILOGT("\t");
        ILOGT("%f",imus_[sampled_index].gyro.pitch); ILOGT("\t");
        ILOGT("%f\n",imus_[sampled_index].gyro.yaw);
        #endif

        sampled_index++;
    }

    StopSampl();
    return imus_;
}

}
}