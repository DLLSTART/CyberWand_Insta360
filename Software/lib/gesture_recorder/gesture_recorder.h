#pragma once
#include <stdint.h>

// ponytail: single-file quaternion store on SPIFFS, no abstractions beyond what's needed

namespace cw {
namespace gesture {

// DMP 四元数: w,x,y,z (float)
struct Quat {
    float w, x, y, z;
};

// 录制约束
static constexpr uint16_t kMaxGestures      = 1000;
static constexpr uint16_t kMaxFramesPerGesture = 300;

/// 初始化 SPIFFS + DMP. 调一次即可.
bool RecorderInit();

/// 开始一次手势录制 (DMP 开始输出四元数)
bool RecorderStart();

/// 采集一帧 DMP 四元数. 阻塞直到 FIFO 有数据或超时.
/// @return true = 成功写入 out
bool RecorderSampleOne(Quat& out);

/// 结束本次录制, 将 buf[0..n) 追加写入 SPIFFS 文件.
/// @return true = 写入成功, false = 已满 1000 条或写入失败
bool RecorderCommit(const Quat* buf, uint16_t n);

/// 当前已录制的手势数量
uint16_t RecorderCount();

}  // namespace gesture
}  // namespace cw
