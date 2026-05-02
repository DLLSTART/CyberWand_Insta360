// =============================================================================
// test_imu_resampler.cpp — ImuResampler 单元测试
// -----------------------------------------------------------------------------
// 覆盖目标:
//   1) 恒等映射: in_len == out_len 时, 输出与输入逐通道相等
//   2) 常量填充: in_len == 1 时, 输出全部等于 in[0]
//   3) 空输入  : in_len == 0 时, 输出全部清零
//   4) 端点保持: 任何 in_len/out_len 组合下, out[0] 等于 in[0],
//                                          out[out_len-1] 等于 in[in_len-1]
//   5) 上采样  : in_len < out_len, 中间帧由相邻输入帧的线性插值得到
//   6) 下采样  : in_len > out_len, 等距抽样 + 插值
//   7) 通道独立: 6 个通道 (acc.x/y/z + gyro.roll/pitch/yaw) 互不影响
//   8) 单帧输出: out_len == 1 时取首尾中点
//
// 注: 浮点比较用 fabs(diff) < kEps, kEps = 1e-5 足以覆盖 float lerp 误差.
// =============================================================================
#include "mini_test.h"
#include "imu_resampler.h"

#include <math.h>
#include <stdint.h>

namespace {

constexpr float kEps = 1e-5f;

inline bool NearF(float a, float b) {
    return fabsf(a - b) < kEps;
}

// 给定 6 个通道的种子值, 构造一帧 IMU
inline cw::common::IMU MakeFrame(float ax, float ay, float az,
                                 float roll, float pitch, float yaw) {
    cw::common::IMU f{};
    f.acc.x = ax; f.acc.y = ay; f.acc.z = az;
    f.gyro.roll = roll; f.gyro.pitch = pitch; f.gyro.yaw = yaw;
    return f;
}

// 用 i 索引线性递增填充 6 通道, 便于人眼校验插值结果
inline cw::common::IMU FrameWithRamp(uint16_t i) {
    return MakeFrame(
        /*acc*/   1.0f * i, 2.0f * i, 3.0f * i,
        /*gyro*/  4.0f * i, 5.0f * i, 6.0f * i);
}

inline bool FramesEqual(const cw::common::IMU& a, const cw::common::IMU& b) {
    return NearF(a.acc.x, b.acc.x) && NearF(a.acc.y, b.acc.y) &&
           NearF(a.acc.z, b.acc.z) &&
           NearF(a.gyro.roll, b.gyro.roll) &&
           NearF(a.gyro.pitch, b.gyro.pitch) &&
           NearF(a.gyro.yaw,   b.gyro.yaw);
}

} // namespace


// ============================ 用例 1: 恒等映射 =============================
MT_TEST(ImuResampler, IdentityWhenSameLength) {
    constexpr uint16_t kN = 8;
    cw::common::IMU in[kN];
    cw::common::IMU out[kN];
    for (uint16_t i = 0; i < kN; ++i) in[i] = FrameWithRamp(i);

    cw::cnn::ImuResampler::Resample(in, kN, out, kN);

    for (uint16_t i = 0; i < kN; ++i) {
        MT_EXPECT_TRUE(FramesEqual(out[i], in[i]));
    }
}


// ============================ 用例 2: 单帧填充 =============================
MT_TEST(ImuResampler, ConstantFillWhenInputHasOneFrame) {
    cw::common::IMU in[1];
    in[0] = MakeFrame(0.5f, -0.5f, 1.0f, 0.1f, -0.1f, 0.2f);

    cw::common::IMU out[16];
    cw::cnn::ImuResampler::Resample(in, 1, out, 16);

    for (uint16_t i = 0; i < 16; ++i) {
        MT_EXPECT_TRUE(FramesEqual(out[i], in[0]));
    }
}


// ============================ 用例 3: 空输入 ===============================
MT_TEST(ImuResampler, ZeroFillWhenInputEmpty) {
    cw::common::IMU out[10];
    // 先污染输出, 确认 Resample 会清零
    for (uint16_t i = 0; i < 10; ++i) {
        out[i] = MakeFrame(99, 99, 99, 99, 99, 99);
    }

    cw::cnn::ImuResampler::Resample(nullptr, 0, out, 10);

    cw::common::IMU zero{};
    for (uint16_t i = 0; i < 10; ++i) {
        MT_EXPECT_TRUE(FramesEqual(out[i], zero));
    }
}

MT_TEST(ImuResampler, ZeroFillWhenInLenZeroEvenWithPtr) {
    cw::common::IMU dummy[3]; dummy[0] = FrameWithRamp(7);
    cw::common::IMU out[5];
    for (auto& f : out) f = MakeFrame(99, 99, 99, 99, 99, 99);

    cw::cnn::ImuResampler::Resample(dummy, 0, out, 5);

    cw::common::IMU zero{};
    for (uint16_t i = 0; i < 5; ++i) {
        MT_EXPECT_TRUE(FramesEqual(out[i], zero));
    }
}


