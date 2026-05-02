#include <Arduino.h>

#include "mpu6050_imu.h"
#include "cnn.h"
#include "imu_resampler.h"
#include "button.h"
#include "led.h"

#include "ble_remote.h"

// =============================================================================
// 系统工作模式
// -----------------------------------------------------------------------------
// 系统在运行时只会处于其中一种模式, 通过双击按键切换:
//
// 两种模式共享完全相同的采样交互:
//     按下 (PressDown) -> 亮 LED + 启动 IMU 连续采样
//     松开 (Release)   -> 停 IMU + 灭 LED
// 差异只在 "采完之后做什么":
//
//   - Application : 正常使用模式.
//                   把这段任意时长的数据线性插值到 150 帧 -> CNN 推理 -> 蓝牙下发.
//
//   - Acquisition : 数据采集模式.
//                   把这段原始 IMU 6 通道数据 dump 到串口, 用于离线训练.
//
// 单击 / 长按事件在两种模式下都被静默忽略 -- 用户体验完全由 PressDown +
// Release 两个边沿描述, 与按住时长无关.
// 默认开机进入 Application, 用户开始使用前无需任何配置.
// =============================================================================
enum class SystemWorkMode {
  Application,  // 应用模式: 手势识别 + 蓝牙控制
  Acquisition   // 采集模式: 记录 IMU 原始数据用于训练
};
static SystemWorkMode kWorkMode = SystemWorkMode::Application;

// CNN 模型输入张量的固定帧数 (= weights.h 训练时窗口长度).
// 任何送入 PredictBlock 的序列必须先线性插值到这个长度.
static constexpr uint16_t kModelInputFrames = 150;


/**
 * 把 CNN 识别结果映射为蓝牙动作并下发.
 *
 * 流程:
 *   1) 取 BleRemote 单例
 *   2) 若未连接对端: 业务命令无法发送, 仅打日志告知用户.
 *      此时 BleRemote 已在持续广播 (未配对则普通广播 / 已配对则带 SN
 *      唤醒广播), 对端会在合适时机主动连接, 用户无需在魔杖侧做任何动作.
 *   3) 已连接情况下按手势分发:
 *      - 圆圈 (顺/逆时针视为同一语义) -> 开始录制
 *      - 勾 (Check)                  -> 切换到下一个子模式
 *      - 叉 (左/右斜均归为叉)        -> 在当前流上打高光标记
 *      - 未知手势                    -> 仅打日志, 不发送命令
 *
 * 设计要点: 本函数完全不感知任何具体协议字段 (命令字 / 模式 ID),
 * 全部由 BleRemote 内部处理, 便于把代码上传开源.
 */
static void dispatch_gesture_to_ble(cw::cnn::ActionType action) {
  using cw::cnn::ActionType;
  using cw::ble::BleRemote;

  auto& ble = BleRemote::GetInstance();

  // 未连接对端: 业务命令无法到达, 直接忽略本次手势.
  // 广播由 BleRemote 内部维护, 用户不必在此触发任何重试动作.
  if (!ble.IsConnected()) {
    ILOGT("[main] gesture %d ignored: peer not connected\n",
          static_cast<int>(action));
    return;
  }

  // 注: 所有 SendXxx 都返回 bool 表示 "是否成功推送 GATT NOTIFY"
  //     这里必须看返回值, 避免在 BLE 队列拥塞 / 内部组帧异常时仍打"成功"日志
  bool sent = false;
  const char* gname = "unknown";
  switch (action) {
    case ActionType::kCircle_Cw:
    case ActionType::kCircle_Aw:
      gname = "circle";
      sent = ble.SendRecordStart();
      break;
    case ActionType::kCheck:
      gname = "check";
      sent = ble.CycleToNextSubMode();
      break;
    case ActionType::kCross_Left:
    case ActionType::kCross_Right:
      gname = "cross";
      sent = ble.SendHighlightMark();
      break;
    case ActionType::kUnknown:
    default:
      ILOGT("[main] unknown gesture %d, ignored\n", static_cast<int>(action));
      return;
  }

  if (sent) {
    ILOGT("[main] gesture %s -> cmd sent OK\n", gname);
  } else {
    ILOGT("[main] gesture %s -> cmd FAILED to send\n", gname);
  }
}


