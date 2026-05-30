#pragma once
#include <Arduino.h>
#include "base.h"
#include "common.h"
#include <stdint.h>

namespace cw {
namespace imu {

enum class IMUStatus {
    kIdle = 0,
    kSampling = 1,
    kSampled = 2,
};

class BaseIMU {

public:
    BaseIMU() = default;
    ~BaseIMU() = default;

    /**
     * @brief 初始化IMU
     * @return true = 初始化成功; false = 硬件不可达
     */
    virtual bool Init() = 0;

    /**
     * @brief 获取采样数据
     */
    virtual const common::IMU* GetSamplData(uint16_t& sampled_count) = 0;

    /**
     * @brief 处理数据结束
     */
    void Commit();
protected:
    /**
     * @brief 开始采样
     */
    void StartSampl();

    /**
     * @brief 停止采样
     */
    void StopSampl();

    /**
     * @brief 获取IMU状态
     * @return IMU状态
     */
    IMUStatus GetStatus();

    /**
     * @brief 设置采样周期
     * @param period 采样周期
     */
    void SetSamplePeriod(uint16_t period_ms);

     /**
     * @brief 获取当前采样周期
     * @return 当前采样周期
     */
    uint16_t GetSamplePeriod();

    /**
     * @brief 获取采样数量
     * @return 采样数量
     */
    uint16_t GetSampleCount();      

    /**
     * @brief 设置采样数量
     * @param count 采样数量
     */
    void SetSampleCount(uint16_t count);

    static const int kIMUMaxCount = 300;
    common::IMU imus_[kIMUMaxCount];

private:
    IMUStatus status_ = IMUStatus::kIdle;
    uint16_t sampled_count = 0;             // 已经采样的数量
    uint16_t cur_used_count_ = 150;           // 周期内采样数量
    uint16_t cur_sample_period_;        // 当前采样周期, 单位ms


    cw::base::Mutex imu_lock = xSemaphoreCreateMutex();
};
}
}