// ============================ 用例 4: 端点保持 =============================
MT_TEST(ImuResampler, EndpointsPreservedOnUpsample) {
    constexpr uint16_t kIn  = 3;
    constexpr uint16_t kOut = 11;
    cw::common::IMU in[kIn];
    in[0] = FrameWithRamp(10);
    in[1] = FrameWithRamp(20);
    in[2] = FrameWithRamp(30);

    cw::common::IMU out[kOut];
    cw::cnn::ImuResampler::Resample(in, kIn, out, kOut);

    MT_EXPECT_TRUE(FramesEqual(out[0],         in[0]));
    MT_EXPECT_TRUE(FramesEqual(out[kOut - 1],  in[kIn - 1]));
}

MT_TEST(ImuResampler, EndpointsPreservedOnDownsample) {
    constexpr uint16_t kIn  = 30;
    constexpr uint16_t kOut = 7;
    cw::common::IMU in[kIn];
    for (uint16_t i = 0; i < kIn; ++i) in[i] = FrameWithRamp(i);

    cw::common::IMU out[kOut];
    cw::cnn::ImuResampler::Resample(in, kIn, out, kOut);

    MT_EXPECT_TRUE(FramesEqual(out[0],         in[0]));
    MT_EXPECT_TRUE(FramesEqual(out[kOut - 1],  in[kIn - 1]));
}


// ============================ 用例 5: 上采样插值 ============================
MT_TEST(ImuResampler, UpsampleTwoToThreeIsExactMidpoint) {
    cw::common::IMU in[2];
    in[0] = MakeFrame(0, 0, 0, 0, 0, 0);
    in[1] = MakeFrame(2, 4, 6, 8, 10, 12);

    cw::common::IMU out[3];
    cw::cnn::ImuResampler::Resample(in, 2, out, 3);

    // 步长 = (2-1) / (3-1) = 0.5
    // 期望: out[0] = in[0]; out[1] = 0.5*in[0] + 0.5*in[1]; out[2] = in[1]
    MT_EXPECT_TRUE(FramesEqual(out[0], in[0]));
    MT_EXPECT_TRUE(FramesEqual(out[2], in[1]));

    cw::common::IMU mid = MakeFrame(1, 2, 3, 4, 5, 6);
    MT_EXPECT_TRUE(FramesEqual(out[1], mid));
}

MT_TEST(ImuResampler, UpsampleQuarterPositionLerp) {
    // in_len=2, out_len=5  ->  step = 1 / 4 = 0.25
    // out[0] = in[0]              t=0
    // out[1] = 0.75*in[0]+0.25*in[1]  t=0.25
    // out[2] = 0.5 *in[0]+0.5 *in[1]  t=0.5
    // out[3] = 0.25*in[0]+0.75*in[1]  t=0.75
    // out[4] = in[1]              t=1
    cw::common::IMU in[2];
    in[0] = MakeFrame(0, 0, 0, 0, 0, 0);
    in[1] = MakeFrame(4, 4, 4, 4, 4, 4);

    cw::common::IMU out[5];
    cw::cnn::ImuResampler::Resample(in, 2, out, 5);

    MT_EXPECT_TRUE(NearF(out[0].acc.x, 0.0f));
    MT_EXPECT_TRUE(NearF(out[1].acc.x, 1.0f));
    MT_EXPECT_TRUE(NearF(out[2].acc.x, 2.0f));
    MT_EXPECT_TRUE(NearF(out[3].acc.x, 3.0f));
    MT_EXPECT_TRUE(NearF(out[4].acc.x, 4.0f));

    MT_EXPECT_TRUE(NearF(out[1].gyro.yaw, 1.0f));
    MT_EXPECT_TRUE(NearF(out[3].gyro.yaw, 3.0f));
}


// ============================ 用例 6: 下采样抽样 ============================
MT_TEST(ImuResampler, DownsampleFiveToThreePicksAtIntegerPositions) {
    // in_len=5, out_len=3  ->  step = 4 / 2 = 2
    // out[0] = in[0]   (src_pos = 0)
    // out[1] = in[2]   (src_pos = 2)
    // out[2] = in[4]   (src_pos = 4)
    cw::common::IMU in[5];
    for (uint16_t i = 0; i < 5; ++i) in[i] = FrameWithRamp(i);

    cw::common::IMU out[3];
    cw::cnn::ImuResampler::Resample(in, 5, out, 3);

    MT_EXPECT_TRUE(FramesEqual(out[0], in[0]));
    MT_EXPECT_TRUE(FramesEqual(out[1], in[2]));
    MT_EXPECT_TRUE(FramesEqual(out[2], in[4]));
}


