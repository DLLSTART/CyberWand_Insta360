# CyberWand 固件设计 v3.0 - 最终版

**创建时间**: 2026-04-05  
**版本**: v3.0 (根据皇上需求更新)  
**目标硬件**: ESP32-C6 + MPU6050

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CyberWand 软件架构                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   按键检测   │     │   MPU6050    │     │   USB 串口   │
│  (模式切换)  │────▶│  数据采集    │────▶│  (数据传输)  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  姿态识别模型   │
                   │   (C 语言实现)   │
                   └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   蓝牙 5.4     │
                   │  (消息发送)    │
                   └─────────────────┘
```

---

## 二、工作模式

### 2.1 模式定义

| 模式 | 进入方式 | 功能 | 数据流向 |
|------|----------|------|----------|
| **录制模式** | 单击按键 | IMU 数据→USB 串口→电脑 | MPU6050 → USB |
| **控制模式** | 再次单击 | IMU 数据→姿态识别→蓝牙 | MPU6050 → 模型 → 蓝牙 |
| **持续录制** | 录制模式 + 长按 | 持续发送 IMU 数据 | MPU6050 → USB (持续) |
| **持续控制** | 控制模式 + 长按 | 持续姿态检测 + 蓝牙 | MPU6050 → 模型 → 蓝牙 (持续) |

### 2.2 状态机

```
初始状态：录制模式

状态转换:
┌─────────────┐
│  录制模式   │◀──── 初始状态
│  (IDLE)     │
└──────┬──────┘
       │ 单击按键
       ▼
┌─────────────┐
│  控制模式   │
│  (CONTROL)  │
└──────┬──────┘
       │ 单击按键
       ▼
┌─────────────┐
│  录制模式   │
│  (循环)     │
└─────────────┘

长按事件 (任意模式):
├── 长按开始 (2 秒) → 进入持续模式
├── 长按期间 → 持续数据传输
└── 长按释放 → 返回正常模式
```

---

## 三、核心功能模块

### 3.1 MPU6050 数据采集

```c
// 数据结构
typedef struct {
    int16_t ax, ay, az;     // 加速度计 (单位：mg)
    int16_t gx, gy, gz;     // 陀螺仪 (单位：mdps)
    uint32_t timestamp;     // 时间戳 (ms)
} imu_data_t;

// 采样频率：100Hz
// 数据格式：二进制 (USB 串口) / 蓝牙 BLE
```

### 3.2 姿态识别模型 (C 语言实现)

```c
// 姿态定义
typedef enum {
    POSE_IDLE = 0,          // 空闲
    POSE_WAVE,              // 挥手
    POSE_FIST,              // 握拳
    POSE_ROTATE_LEFT,       // 左旋转
    POSE_ROTATE_RIGHT,      // 右旋转
    POSE_TILT_UP,           // 上倾斜
    POSE_TILT_DOWN,         // 下倾斜
    POSE_COUNT
} pose_type_t;

// 模型结构 (简化版决策树)
typedef struct {
    pose_type_t pose;
    float threshold;
    int axis;
} pose_model_t;

// 姿态匹配函数
pose_type_t recognize_pose(imu_data_t* data, imu_data_t* history);
```

### 3.3 蓝牙消息协议

```c
// 蓝牙消息结构
typedef struct {
    uint8_t header;         // 消息头 (0xAA)
    uint8_t pose_id;        // 姿态 ID
    uint8_t timestamp;      // 时间戳
    uint8_t checksum;       // 校验和
} ble_message_t;

// 私有数据模拟 (示例)
#define BLE_POSE_IDLE       0x00
#define BLE_POSE_WAVE       0x01
#define BLE_POSE_FIST       0x02
#define BLE_POSE_ROTATE_L   0x03
#define BLE_POSE_ROTATE_R   0x04
#define BLE_POSE_TILT_UP    0x05
#define BLE_POSE_TILT_DOWN  0x06
```

### 3.4 USB 串口通信

```c
// USB 串口配置
#define USB_BAUDRATE    115200
#define USB_DATA_BITS   8
#define USB_STOP_BITS   1
#define USB_PARITY      NONE

// 数据格式 (二进制)
// [Header][Data][Checksum]
// 0xAA [6 bytes IMU][1 byte checksum]
```

### 3.5 按键检测

```c
// 按键事件
typedef enum {
    KEY_NONE = 0,
    KEY_SHORT_PRESS,    // 短按 (<2s)
    KEY_LONG_PRESS,     // 长按 (≥2s)
    KEY_LONG_RELEASE    // 长按释放
} key_event_t;

