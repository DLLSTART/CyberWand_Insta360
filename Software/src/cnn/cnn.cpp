#include "cnn.h"

namespace cw {
namespace cnn {

static uint8_t static_buf_[1024 * 8];    /* 静态缓冲区，供 nnom 推理时使用，避免动态分配 */

ActionRecognitionCNN::~ActionRecognitionCNN() {
    if(model_ != nullptr) {
        nnom_free(model_);
        model_ = nullptr;
    }
}

bool ActionRecognitionCNN::Init() {
    nnom_set_static_buf(static_buf_, sizeof(static_buf_));
    model_ = nnom_model_create();
    if (model_ == nullptr) {
        return false;
    }
    return true;
}

ActionType ActionRecognitionCNN::PredictBlock(const cw::common::IMU* input_data, uint16_t length) {
    if (model_ == nullptr) {
        return ActionType::kUnknown;
    }
	for(uint16_t i = 0; i < length;i++){
		// nnom_input_data[i*3]   = (int8_t)round(input_data[i].acc.x  * kQuantificationScale);
		// nnom_input_data[i*3+1] = (int8_t)round(input_data[i].acc.y * kQuantificationScale);
		// nnom_input_data[i*3+2] = (int8_t)round(input_data[i].acc.z   * kQuantificationScale);

		// nnom_input_data[i*3]   = (int8_t)round(input_data[i].gyro.roll  * kQuantificationScale);
		// nnom_input_data[i*3+1] = (int8_t)round(input_data[i].gyro.pitch * kQuantificationScale);
		// nnom_input_data[i*3+2] = (int8_t)round(input_data[i].gyro.yaw   * kQuantificationScale);

		nnom_input_data[i*6]   = (int8_t)round(input_data[i].acc.x  * kQuantificationScale);
		nnom_input_data[i*6+1] = (int8_t)round(input_data[i].acc.y * kQuantificationScale);
		nnom_input_data[i*6+2] = (int8_t)round(input_data[i].acc.z   * kQuantificationScale);
		nnom_input_data[i*6+3]   = (int8_t)round(input_data[i].gyro.roll  * kQuantificationScale);
		nnom_input_data[i*6+4] = (int8_t)round(input_data[i].gyro.pitch * kQuantificationScale);
		nnom_input_data[i*6+5] = (int8_t)round(input_data[i].gyro.yaw   * kQuantificationScale);
	}
    if (!RunModel()) {
        return ActionType::kUnknown;
    }
    return action_type_;
}

bool ActionRecognitionCNN::RunModel() {
    model_run(model_);
    int8_t* output = (int8_t*)nnom_output_data;
    uint8_t max_index = 0;
    int8_t max_value = output[0];
    for (uint8_t i = 0; i < static_cast<uint8_t>(ActionType::kMax); i++) {
        // #if defined(CY_DEBUG)
        ILOGT("output[%d] = %d\n", i, (output[i] / 127) * 100); // 输出值归一化为百分比显示
        // #endif
        if (output[i] > max_value) {
            max_value = output[i];
            max_index = i;
        }
    }
    if (max_value > kThreshold) {
        action_type_ = static_cast<ActionType>(max_index);
    } else {
        action_type_ = ActionType::kUnknown;
    }
    return true;
}

} 
}