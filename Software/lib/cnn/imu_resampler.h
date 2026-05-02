#pragma once

#include <stdint.h>
#include "common.h"

namespace cw {
namespace cnn {

/**
 * @brief  IMU 序列长度归一化器 (任意 N 帧 -> 固定 M 帧, 线性插值).
 *
 * 设计动机:
 *   "按下到松开" 模式下, 用户挥舞手势时长可变 (30 ~ 300 帧), 而 nnom CNN
 *   模型的输入张量形状是训练时固化的 (默认 150 帧 x 6 通道). 直接把可变
 *   长度送进 PredictBlock 会让超出 N 的部分残留旧数据, 推理结果不可信.
 *
 *   本类提供一个纯函数 Resample, 把 in_len 帧的 IMU 序列等比映射到 out_len
 *   帧, 中间帧用左右两端的线性插值合成. 这种做法能保留手势整体形态
 *   (起手 / 转折 / 收手), 比 "居中裁剪" 或 "末端 padding" 对短/长手势都更友好.
 *
 * 算法:
 *   for i in [0, out_len):
 *       src_pos = i * (in_len - 1) / (out_len - 1)        // 浮点
 *       lo = floor(src_pos), hi = ceil(src_pos), t = src_pos - lo
 *       out[i] = (1 - t) * in[lo] + t * in[hi]            // 6 个通道分别插值
 *
 * 边界:
 *   - in_len == 0     : 直接清零 out
 *   - in_len == 1     : out 全部填充 in[0]
 *   - in_len >= out_len: 退化为下采样 (仍是线性插值, 不抗混叠 -- 手势频谱较低, 可接受)
 *   - in_len < out_len : 上采样 (线性插值放大)
 *
 * 性能:
 *   纯定点 + 浮点乘加, 无动态分配, 150 * 6 ≈ 900 次 lerp, 微秒级开销.
 *
 * 可单元测试: 无任何 Arduino / FreeRTOS 依赖, 仅用 stdint + common::IMU.
 */
class ImuResampler {
public:
    /**
     * @brief  把 in[0..in_len) 线性插值到 out[0..out_len).
     * @param  in       输入序列 (任意长度)
     * @param  in_len   输入有效帧数
     * @param  out      调用方提供的输出缓冲, 必须能容纳 out_len 帧
     * @param  out_len  期望输出帧数 (通常 = 150 = CNN 输入帧数)
     */
    static void Resample(const common::IMU* in,
                         uint16_t in_len,
                         common::IMU* out,
                         uint16_t out_len);
};

} // namespace cnn
} // namespace cw
