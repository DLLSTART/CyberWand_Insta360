#include "base_imu.h"

namespace cw {
namespace imu {

void BaseIMU::StartSampl() {
    cw::base::AutoMutex lock(imu_lock);
    status_ = IMUStatus::kSampling;
}

void BaseIMU::StopSampl() {
    cw::base::AutoMutex lock(imu_lock);
    status_ = IMUStatus::kSampled;
}

IMUStatus BaseIMU::GetStatus() {
    cw::base::AutoMutex lock(imu_lock);
    return status_;
}

void BaseIMU::SetSamplePeriod(uint16_t period_ms) {
    cur_sample_period_ = period_ms;
}

uint16_t BaseIMU::GetSamplePeriod() {
    return cur_sample_period_;
}

uint16_t BaseIMU::GetSampleCount() {
    return cur_used_count_;
}


void BaseIMU::SetSampleCount(uint16_t count) {
    cur_used_count_ = count;
}

void BaseIMU::Commit() {
    cw::base::AutoMutex lock(imu_lock);
    status_ = IMUStatus::kIdle;
}

}
}