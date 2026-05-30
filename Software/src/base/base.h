#pragma once

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_timer.h"

// Logging macros: tag-based ESP_LOGI, printf-style
#define ILOGN(msg)         ESP_LOGI("cw", "%s", msg)
#define ILOGT(fmt, ...)    ESP_LOGI("cw", fmt, ##__VA_ARGS__)

// Sleep macros: use FreeRTOS vTaskDelay with proper tick conversion
#define SleepMs(ms) vTaskDelay(pdMS_TO_TICKS(ms))
#define SleepS(s)   vTaskDelay(pdMS_TO_TICKS((s)*1000))

// millis() replacement
static inline uint32_t get_millis() {
    return (uint32_t)(esp_timer_get_time() / 1000);
}

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
    explicit AutoMutex(Mutex& mutex) : _mutex(mutex) {
        xSemaphoreTake(_mutex, portMAX_DELAY);
    }

    ~AutoMutex() {
        xSemaphoreGive(_mutex);
    }

    AutoMutex(const AutoMutex&) = delete;
    AutoMutex& operator=(const AutoMutex&) = delete;

private:
    Mutex& _mutex;
};

}
}
