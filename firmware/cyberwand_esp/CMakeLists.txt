# ESP-IDF CMake 项目配置 - CyberWand

cmake_minimum_required(VERSION 3.16)

# 设置目标芯片为 ESP32-C6
set(IDF_TARGET "esp32c6")

# 包含 ESP-IDF 构建系统
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# 项目名称
project(cyberwand VERSION 3.0.0 LANGUAGES C CXX ASM)

# 组件依赖
idf_component_register(
    SRCS 
        "main/cyberwand_main.c"
        "main/mpu6050.c"
        "main/usb_serial.c"
        "main/ble_comm.c"
        "main/button.c"
        "main/led.c"
        "main/pose_model.c"
    INCLUDE_DIRS 
        "main"
    REQUIRES 
        driver
        freertos
        esp_timer
        nvs_flash
        bt
)

# 编译选项
target_compile_options(cyberwand PRIVATE
    -Wall
    -Wextra
)

# 启用浮点运算优化 (姿态识别需要)
target_compile_options(cyberwand PRIVATE
    -ffast-math
)

# 调试选项
if(CONFIG_LOG_DEFAULT_LEVEL_DEBUG)
    target_compile_definitions(cyberwand PRIVATE
        DEBUG=1
    )
endif()
