#pragma once
#include "nnom.h"
#include "weights.h"
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