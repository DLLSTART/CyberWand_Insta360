#include "Arduino.h"

#include <cstdarg>
#include <cstdio>
#include <cstring>

namespace {
uint32_t g_mock_ms     = 0;
bool     g_serial_echo = false;
}  // namespace

namespace cw_test {

void SetMockMillis(uint32_t v) { g_mock_ms = v; }
void AdvanceMockMillis(uint32_t n) { g_mock_ms += n; }
void EnableSerialEcho(bool on) { g_serial_echo = on; }

}  // namespace cw_test

uint32_t millis() { return g_mock_ms; }

HardwareSerialMock Serial;

size_t HardwareSerialMock::print(const char* s) {
    if (g_serial_echo && s) {
        std::fputs(s, stdout);
    }
    return s ? std::strlen(s) : 0;
}
size_t HardwareSerialMock::println(const char* s) {
    if (g_serial_echo) {
        if (s) std::fputs(s, stdout);
        std::fputc('\n', stdout);
    }
    return s ? std::strlen(s) + 1 : 1;
}
size_t HardwareSerialMock::println() {
    if (g_serial_echo) std::fputc('\n', stdout);
    return 1;
}
size_t HardwareSerialMock::printf(const char* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    if (g_serial_echo) {
        int n = std::vfprintf(stdout, fmt, ap);
        va_end(ap);
        return n > 0 ? static_cast<size_t>(n) : 0;
    }
    // 静默时仍消耗 va 参数, 避免未定义行为
    char buf[256];
    int n = std::vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    return n > 0 ? static_cast<size_t>(n) : 0;
}
