#pragma once
#include "nnom.h"
// weights.h 由 CNNTrainRaw.py 训练 pipeline 自动生成, 里面把 string literal
// 直接赋给 nnom 的 char* name 字段, GCC -Wwrite-strings 会报 14 条警告.
// 不能手改 weights.h (重新训练会被覆盖), 在包含位置局部抑制即可.
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wwrite-strings"
#include "weights.h"
#pragma GCC diagnostic pop
#include "common.h"
#include "base.h"

namespace cw {
namespace cnn {

typedef int8_t ModelOutput;

enum class ActionType : uint8_t {
    kCircle_Cw = 0,
    kCircle_Aw = 1,
    kCheck = 2,
    kCross_Left = 3,
    kCross_Right = 4,
    kUnknown = 5,

    kMax,
};

class ActionRecognitionCNN : public cw::base::Singleton<ActionRecognitionCNN> {
public:
    ActionRecognitionCNN() = default;
    ~ActionRecognitionCNN();

    bool Init();
    ActionType PredictBlock(const cw::common::IMU* input_data, uint16_t length);

    

private:
    bool RunModel();
    constexpr static uint8_t kQuantificationScale = (pow(2,INPUT_1_OUTPUT_DEC));
    constexpr static uint8_t kThreshold = 70; // 70% 的置信度阈值，低于这个值的预测结果将被视为未知动作
    nnom_model_t* model_;
    ActionType action_type_{ActionType::kUnknown};

};
} 
}