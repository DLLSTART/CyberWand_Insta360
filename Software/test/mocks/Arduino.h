// =============================================================================
// Arduino.h — 本地单元测试用桩, 替代真实 Arduino 框架头
// -----------------------------------------------------------------------------
// 仅提供生产代码 (lib/ble) 在编译期需要的最小符号集:
//   - 基本整数类型 / size_t (从 <cstdint> 与 <cstddef> 转发)
//   - millis() : 由测试通过 cw_test::SetMockMillis() 显式驱动, 默认从 0 开始
//   - Serial.println / Serial.printf : 静默或直通 stdout (受全局开关控制)
//
// 与真 Arduino 行为差异:
//   - millis() 不会因系统时间自然推进, 必须由测试代码显式设置
//   - String / FreeRTOS API 全部不实现 (lib/ble 不需要)
// =============================================================================
#pragma once
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string>

// ---- 与生产代码可能用到的最小整型别名 ----
using byte = uint8_t;

// ---- 测试控制接口 ----
namespace cw_test {

// 设定下一次 millis() 返回值; 调用一次后保持, 直到下次设定
void SetMockMillis(uint32_t v);

// 让 millis() 自增 n 毫秒
void AdvanceMockMillis(uint32_t n);

// 是否把 Serial 输出转发到 stdout (默认 false 静默, 测试更干净)
void EnableSerialEcho(bool on);

}  // namespace cw_test

// ---- Arduino 风格全局函数 ----
uint32_t millis();

// ---- 全局 Serial 对象 (最小可用形态) ----
class HardwareSerialMock {
public:
    void   begin(uint32_t /*baud*/) {}
    size_t print(const char* s);
    size_t println(const char* s);
    size_t println();
    size_t printf(const char* fmt, ...);
};

extern HardwareSerialMock Serial;