// 检测逻辑
key_event_t detect_key_event();
```

### 3.6 LED 灯语

```c
// LED 模式
typedef enum {
    LED_IDLE = 0,       // 闪烁 (等待连接)
    LED_RECORD,         // 常亮 (录制中)
    LED_CONTROL,        // 慢闪 (控制模式)
    LED_TRANSFER,       // 快闪 (数据传输)
    LED_ERROR           // 快闪 3 次 (错误)
} led_pattern_t;
```

---

## 四、主程序流程

```c
void app_main() {
    // 1. 初始化
    mpu6050_init();
    usb_serial_init();
    ble_init();
    led_init();
    
    // 2. 主循环
    while (1) {
        // 读取 IMU 数据
        imu_data_t imu = mpu6050_read();
        
        // 检测按键事件
        key_event_t key = detect_key_event();
        
        // 状态机处理
        switch (current_mode) {
            case MODE_RECORD:
                if (key == KEY_SHORT_PRESS) {
                    current_mode = MODE_CONTROL;
                    led_set(LED_CONTROL);
                } else if (key == KEY_LONG_PRESS) {
                    continuous_mode = true;
                    led_set(LED_TRANSFER);
                } else if (key == KEY_LONG_RELEASE) {
                    continuous_mode = false;
                    led_set(LED_RECORD);
                }
                
                // 发送 IMU 数据到 USB
                usb_send_imu(&imu);
                break;
                
            case MODE_CONTROL:
                if (key == KEY_SHORT_PRESS) {
                    current_mode = MODE_RECORD;
                    led_set(LED_RECORD);
                } else if (key == KEY_LONG_PRESS) {
                    continuous_mode = true;
                    led_set(LED_TRANSFER);
                } else if (key == KEY_LONG_RELEASE) {
                    continuous_mode = false;
                    led_set(LED_CONTROL);
                }
                
                // 姿态识别
                pose_type_t pose = recognize_pose(&imu, history);
                
                // 发送蓝牙消息
                if (continuous_mode || pose_changed(pose)) {
                    ble_send_pose(pose);
                }
                break;
        }
        
        // 延迟 (10ms @ 100Hz)
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
```

---

## 五、单元测试

### 5.1 MPU6050 测试

```c
// test_mpu6050.c
void test_mpu6050_init() {
    TEST_ASSERT_EQUAL(ESP_OK, mpu6050_init());
}

void test_mpu6050_read() {
    imu_data_t imu;
    TEST_ASSERT_EQUAL(ESP_OK, mpu6050_read(&imu));
    TEST_ASSERT_NOT_EQUAL(0, imu.ax);
    TEST_ASSERT_NOT_EQUAL(0, imu.ay);
    TEST_ASSERT_EQUAL(0, imu.az); // 静止时 Z 轴应为 g
}
```

### 5.2 姿态识别测试

```c
// test_pose_recognition.c
void test_pose_idle() {
    imu_data_t imu = {0, 0, 1000, 0, 0, 0}; // 静止
    TEST_ASSERT_EQUAL(POSE_IDLE, recognize_pose(&imu, NULL));
}

void test_pose_wave() {
    imu_data_t imu = {500, 0, 0, 0, 1000, 0}; // X 轴加速 + Y 轴陀螺仪
    TEST_ASSERT_EQUAL(POSE_WAVE, recognize_pose(&imu, NULL));
}

void test_pose_fist() {
    imu_data_t imu = {0, 0, 2000, 0, 0, 0}; // Z 轴加速
    TEST_ASSERT_EQUAL(POSE_FIST, recognize_pose(&imu, NULL));
}
```

### 5.3 按键测试

```c
// test_button.c
void test_short_press() {
    simulate_button_press(500); // 500ms
    TEST_ASSERT_EQUAL(KEY_SHORT_PRESS, detect_key_event());
}

void test_long_press() {
    simulate_button_press(2500); // 2.5s
    TEST_ASSERT_EQUAL(KEY_LONG_PRESS, detect_key_event());
}
```

### 5.4 USB 串口测试

```c
// test_usb_serial.c
void test_usb_send() {
    imu_data_t imu = {100, 200, 1000, 0, 0, 0};
    TEST_ASSERT_EQUAL(8, usb_send_imu(&imu));
}

void test_usb_checksum() {
    uint8_t data[] = {0xAA, 0x01, 0x02, 0x03};
    uint8_t checksum = calculate_checksum(data, 4);
    TEST_ASSERT_EQUAL(0xAA ^ 0x01 ^ 0x02 ^ 0x03, checksum);
}
```

### 5.5 蓝牙消息测试

```c
// test_ble.c
void test_ble_message_format() {
    ble_message_t msg = {0xAA, POSE_WAVE, 0x01, 0};
    msg.checksum = calculate_checksum((uint8_t*)&msg, 3);
    
    TEST_ASSERT_EQUAL(0xAA, msg.header);
    TEST_ASSERT_EQUAL(POSE_WAVE, msg.pose_id);
    TEST_ASSERT_NOT_EQUAL(0, msg.checksum);
}

void test_ble_send() {
    TEST_ASSERT_EQUAL(ESP_OK, ble_send_pose(POSE_WAVE));
}
```

---

## 六、项目结构

```
cyberwand_firmware/
├── src/
│   ├── main.c                  # 主程序
│   ├── mpu6050.c/h            # MPU6050 驱动
│   ├── usb_serial.c/h         # USB 串口
│   ├── ble_comm.c/h           # 蓝牙通信
│   ├── button.c/h             # 按键检测
│   ├── led.c/h                # LED 灯语
│   ├── pose_model.c/h         # 姿态识别模型
│   └── utils.c/h              # 工具函数
├── tests/
│   ├── test_mpu6050.c
│   ├── test_pose_recognition.c
│   ├── test_button.c
│   ├── test_usb_serial.c
│   └── test_ble.c
├── CMakeLists.txt
├── sdkconfig
└── README.md
```

---

## 七、开发环境

### 7.1 工具链

```bash
# ESP-IDF 安装
git clone https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32c6
. ./export.sh

# 项目编译
idf.py set-target esp32c6
idf.py build
idf.py flash
idf.py monitor
```

### 7.2 测试框架

```bash
# 运行单元测试
idf.py build
python -m pytest tests/

# 代码覆盖率
gcov --version
```

---

## 八、检查清单

### 硬件
- [x] MPU6050 传感器选型
- [x] ESP32-C6 主控选型
- [x] 引脚分配完成
- [x] 电路设计完成
- [ ] PCB 绘制
- [ ] PCB 打样
- [ ] 元件焊接

### 软件
- [x] 系统架构设计
- [x] 工作模式定义
- [x] 姿态模型设计
- [x] 通信协议设计
- [ ] 代码实现
- [ ] 单元测试
- [ ] 集成测试

---

**设计状态**: 软件设计完成，待代码实现  
**预计开发周期**: 硬件 2 周 + 软件 2 周 = 4 周
