#pragma once

#include "base_imu.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

namespace cw {
namespace imu {
#define IMU_SAMPLING_TIME_MS (1500)
#define IMU_SEQUENCE_LENGTH_MAX (150)
#define IMU_ACC_TRANS_CONSTANT (8192.0)  // +-4g
#define IMU_GYRO_TRANS_RADIAN_CONSTANT (4213.359738)
#define IMU_SAMPLE_NEED_TIME_MS (3)

constexpr uint16_t kContinuousFramePeriodMs = 10;
constexpr uint16_t kContinuousMinFrames     = 30;
constexpr uint16_t kContinuousMaxFrames     = 300;

class Mpu6050IMU : public BaseIMU , public base::Singleton<Mpu6050IMU>{

public:
    Mpu6050IMU();
    ~Mpu6050IMU() = default;

    bool Init() override;
    void Init(uint16_t sample_period_ms, uint16_t sample_count);

    bool IsI2cReady() const { return i2c_ready_; }

    const common::IMU* GetSamplData(uint16_t& sampled_count) override;
    const common::IMU* GetSamplData(uint16_t& sampled_count, uint16_t timeout_ms);

    void SampleOneFrame(common::IMU& out);

    common::IMU* GetContinuousBuffer(uint16_t& out_capacity);

    bool EnableDataReadyInterrupt(uint8_t int_pin);
    bool WaitForDataReady(uint32_t timeout_ms);
    bool IsInterruptModeActive() const;


private:
    bool i2c_ready_ = false;
};
}
}
