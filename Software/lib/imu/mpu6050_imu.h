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

// =============================================================================
// 连续采样模式参数 (用于 "按下到松开" 任意时长手势采样)
// -----------------------------------------------------------------------------
//  - kContinuousFramePeriodMs : 采样名义周期, 与原 1500ms/150帧 = 10ms 对齐
//                               (减去 ~3ms IMU 通信耗时, 实际 sleep ≈ 7ms)
//  - kContinuousMinFrames     : 单次手势最少帧数 (低于此值视为误触, 丢弃)
//  - kContinuousMaxFrames     : 单次手势最多帧数 (上限保护, 与 kIMUMaxCount=300 对齐)
//
// 调用方典型用法:
//   1) 按下边沿 (ButtonEvent::PressDown) 来到 -> 准备 N=0
//   2) 在 main loop 里循环:
//        Mpu6050IMU::SampleOneFrame(buf[N++])    -- 同步采一帧 (~3ms)
//        ButtonManager::GetEvent(msg, 7ms)       -- 同时等 Release 事件
//   3) 收到 Release 事件 / N 达到 kContinuousMaxFrames -> 退出循环
//   4) buf[0..N) 即为本次手势的全部 IMU 数据
// =============================================================================
constexpr uint16_t kContinuousFramePeriodMs = 10;
constexpr uint16_t kContinuousMinFrames     = 30;
constexpr uint16_t kContinuousMaxFrames     = 300;

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
     * @brief 获取采样数据 (固定 GetSampleCount() 帧, 阻塞)
     * @note  Acquisition 模式 / 训练数据制作走这条路径, 帧数固定便于训练对齐.
     */
    const common::IMU* GetSamplData(uint16_t& sampled_count) override;

    const common::IMU* GetSamplData(uint16_t& sampled_count, uint16_t timeout_ms);

    /**
     * @brief  同步采集单帧 IMU 数据 (~3ms, 不修改采样状态机).
     *
     * 设计动机: 让 "按下到松开" 模式下, main loop 可以
     *   - 自己控制采样节奏 (循环里夹一次按键事件 poll, 实现 Release 提前打断)
     *   - 自己控制总帧数 (上限由 kContinuousMaxFrames 约束)
     *   - 不引入额外 FreeRTOS task, 与原有 ButtonManager 任务模型对称
     *
     * @param  out  调用方提供的输出帧, 写入 acc.{x,y,z} 与 gyro.{roll,pitch,yaw}
     */
    void SampleOneFrame(common::IMU& out);

    /**
     * @brief  暴露内部 IMU 缓冲, 供 "连续采样" 调用方就地写入.
     * @param  out_capacity  [out] 缓冲容量 (= BaseIMU::kIMUMaxCount = 300)
     * @return 缓冲首地址; 调用方可写入 [0, out_capacity) 范围
     *
     * 复用 BaseIMU::imus_ 内部缓冲, 避免再开一个 300 * sizeof(IMU) 的栈/堆缓冲.
     * 调用方负责自身的写入边界管理.
     */
    common::IMU* GetContinuousBuffer(uint16_t& out_capacity);


private:
    MPU6050 mpu;
};
}
}