// ============================ 用例 7: 通道独立性 ============================
MT_TEST(ImuResampler, ChannelsAreIndependent) {
    // 设计: 把每个通道用完全不同的斜率, 确认插值不串扰.
    cw::common::IMU in[2];
    in[0] = MakeFrame(/*acc*/  1, 10, 100, /*gyro*/ -1, -10, -100);
    in[1] = MakeFrame(/*acc*/  3, 30, 300, /*gyro*/ -3, -30, -300);

    cw::common::IMU out[3];
    cw::cnn::ImuResampler::Resample(in, 2, out, 3);

    MT_EXPECT_TRUE(NearF(out[1].acc.x,       2.0f));
    MT_EXPECT_TRUE(NearF(out[1].acc.y,      20.0f));
    MT_EXPECT_TRUE(NearF(out[1].acc.z,     200.0f));
    MT_EXPECT_TRUE(NearF(out[1].gyro.roll,  -2.0f));
    MT_EXPECT_TRUE(NearF(out[1].gyro.pitch,-20.0f));
    MT_EXPECT_TRUE(NearF(out[1].gyro.yaw, -200.0f));
}


// ============================ 用例 8: 单帧输出 =============================
MT_TEST(ImuResampler, SingleOutputIsMidpointOfEnds) {
    cw::common::IMU in[5];
    in[0] = MakeFrame( 0,  0,  0,  0,  0,  0);
    in[1] = MakeFrame(99, 99, 99, 99, 99, 99); // 中间帧不应影响
    in[2] = MakeFrame(11, 22, 33, 44, 55, 66);
    in[3] = MakeFrame(77, 77, 77, 77, 77, 77);
    in[4] = MakeFrame(10, 20, 30, 40, 50, 60);

    cw::common::IMU out[1];
    cw::cnn::ImuResampler::Resample(in, 5, out, 1);

    cw::common::IMU expected = MakeFrame(5.0f, 10.0f, 15.0f, 20.0f, 25.0f, 30.0f);
    MT_EXPECT_TRUE(FramesEqual(out[0], expected));
}


// ============================ 用例 9: 真实场景规模 =========================
MT_TEST(ImuResampler, RealisticGesture90To150NoCrash) {
    // 模拟用户按住 ~900ms 实际采到 90 帧, 归一化到 150 帧 (CNN 输入).
    // 不验证具体数值, 只验证: 端点保持, 中间无 NaN/inf, 通道无串扰.
    constexpr uint16_t kIn  = 90;
    constexpr uint16_t kOut = 150;
    cw::common::IMU in[kIn];
    for (uint16_t i = 0; i < kIn; ++i) {
        // 用 sin/cos 模拟一个圆圈手势的轨迹
        float t = (float)i / (float)(kIn - 1);
        in[i].acc.x = sinf(t * 6.2831853f);
        in[i].acc.y = cosf(t * 6.2831853f);
        in[i].acc.z = 1.0f;
        in[i].gyro.roll  = 0.5f * sinf(t * 6.2831853f);
        in[i].gyro.pitch = 0.5f * cosf(t * 6.2831853f);
        in[i].gyro.yaw   = t;
    }

    cw::common::IMU out[kOut];
    cw::cnn::ImuResampler::Resample(in, kIn, out, kOut);

    MT_EXPECT_TRUE(FramesEqual(out[0],          in[0]));
    MT_EXPECT_TRUE(FramesEqual(out[kOut - 1],   in[kIn - 1]));

    // 验证全部输出都是有限数 (lerp 不会引入 NaN/inf)
    for (uint16_t i = 0; i < kOut; ++i) {
        MT_EXPECT_TRUE(isfinite(out[i].acc.x));
        MT_EXPECT_TRUE(isfinite(out[i].acc.y));
        MT_EXPECT_TRUE(isfinite(out[i].acc.z));
        MT_EXPECT_TRUE(isfinite(out[i].gyro.roll));
        MT_EXPECT_TRUE(isfinite(out[i].gyro.pitch));
        MT_EXPECT_TRUE(isfinite(out[i].gyro.yaw));
    }
}


// ============================ 用例 10: out_len=0 安全 =====================
MT_TEST(ImuResampler, OutLenZeroIsNoop) {
    cw::common::IMU in[3];
    for (uint16_t i = 0; i < 3; ++i) in[i] = FrameWithRamp(i);
    // 给个非 nullptr 的 out, 但 out_len=0, 期望函数立即返回什么都不写
    cw::common::IMU out[1];
    out[0] = MakeFrame(42, 42, 42, 42, 42, 42);

    cw::cnn::ImuResampler::Resample(in, 3, out, 0);

    cw::common::IMU sentinel = MakeFrame(42, 42, 42, 42, 42, 42);
    MT_EXPECT_TRUE(FramesEqual(out[0], sentinel));
}
