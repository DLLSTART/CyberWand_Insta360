/**
 * CyberWand - 模拟 MPU6050 传感器驱动
 * 用于 PC 端单元测试，无需真实硬件
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "mpu6050_sim.h"

// 四元数结构
typedef struct {
    float w, x, y, z;
} quaternion_t;

// 模拟姿态数据
static quaternion_t current_quat = {1, 0, 0, 0};  // 初始姿态
static imu_data_t simulated_imu = {0};

/**
 * 生成转圈动作的四元数
 * @param angle 旋转角度（度）
 */
quaternion_t generate_rotation_quaternion(float angle_deg)
{
    quaternion_t q;
    float angle_rad = angle_deg * M_PI / 180.0f;
    
    q.w = cosf(angle_rad / 2);
    q.x = 0;
    q.y = 0;
    q.z = sinf(angle_rad / 2);  // Z 轴旋转
    
    return q;
}

/**
 * 生成 V 形动作的四元数
 * @param v_angle V 形角度（度）
 */
quaternion_t generate_v_shape_quaternion(float v_angle_deg)
{
    quaternion_t q;
    float angle_rad = v_angle_deg * M_PI / 180.0f;
    
    q.w = cosf(angle_rad / 2);
    q.x = sinf(angle_rad / 2);  // X 轴倾斜
    q.y = 0;
    q.z = 0;
    
    return q;
}

/**
 * 四元数转欧拉角（加速度计模拟）
 */
void quaternion_to_accel(const quaternion_t* q, int16_t* ax, int16_t* ay, int16_t* az)
{
    // 重力加速度 1g = 16384 (MPU6050 默认量程±2g)
    const float g = 16384.0f;
    
    // 从四元数计算加速度分量
    *ax = (int16_t)(g * 2 * (q->x * q->z - q->w * q->y));
    *ay = (int16_t)(g * 2 * (q->w * q->x + q->y * q->z));
    *az = (int16_t)(g * 2 * (q->w * q->w - 0.5f + q->z * q->z));
}

/**
 * 四元数转角速度（陀螺仪模拟）
 */
void quaternion_to_gyro(const quaternion_t* q, int16_t* gx, int16_t* gy, int16_t* gz)
{
    // 假设角速度 1°/s = 131 (MPU6050 默认量程±250°/s)
    const float gyro_scale = 131.0f;
    
    // 简化模拟：假设角速度与四元数变化率成正比
    *gx = (int16_t)(q->x * 100 * gyro_scale);
    *gy = (int16_t)(q->y * 100 * gyro_scale);
    *gz = (int16_t)(q->z * 100 * gyro_scale);
}

/**
 * 初始化模拟传感器
 */
int mpu6050_sim_init(void)
{
    srand((unsigned int)time(NULL));
    current_quat.w = 1;
    current_quat.x = 0;
    current_quat.y = 0;
    current_quat.z = 0;
    
    printf("[SIM] MPU6050 initialized (simulation mode)\n");
    return 0;
}

/**
 * 读取模拟 IMU 数据
 */
int mpu6050_sim_read(imu_data_t* data)
{
    // 从当前四元数生成加速度和角速度
    quaternion_to_accel(&current_quat, &data->ax, &data->ay, &data->az);
    quaternion_to_gyro(&current_quat, &data->gx, &data->gy, &data->gz);
    
    // 添加少量噪声
    data->ax += (rand() % 100 - 50);
    data->ay += (rand() % 100 - 50);
    data->az += (rand() % 100 - 50);
    
    data->timestamp = (uint32_t)time(NULL);
    
    return 0;
}

/**
 * 设置模拟姿态（转圈动作）
 */
void mpu6050_sim_set_rotation(float angle_deg)
{
    current_quat = generate_rotation_quaternion(angle_deg);
    printf("[SIM] Set rotation: %.1f°\n", angle_deg);
}

/**
 * 设置模拟姿态（V 形动作）
 */
void mpu6050_sim_set_v_shape(float v_angle_deg)
{
    current_quat = generate_v_shape_quaternion(v_angle_deg);
    printf("[SIM] Set V-shape: %.1f°\n", v_angle_deg);
}

/**
 * 模拟连续动作序列
 */
void mpu6050_sim_action_sequence(action_sequence_t seq)
{
    switch (seq) {
        case ACTION_IDLE:
            mpu6050_sim_set_rotation(0);
            break;
        case ACTION_ROTATE_LEFT:
            mpu6050_sim_set_rotation(90);
            break;
        case ACTION_ROTATE_RIGHT:
            mpu6050_sim_set_rotation(-90);
            break;
        case ACTION_V_SHAPE_UP:
            mpu6050_sim_set_v_shape(45);
            break;
        case ACTION_V_SHAPE_DOWN:
            mpu6050_sim_set_v_shape(-45);
            break;
    }
}
