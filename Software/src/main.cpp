#include <Arduino.h>
#include "mpu6050_imu.h"
#include "infrared_radio.h"
#include "cnn.h"
#include "button.h"
#include "led.h"

// 定义系统工作模式 (PascalCase)
enum class SystemWorkMode {
    Application, // 应用模式
    Acquisition  // 采集模式
};
static SystemWorkMode kWorkMode = SystemWorkMode::Application; // 默认应用模式


void system_init(void) {
  Serial.begin(115200);

  // 1. 获取并打印原本的优先级 (通常 ESP32 默认是 1)
  UBaseType_t defaultPriority = uxTaskPriorityGet(NULL);
  Serial.printf("[system] loop Priority: %d\n", defaultPriority);

  // 2. 修改 loop 任务的优先级 (例如提高到 3)
  vTaskPrioritySet(NULL, 3);

  // 3. 验证是否修改成功
  UBaseType_t newPriority = uxTaskPriorityGet(NULL);
  Serial.printf("[system] loop Priority: %d\n", newPriority);

  cw::imu::Mpu6050IMU::GetInstance().Init();
  // cw::cyberwand::radio::InfraredRadio::GetInstance().Init();
  cw::cnn::ActionRecognitionCNN::GetInstance().Init();
       
  cw::button::ButtonManager::GetInstance().AddButton(26, cw::button::ButtonType::JoystickBtn);  
  cw::button::ButtonManager::GetInstance().Begin();

  cw::led::LedManager::GetInstance().AddLed(13, cw::led::LedType::Status, HIGH);
  cw::led::LedManager::GetInstance().Begin();    
}

void setup() {
  system_init();
}

void single_click_handler() {
  uint16_t imu_count = 0;
  uint16_t radio_size = 0;
  if (kWorkMode == SystemWorkMode::Acquisition) {
    auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
    if(data_ptr == nullptr) {
      ILOGN("Imu Data Error!");
      return;
    }
    cw::imu::Mpu6050IMU::GetInstance().Commit();
  } else {
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status, cw::led::LedMode::On, 0, cw::led::LedMode::On);
    auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
    if(data_ptr == nullptr) {
      ILOGN("Imu Data Error!");
      return;
    }
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status, cw::led::LedMode::Off, 0, cw::led::LedMode::Off);
    auto action_type = cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(data_ptr, imu_count);
    ILOGT("Action Type: %d\n", static_cast<int>(action_type));
    cw::imu::Mpu6050IMU::GetInstance().Commit();
  }
}

void double_click_handler() {
  if (kWorkMode == SystemWorkMode::Application) {
    kWorkMode = SystemWorkMode::Acquisition;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status, cw::led::LedMode::BlinkFast, 2000, cw::led::LedMode::Off);
  } else {
    kWorkMode = SystemWorkMode::Application;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status, cw::led::LedMode::On, 3000, cw::led::LedMode::Off);
  }
}

void long_press_handler() {
  // 这里可以添加长按事件的处理逻辑，例如切换到某个特殊模式或者重置设备等
  uint16_t imu_count = 150;
  cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
  cw::imu::Mpu6050IMU::GetInstance().Commit();
}



void loop() {
  using namespace cw::button;
  using namespace cw::led;

  ButtonMessage message{};
  if (ButtonManager::GetInstance().GetEvent(message)) {
    switch (message.type) 
    {
      case ButtonType::Power: {
        ILOGN("Power");
      } break;
      case ButtonType::JoystickBtn:{
        if (ButtonEvent::SingleClick == message.event) {
          single_click_handler();
        } else if (ButtonEvent::DoubleClick == message.event) {
          double_click_handler();
        } else if (ButtonEvent::LongPress == message.event) {
          long_press_handler();
        } 
      }break;
      case ButtonType::Menu: {
        ILOGN("Menu");
      } break;
    }
  }
}