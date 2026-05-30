#pragma once
#include <string.h>
#include "base.h"
#include "common.h"
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

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

    virtual bool Init() = 0;

    virtual const common::IMU* GetSamplData(uint16_t& sampled_count) = 0;

    void Commit();
protected:
    void StartSampl();
    void StopSampl();

    IMUStatus GetStatus();

    void SetSamplePeriod(uint16_t period_ms);
    uint16_t GetSamplePeriod();

    uint16_t GetSampleCount();
    void SetSampleCount(uint16_t count);

    static const int kIMUMaxCount = 300;
    common::IMU imus_[kIMUMaxCount];

private:
    IMUStatus status_ = IMUStatus::kIdle;
    uint16_t sampled_count = 0;
    uint16_t cur_used_count_ = 150;
    uint16_t cur_sample_period_;

    cw::base::Mutex imu_lock = xSemaphoreCreateMutex();
};
}
}
