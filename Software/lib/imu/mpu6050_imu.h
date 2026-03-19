#pragma once

#include "base_imu.h"
#include "I2Cdev.h"
#include "MPU6050.h"

namespace cw {
namespace imu {
#define IMU_SAMPLING_TIME_MS (1500)
#define IMU_SEQUENCE_LENGTH_MAX (150)
#define IMU_ACC_TRANS_CONSTANT (8192.0)  //+-4g
#define IMU_GYRO_TRANS_RADIAN_CONSTANT (4213.359738) 
#define IMU_SAMPLE_NEED_TIME_MS (3)     // 陀螺仪采样需要时间
//#define IMU_GYRO_TRANS_RADIAN_CONSTANT (1.0) 

class Mpu6050IMU : public BaseIMU , public base::Singleton<Mpu6050IMU>{

public:
    Mpu6050IMU();
    ~Mpu6050IMU() = default;

    /**
     * @brief 初始化IMU
     */
    void Init() override;

    void Init(uint16_t sample_period_ms, uint16_t sample_count);

    /**
     * @brief 获取采样数据
     */
    const common::IMU* GetSamplData(uint16_t& sampled_count) override;

    const common::IMU* GetSamplData(uint16_t& sampled_count, uint16_t timeout_ms);


private:
    MPU6050 mpu;
};
}
}