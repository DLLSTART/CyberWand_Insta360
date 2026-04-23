#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLEAdvertising.h>

#include "mpu6050_imu.h"
#include "cnn.h"
#include "button.h"
#include "led.h"


// 系统工作模式
enum class SystemWorkMode {
  Application,  // 应用模式：执行手势识别 + 蓝牙发送
  Acquisition   // 采集模式：记录 IMU 原始数据，用于训练
};
static SystemWorkMode kWorkMode = SystemWorkMode::Application;


// 蓝牙服务与特征 UUID (自定义)
static const char kServiceUuid[]    = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
static const char kTxCharUuid[]     = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";

// 广播配置：每个手势对应一串可配置字符串，默认示例
// 实际工程中可从 NVS / Flash 读取
struct GestureBlePayload {
  int         gesture_id;
  const char* payload;
};

static const GestureBlePayload kGesturePayloads[] = {
  {0, "GESTURE_CIRCLE"},
  {1, "GESTURE_LIGHTNING"},
  {2, "GESTURE_H"},
  {3, "GESTURE_W"},
};

static BLEServer*         s_ble_server        = nullptr;
static BLECharacteristic* s_tx_characteristic = nullptr;
static BLEAdvertising*    s_ble_advertising   = nullptr;
static bool               s_ble_client_conn   = false;


// BLE 连接事件回调
class BleServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* server) override {
    s_ble_client_conn = true;
    Serial.println("[ble] client connected");
  }
  void onDisconnect(BLEServer* server) override {
    s_ble_client_conn = false;
    Serial.println("[ble] client disconnected, restart advertising");
    server->getAdvertising()->start();
  }
};


// 蓝牙初始化：建立 GATT 服务 + 启动广播
static void ble_init(void) {
  BLEDevice::init("CyberWand");
  s_ble_server = BLEDevice::createServer();
  s_ble_server->setCallbacks(new BleServerCallbacks());

  BLEService* service = s_ble_server->createService(kServiceUuid);
  s_tx_characteristic = service->createCharacteristic(
      kTxCharUuid,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ);
  service->start();

  s_ble_advertising = BLEDevice::getAdvertising();
  s_ble_advertising->addServiceUUID(kServiceUuid);
  s_ble_advertising->setScanResponse(true);
  s_ble_advertising->start();
  Serial.println("[ble] advertising started");
}


// 根据手势 id 查表，通过 BLE 发送数据并更新广播内容
static void ble_send_gesture(int gesture_id) {
  const char* payload = nullptr;
  for (const auto& item : kGesturePayloads) {
    if (item.gesture_id == gesture_id) {
      payload = item.payload;
      break;
    }
  }
  if (payload == nullptr) {
    Serial.printf("[ble] gesture %d not mapped\n", gesture_id);
    return;
  }

  // 连接状态下通过 NOTIFY 推送
  if (s_ble_client_conn && s_tx_characteristic != nullptr) {
    s_tx_characteristic->setValue(reinterpret_cast<uint8_t*>(const_cast<char*>(payload)),
                                  strlen(payload));
    s_tx_characteristic->notify();
    Serial.printf("[ble] notify: %s\n", payload);
  }

  // 未连接时更新广播数据，作为一次性广播消息
  if (!s_ble_client_conn && s_ble_advertising != nullptr) {
    BLEAdvertisementData adv_data;
    adv_data.setName("CyberWand");
    adv_data.setManufacturerData(std::string(payload));
    s_ble_advertising->setAdvertisementData(adv_data);
    Serial.printf("[ble] broadcast: %s\n", payload);
  }
}


void system_init(void) {
  Serial.begin(115200);

  // 1. 获取并打印原本的优先级 (通常 ESP32 默认是 1)
  UBaseType_t default_priority = uxTaskPriorityGet(NULL);
  Serial.printf("[system] loop Priority: %d\n", default_priority);

  // 2. 修改 loop 任务的优先级 (例如提高到 3)
  vTaskPrioritySet(NULL, 3);

  // 3. 验证是否修改成功
  UBaseType_t new_priority = uxTaskPriorityGet(NULL);
  Serial.printf("[system] loop Priority: %d\n", new_priority);

  cw::imu::Mpu6050IMU::GetInstance().Init();
  cw::cnn::ActionRecognitionCNN::GetInstance().Init();

  cw::button::ButtonManager::GetInstance().AddButton(26, cw::button::ButtonType::JoystickBtn);
  cw::button::ButtonManager::GetInstance().Begin();

  cw::led::LedManager::GetInstance().AddLed(13, cw::led::LedType::Status, HIGH);
  cw::led::LedManager::GetInstance().Begin();

  ble_init();
}


void setup() {
  system_init();
}


// 单击：采集模式下记录一段数据，应用模式下识别手势并通过 BLE 发送
void single_click_handler(void) {
  uint16_t imu_count = 0;
  if (kWorkMode == SystemWorkMode::Acquisition) {
    auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
    if (data_ptr == nullptr) {
      ILOGN("IMU data error");
      return;
    }
    cw::imu::Mpu6050IMU::GetInstance().Commit();
    return;
  }

  cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                             cw::led::LedMode::On, 0,
                                             cw::led::LedMode::On);
  auto data_ptr = cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
  if (data_ptr == nullptr) {
    ILOGN("IMU data error");
    return;
  }
  cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                             cw::led::LedMode::Off, 0,
                                             cw::led::LedMode::Off);
  auto action_type = cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(data_ptr, imu_count);
  ILOGT("action type: %d\n", static_cast<int>(action_type));
  cw::imu::Mpu6050IMU::GetInstance().Commit();

  // 手势识别结果通过 BLE 发送/广播
  ble_send_gesture(static_cast<int>(action_type));
}


// 双击：切换应用模式 / 采集模式
void double_click_handler(void) {
  if (kWorkMode == SystemWorkMode::Application) {
    kWorkMode = SystemWorkMode::Acquisition;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                               cw::led::LedMode::BlinkFast, 2000,
                                               cw::led::LedMode::Off);
  } else {
    kWorkMode = SystemWorkMode::Application;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                               cw::led::LedMode::On, 3000,
                                               cw::led::LedMode::Off);
  }
}


// 长按：强制采样一段数据并提交
void long_press_handler(void) {
  uint16_t imu_count = 150;
  cw::imu::Mpu6050IMU::GetInstance().GetSamplData(imu_count);
  cw::imu::Mpu6050IMU::GetInstance().Commit();
}


void loop() {
  using namespace cw::button;
  using namespace cw::led;

  ButtonMessage message{};
  if (!ButtonManager::GetInstance().GetEvent(message)) {
    return;
  }

  switch (message.type) {
    case ButtonType::Power: {
      ILOGN("power");
    } break;
    case ButtonType::JoystickBtn: {
      if (ButtonEvent::SingleClick == message.event) {
        single_click_handler();
      } else if (ButtonEvent::DoubleClick == message.event) {
        double_click_handler();
      } else if (ButtonEvent::LongPress == message.event) {
        long_press_handler();
      }
    } break;
    case ButtonType::Menu: {
      ILOGN("menu");
    } break;
  }
}
