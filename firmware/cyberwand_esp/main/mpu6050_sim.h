/**
 * CyberWand - 模拟 MPU6050 传感器头文件
 */

#ifndef MPU6050_SIM_H
#define MPU6050_SIM_H

#include <stdint.h>

// IMU 数据结构
typedef struct {
    int16_t ax, ay, az;     // 加速度计
    int16_t gx, gy, gz;     // 陀螺仪
    uint32_t timestamp;     // 时间戳
} imu_data_t;

// 四元数结构
typedef struct {
    float w, x, y, z;
} quaternion_t;

// 动作序列枚举
typedef enum {
    ACTION_IDLE = 0,
    ACTION_ROTATE_LEFT,
    ACTION_ROTATE_RIGHT,
    ACTION_V_SHAPE_UP,
    ACTION_V_SHAPE_DOWN
} action_sequence_t;

// 函数声明
int mpu6050_sim_init(void);
int mpu6050_sim_read(imu_data_t* data);
void mpu6050_sim_set_rotation(float angle_deg);
void mpu6050_sim_set_v_shape(float v_angle_deg);
void mpu6050_sim_action_sequence(action_sequence_t seq);

// 四元数生成函数
quaternion_t generate_rotation_quaternion(float angle_deg);
quaternion_t generate_v_shape_quaternion(float v_angle_deg);

// 四元数转换函数
void quaternion_to_accel(const quaternion_t* q, int16_t* ax, int16_t* ay, int16_t* az);
void quaternion_to_gyro(const quaternion_t* q, int16_t* gx, int16_t* gy, int16_t* gz);

#endif // MPU6050_SIM_H