/**
 * 系统一次性初始化, 在 setup() 阶段调用.
 *
 * 流程:
 *   1) 串口 115200 用于日志
 *   2) 提升 loop 任务优先级至 3, 让按键 / IMU 处理更及时
 *      (默认是 1, 可能被一些后台任务抢占影响实时性)
 *   3) 初始化 IMU 与 CNN 推理引擎
 *   4) 注册按键 (GPIO26) 并启动按键管理器
 *   5) 注册状态 LED (GPIO13) 并启动 LED 管理器
 *   6) 初始化 BLE 协议栈 (启动可发现广播)
 */
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

  cw::ble::BleRemote::GetInstance().Init();
}


/// Arduino 框架入口: 只做一次性初始化
void setup() {
  system_init();
}


/**
 * 双击事件处理: 在两种工作模式之间切换 (LED 仅做视觉反馈, 不影响业务).
 *
 *   - 当前 Application -> 切到 Acquisition, LED 快闪 2s 提示
 *   - 当前 Acquisition -> 切回 Application, LED 长亮 3s 提示
 *
 * 注: 双击事件实际由 capture_press_to_release 在采样循环里捕获,
 *     当用户的二次按下被 button 状态机判定为 DoubleClick 时同步触发本函数.
 */
void double_click_handler(void) {
  if (kWorkMode == SystemWorkMode::Application) {
    kWorkMode = SystemWorkMode::Acquisition;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                               cw::led::LedMode::BlinkFast, 2000,
                                               cw::led::LedMode::Off);
    ILOGN("[main] mode -> Acquisition");
  } else {
    kWorkMode = SystemWorkMode::Application;
    cw::led::LedManager::GetInstance().SetMode(cw::led::LedType::Status,
                                               cw::led::LedMode::On, 3000,
                                               cw::led::LedMode::Off);
    ILOGN("[main] mode -> Application");
  }
}


// 采样循环退出原因, 决定后处理走哪条路径
enum class CaptureExitReason {
  UserReleased,      // 正常松开 -> 走模式分支后处理
  UserDoubleClicked, // 期间收到 DoubleClick -> 切模式 + 丢弃数据
  HitMaxFrames,      // 达到上限自动停止 -> 走模式分支后处理 (按上限当成有效手势)
};


/**
 * 共享底层: "按下到松开" 连续采样.
 *
 * 调用前提: 调用方刚从按键队列取到 ButtonEvent::PressDown.
 *
 * 流程:
 *   1) 点亮状态 LED 提示 "正在记录"
 *   2) 拿 IMU 内部缓冲首地址 + 容量 (= 300 帧)
 *   3) 循环:
 *        - SampleOneFrame(buf[N++])     -- 同步采一帧 ~3ms
 *        - GetEvent(7ms)                -- 等下一帧时间, 顺带 poll 按键队列
 *          - JoystickBtn::Release      -> 退出循环, 返回 UserReleased
 *          - JoystickBtn::DoubleClick  -> 退出循环, 返回 UserDoubleClicked
 *                                          (button 状态机会在二次按下时同步发出
 *                                           PressDown + DoubleClick, 此处的
 *                                           DoubleClick 必须在采样循环里截获,
 *                                           否则就丢失了切模式的能力)
 *          - 其他事件                   -> 忽略, 继续采样
 *        - N >= kContinuousMaxFrames    -> 退出循环, 返回 HitMaxFrames
 *   4) 熄灭 LED
 *
 * 注:
 *   - 期间整个 loop 阻塞, 但最长 ~3 秒 (300 帧 * 10ms),
 *     BleRemote::SwitchAdvByTick 内部已按 N 秒节流, 短暂延迟无副作用.
 *   - 7ms 等待时间 = "10ms 总周期 - 3ms IMU 通信", 与原 GetSamplData sleep_ms 完全等价.
 */
