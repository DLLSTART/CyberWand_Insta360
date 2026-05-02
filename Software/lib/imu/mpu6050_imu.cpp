#pragma once
#include "mpu6050_imu.h"
#include <stdint.h>
#include "base.h"
#include "common.h"
#include "esp_timer.h"
#include "board_config.h"   // kPinI2cSda / kPinI2cScl / kI2cClockHz

namespace cw { 
namespace imu {
Mpu6050IMU::Mpu6050IMU() : BaseIMU() {
    SetSamplePeriod(IMU_SAMPLING_TIME_MS);
    SetSampleCount(IMU_SEQUENCE_LENGTH_MAX);
}
void Mpu6050IMU::Init() {
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    // ESP32-S3 默认 Wire 引脚不一定是 IO8/IO9, 必须显式指定原理图里实际接 IMU 的引脚.
    // 否则 begin() 用的是默认 IO, scanner 可能完全看不到 0x68.
    Wire.begin(cw::board::kPinI2cSda, cw::board::kPinI2cScl);
    Wire.setClock(cw::board::kI2cClockHz);
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(static_cast<uint16_t>(cw::board::kI2cClockHz / 1000), true);
    #endif

    mpu.initialize();
    if(mpu.testConnection() ==  false){
        ILOGN("MPU6050 connection failed");
        while(true);
    } else{
        Serial.println("MPU6050 connection successful");
    }

    // mpu.setXAccelOffset(0); //Set your accelerometer offset for axis X
    // mpu.setYAccelOffset(0); //Set your accelerometer offset for axis Y
    // mpu.setZAccelOffset(0); //Set your accelerometer offset for axis Z
    // mpu.setXGyroOffset(0);  //Set your gyro offset for axis X
    // mpu.setYGyroOffset(0);  //Set your gyro offset for axis Y
    // mpu.setZGyroOffset(0);  //Set your gyro offset for axis Z

    // 1. 临时将加速度计设为默认的 ±2g 量程，迎合校准函数的胃口
    // mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2); 
    
    // 2. 确保此时传感器绝对平放、静止，并且芯片正面朝上！然后执行校准
    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);
    
    // 3. 校准完成后，切回你项目需要的 ±4g 量程
    // mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
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

        #ifndef defined(CY_DEBUG)
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