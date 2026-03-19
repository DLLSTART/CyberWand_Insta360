#pragma once
#include "nnom.h"
#include "weights.h"
#include "common.h"
#include "base.h"

namespace cw {
namespace cnn {

typedef int8_t ModelOutput;

enum class ActionType : uint8_t {
    kLightning = 0,
    kClick = 1,
    kNoMotion = 2,
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
    constexpr static uint8_t kThreshold = 63;
    nnom_model_t* model_;
    ActionType action_type_{ActionType::kNoMotion};

};
} 
}