static CaptureExitReason capture_press_to_release(cw::common::IMU*& out_buf,
                                                  uint16_t& out_n) {
  using cw::button::ButtonEvent;
  using cw::button::ButtonMessage;
  using cw::button::ButtonType;

  auto& imu = cw::imu::Mpu6050IMU::GetInstance();
  auto& btn = cw::button::ButtonManager::GetInstance();
  auto& led = cw::led::LedManager::GetInstance();

  uint16_t buf_capacity = 0;
  out_buf = imu.GetContinuousBuffer(buf_capacity);
  if (buf_capacity > cw::imu::kContinuousMaxFrames) {
    buf_capacity = cw::imu::kContinuousMaxFrames;
  }

  led.SetMode(cw::led::LedType::Status,
              cw::led::LedMode::On, 0,
              cw::led::LedMode::On);

  uint16_t n = 0;
  CaptureExitReason reason = CaptureExitReason::HitMaxFrames;
  ButtonMessage msg{};

  while (n < buf_capacity) {
    imu.SampleOneFrame(out_buf[n]);
    ++n;

    if (btn.GetEvent(msg, pdMS_TO_TICKS(7))) {
      if (msg.type == ButtonType::JoystickBtn) {
        if (msg.event == ButtonEvent::Release) {
          reason = CaptureExitReason::UserReleased;
          break;
        }
        if (msg.event == ButtonEvent::DoubleClick) {
          reason = CaptureExitReason::UserDoubleClicked;
          break;
        }
      }
      // 其他事件 (Power/Menu/SingleClick/LongPress/重入 PressDown) 与本次手势
      // 无关, 直接吞掉继续采样.
    }
  }

  led.SetMode(cw::led::LedType::Status,
              cw::led::LedMode::Off, 0,
              cw::led::LedMode::Off);

  out_n = n;
  return reason;
}


/**
 * Acquisition 模式后处理: 把本次采到的 N 帧 IMU 数据 dump 到串口.
 *
 * 用途: 训练数据集制作时, 把魔杖接电脑通过串口抓 6 通道时序日志,
 *       离线 Python 脚本从日志里 parse 出每段手势.
 *
 * 输出格式 (每帧一行, 6 列 tab 分隔, 与原 GetSamplData 内的 ILOGT 完全一致):
 *   acc.x  acc.y  acc.z  gyro.roll  gyro.pitch  gyro.yaw
 *
 * 防御性: buf/n 是来自 capture_press_to_release 的引用赋值结果, 正常情况下
 *         一定非空且非零; 这里仍做一次 sanity check, 防止未来调用方误传.
 */
static void dump_capture_for_training(const cw::common::IMU* buf, uint16_t n) {
  if (buf == nullptr || n == 0) {
    ILOGT("[acq] dump aborted: invalid args buf=%p n=%u\n",
          static_cast<const void*>(buf), n);
    return;
  }
  ILOGT("[acq] capture begin, %u frames\n", n);
  for (uint16_t i = 0; i < n; ++i) {
    ILOGT("%f", buf[i].acc.x);      ILOGT("\t");
    ILOGT("%f", buf[i].acc.y);      ILOGT("\t");
    ILOGT("%f", buf[i].acc.z);      ILOGT("\t");
    ILOGT("%f", buf[i].gyro.roll);  ILOGT("\t");
    ILOGT("%f", buf[i].gyro.pitch); ILOGT("\t");
    ILOGT("%f\n", buf[i].gyro.yaw);
  }
  ILOGN("[acq] capture end");
}


/**
 * Application 模式后处理: 长度归一化到 150 帧 -> CNN 推理 -> BLE 下发.
 *
 * 参数语义 (注意: 是 "只读" 而非 "外传"):
 *   - buf : 来自 capture_press_to_release 引用赋值的 IMU 内部静态缓冲首址,
 *           本函数<b>不修改</b> buf, 仅作为 Resample 的输入指针, 故值传递正确;
 *   - n   : 来自 capture_press_to_release 引用赋值的实际采到帧数,
 *           本函数<b>不修改</b> n, 仅作为 Resample 的输入长度, 故值传递正确.
 *
 * 防御性: 即便参数语义正确, 仍 sanity check 一次, 防止未来调用方误传 (例如
 *         有人重构时漏掉 capture_press_to_release 的引用赋值).
 */
static void recognize_and_dispatch(const cw::common::IMU* buf, uint16_t n) {
  if (buf == nullptr || n == 0) {
    ILOGT("[app] recognize aborted: invalid args buf=%p n=%u\n",
          static_cast<const void*>(buf), n);
    return;
  }

  // 用栈上缓冲, 避免污染 IMU 内部缓冲 (后续采样还会复用)
  cw::common::IMU normalized[kModelInputFrames];
  cw::cnn::ImuResampler::Resample(buf, n, normalized, kModelInputFrames);

  auto action_type =
      cw::cnn::ActionRecognitionCNN::GetInstance().PredictBlock(
          normalized, kModelInputFrames);
  ILOGT("[app] action type: %d (from %u raw frames)\n",
        static_cast<int>(action_type), n);

  dispatch_gesture_to_ble(action_type);
}


