#include "imu_resampler.h"

#include <math.h>
#include <string.h>

namespace cw {
namespace cnn {

// 把 [in[lo], in[hi]] 之间按 t (0..1) 线性插值, 输出 IMU 6 通道
static inline void LerpFrame(const common::IMU& lo,
                             const common::IMU& hi,
                             float t,
                             common::IMU& out) {
    const float w_lo = 1.0f - t;
    out.acc.x      = w_lo * lo.acc.x      + t * hi.acc.x;
    out.acc.y      = w_lo * lo.acc.y      + t * hi.acc.y;
    out.acc.z      = w_lo * lo.acc.z      + t * hi.acc.z;
    out.gyro.roll  = w_lo * lo.gyro.roll  + t * hi.gyro.roll;
    out.gyro.pitch = w_lo * lo.gyro.pitch + t * hi.gyro.pitch;
    out.gyro.yaw   = w_lo * lo.gyro.yaw   + t * hi.gyro.yaw;
}

void ImuResampler::Resample(const common::IMU* in,
                            uint16_t in_len,
                            common::IMU* out,
                            uint16_t out_len) {
    if (out == nullptr || out_len == 0) {
        return;
    }

    // 边界 1: 输入为空 -> 输出全 0, 让 CNN 输出 kUnknown 而不是垃圾值
    if (in == nullptr || in_len == 0) {
        memset(out, 0, sizeof(common::IMU) * out_len);
        return;
    }

    // 边界 2: 输入只有 1 帧 -> 全部填充该帧 (退化为常数序列)
    if (in_len == 1) {
        for (uint16_t i = 0; i < out_len; ++i) {
            out[i] = in[0];
        }
        return;
    }

    // 边界 3: 输出只有 1 帧 -> 取首尾中点
    if (out_len == 1) {
        LerpFrame(in[0], in[in_len - 1], 0.5f, out[0]);
        return;
    }

    // 通用情况: 把 [0, in_len-1] 等距映射到 [0, out_len-1]
    //   step = (in_len - 1) / (out_len - 1)
    //   src_pos(i) = i * step
    const float step = static_cast<float>(in_len - 1) /
                       static_cast<float>(out_len - 1);

    for (uint16_t i = 0; i < out_len; ++i) {
        const float src_pos = i * step;

        // 取左右两端整数索引并夹紧到合法范围
        uint16_t lo = static_cast<uint16_t>(src_pos);
        if (lo >= in_len - 1) {
            // 边界 i == out_len - 1 时浮点累加可能恰好等于 in_len - 1
            // 直接用末帧, 避免越界
            out[i] = in[in_len - 1];
            continue;
        }
        const uint16_t hi = lo + 1;
        const float t = src_pos - static_cast<float>(lo);

        LerpFrame(in[lo], in[hi], t, out[i]);
    }
}

} // namespace cnn
} // namespace cw
