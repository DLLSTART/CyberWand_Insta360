#pragma once
#include "mpu6050_imu.h"
#include <stdint.h>
#include "base.h"
#include "common.h"
#include "esp_timer.h"

namespace cw { 
namespace imu {
Mpu6050IMU::Mpu6050IMU() : BaseIMU() {
    SetSamplePeriod(IMU_SAMPLING_TIME_MS);
    SetSampleCount(IMU_SEQUENCE_LENGTH_MAX);
}
void Mpu6050IMU::Init() {
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin(); 
    Wire.setClock(400000);
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
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