/**
 * 顶层: 按下 -> 亮灯采样 -> 松开停采灭灯 -> 按当前模式做后处理.
 *
 * 流程:
 *   1) capture_press_to_release: 共享底层, 阻塞循环, 取出 N 帧
 *   2) reason == UserDoubleClicked -> 用户在双击切模式, 调 double_click_handler 后返回
 *      (本次 spurious 短按数据丢弃)
 *   3) N < kContinuousMinFrames -> 视为误触, 直接返回, 不做任何后处理
 *   4) 按工作模式分支:
 *        Application -> recognize_and_dispatch
 *        Acquisition -> dump_capture_for_training
 *
 * 设计要点:
 *   - 单击 / 长按事件被彻底舍弃: 用户体验由 "按下 + 松开" 两个边沿完全描述
 *   - 两种模式的差异只在"采完之后做什么", 采样过程 (亮灯/计帧/停采) 完全一致
 */
void handle_button_press(void) {
  // 这两个变量只是 "出参占位": capture_press_to_release 通过 IMU*& / uint16_t&
  // 引用回写真实值. 这里初始化为 nullptr/0 仅是良好习惯, 不会影响调用结果.
  cw::common::IMU* buf = nullptr;
  uint16_t n = 0;

  CaptureExitReason reason = capture_press_to_release(buf, n);

  // 显式 trace: 看到 buf 是 imus_ 内部静态缓冲的首址 (非空), n 是采到帧数.
  // 该日志在 release 构建里可以裁掉, 这里保留便于初次集成时验证数据流.
  ILOGT("[main] capture returned: buf=%p n=%u reason=%d\n",
        static_cast<const void*>(buf), n, static_cast<int>(reason));

  if (reason == CaptureExitReason::UserDoubleClicked) {
    ILOGT("[main] double-click during capture, switching mode\n");
    double_click_handler();
    return;
  }

  if (reason == CaptureExitReason::HitMaxFrames) {
    ILOGT("[main] capture hit max %u frames, force stopped\n", n);
  } else {
    ILOGT("[main] capture done: %u frames\n", n);
  }

  if (n < cw::imu::kContinuousMinFrames) {
    ILOGT("[main] gesture too short (%u < %u frames), discarded\n",
          n, cw::imu::kContinuousMinFrames);
    return;
  }

  if (kWorkMode == SystemWorkMode::Application) {
    recognize_and_dispatch(buf, n);
  } else {
    dump_capture_for_training(buf, n);
  }
}


/**
 * Arduino 框架主循环.
 *
 * 流程:
 *   1) 给 BleRemote 一次内部 tick: 已配对+未连接状态下驱动 Normal/Wakeup
 *      广播包按周期轮换 (内部已节流, 高频调用无副作用).
 *   2) 阻塞至多 20ms 等一个按键事件;
 *      未取到事件 -> 立即返回继续轮询, 让 BLE tick 能尽快回到 1).
 *   3) 按按键事件分发:
 *      - JoystickBtn::PressDown   -> handle_button_press (按下到松开采样 + 模式分支后处理)
 *      - JoystickBtn::DoubleClick -> double_click_handler (容错路径; 通常 DoubleClick
 *                                    在 capture_press_to_release 内部已被截获)
 *      - 其他 (Release / SingleClick / LongPress) -> 静默忽略
 *      - Power / Menu             -> 仅打日志预留扩展
 *
 * 注: BLE 连接 / 断开 / 收帧等事件由 BleRemote 内部回调直接驱动,
 *     主循环只需周期 tick 推进广播轮换.
 */
void loop() {
  using namespace cw::button;
  using namespace cw::led;

  cw::ble::BleRemote::GetInstance().SwitchAdvByTick();

  ButtonMessage message{};
  if (!ButtonManager::GetInstance().GetEvent(message, pdMS_TO_TICKS(20))) {
    return;
  }

  switch (message.type) {
    case ButtonType::Power: {
      ILOGN("power");
    } break;
    case ButtonType::JoystickBtn: {
      if (ButtonEvent::PressDown == message.event) {
        handle_button_press();
      } else if (ButtonEvent::DoubleClick == message.event) {
        // 容错路径: 正常情况下 DoubleClick 已经在 capture 循环里被截获,
        // 这里只是兜底 (例如未来 button 时序变化导致 DoubleClick 在循环外到达).
        double_click_handler();
      }
      // 其余事件 (Release / SingleClick / LongPress) 静默忽略
    } break;
    case ButtonType::Menu: {
      ILOGN("menu");
    } break;
  }
}

