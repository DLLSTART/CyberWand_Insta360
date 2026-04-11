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
  cw::imu::Mpu6050IMU::GetInstance().Init();
  cw::cyberwand::radio::InfraredRadio::GetInstance().Init();
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
    const uint16_t* recv_buffer = cw::cyberwand::radio::InfraredRadio::GetInstance().Receive(radio_size);
    if(recv_buffer != nullptr) {
      auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
      if(data_ptr == nullptr) {
        ILOGN("Imu Data Error!");
        return;
      }
      cw::imu::Mpu6050IMU::GetInstance().Commit();
    }
  } else {
    const uint16_t* recv_buffer = cw::cyberwand::radio::InfraredRadio::GetInstance().Receive(radio_size);
    if(recv_buffer != nullptr) {
      auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
      if(data_ptr == nullptr) {
        ILOGN("Imu Data Error!");
        return;
      }
      auto action_type = cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(data_ptr, imu_count);
      ILOGT("Action Type: %d\n", static_cast<int>(action_type));
      cw::imu::Mpu6050IMU::GetInstance().Commit();
    }
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
          ILOGN("Joystick Long Press");
          LedManager::GetInstance().SetMode(LedType::Status, LedMode::Off);
        } 
      }break;
      case ButtonType::Menu: {
        ILOGN("Menu");
      } break;
    }
  }
}