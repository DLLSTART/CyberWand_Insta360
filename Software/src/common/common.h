#pragma once

// #define CY_DEBUG
#define ENUM_TO_STRING(ENUM) #ENUM

namespace cw {
namespace common {
struct Acc {
    float x;
    float y;
    float z;
};

struct Gyro {
    float roll;
    float pitch;
    float yaw;
};

class IMU {
public:
    IMU() = default;
    ~IMU() = default;
    Acc acc;
    Gyro gyro;
};
}
}
