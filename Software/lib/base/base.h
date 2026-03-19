#pragma once
#include <Arduino.h>
#include "freertos/task.h"
#define ILOGN Serial.println
#define ILOGT Serial.printf
#define SleepMs(ms) vTaskDelay((ms))
#define SleepS(s) vTaskDelay(((s)*1000))

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

typedef SemaphoreHandle_t Mutex;
class AutoMutex {
public:
    // 构造时加锁
    explicit AutoMutex(Mutex& mutex) : _mutex(mutex) {
        xSemaphoreTake(_mutex, portMAX_DELAY);
    }

    // 析构时自动解锁
    ~AutoMutex() {
        xSemaphoreGive(_mutex);
    }

    // 禁止拷贝，防止重复解锁
    AutoMutex(const AutoMutex&) = delete;
    AutoMutex& operator=(const AutoMutex&) = delete;

private:
    Mutex& _mutex;
};

}
}