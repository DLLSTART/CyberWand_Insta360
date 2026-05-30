#pragma once

#include "base_imu.h"
#include "I2Cdev.h"
#include "MPU6050.h"

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

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
     * @return true = I2C 连接成功; false = MPU6050 不可达 (I2C 扫描无设备 / whoami 失败)
     */
    bool Init() override;

    void Init(uint16_t sample_period_ms, uint16_t sample_count);

    /** @brief 查询 I2C 总线是否已成功初始化 (供 main 自检使用) */
    bool IsI2cReady() const { return i2c_ready_; }

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

    /**
     * @brief  启用 IMU DRDY (数据就绪) 中断驱动模式.
     *
     * 配置链:
     *   1) IMU 侧: SMPLRT_DIV = kImuSampleRateDiv (100Hz);
     *              INT 引脚 active high / 推挽 / 50us 脉冲 / 任意读清除;
     *              使能 DATA_RDY 中断
     *   2) ESP32 侧: 创建二值信号量 + attachInterrupt(int_pin, ISR, RISING)
     *
     * 调用方典型流程: Init() -> EnableDataReadyInterrupt(kPinImuInt)
     *                 然后用 WaitForDataReady() 阻塞等中断, 替代固定 vTaskDelay
     *
     * @param  int_pin  ESP32 端连接 IMU INT 的 GPIO 编号 (= cw::board::kPinImuInt)
     * @return true = 配置成功; false = 信号量创建失败 (极少见)
     *
     * ⚠️ R5 风险: 如果 IMU pin 11 实际是 FSYNC (输入) 而不是 INT (输出),
     *              ISR 永远不会被触发. WaitForDataReady() 会持续超时,
     *              调用方应在超时时切到固定周期 vTaskDelay 兜底, 见 main.cpp.
     */
    bool EnableDataReadyInterrupt(uint8_t int_pin);

    /**
     * @brief  阻塞等待一帧 DRDY 中断到来.
     *
     * @param  timeout_ms  最长等待时间; 推荐 = cw::board::kImuIntWaitMs (15ms)
     * @return true  = 在超时前收到中断 (= IMU 有新数据可读)
     *         false = 中断未到 / 中断未启用 — 调用方应当启动兜底机制
     *
     * 必须先调过 EnableDataReadyInterrupt() 才有效, 否则总是返回 false.
     */
    bool WaitForDataReady(uint32_t timeout_ms);

    /**
     * @brief  查询当前是否处于中断驱动模式.
     * @return true = EnableDataReadyInterrupt() 已成功调用; false = 仅轮询
     */
    bool IsInterruptModeActive() const;


private:
    MPU6050 mpu;
    bool i2c_ready_ = false;
};
}
}