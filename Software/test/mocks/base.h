// =============================================================================
// base.h — 本地单元测试用版本, 替代 lib/base/base.h
// -----------------------------------------------------------------------------
// 与生产版本差异:
//   - 不引入 FreeRTOS 头, 不定义 Mutex/AutoMutex (本项目 ble 模块未使用)
//   - ILOGN / ILOGT 宏直通 mock Serial (默认静默)
//   - Singleton<T> 模板与生产版本完全一致
// =============================================================================
#pragma once
#include <Arduino.h>

#define ILOGN Serial.println
#define ILOGT Serial.printf

namespace cw {
namespace base {

template <typename T>
class Singleton {
public:
    static T& GetInstance() {
        static T instance;
        return instance;
    }

    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;

protected:
    Singleton() = default;
    virtual ~Singleton() = default;
};

}  // namespace base
}  // namespace cw
