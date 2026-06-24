#include "gesture_recorder.h"

#include <Arduino.h>
#include <SPIFFS.h>
#include "MPU6050_6Axis_MotionApps20.h"
#include "board_config.h"
#include "base.h"

// ponytail: DMP quaternion -> SPIFFS binary file, minimal code

namespace cw {
namespace gesture {

static constexpr const char* kFilePath = "/gestures.bin";
static constexpr uint32_t kMagic = 0x31305247;  // "GR01" LE

static MPU6050 s_dmp;  // 与 mpu6050_imu 共享同一物理芯片 (0x68)
static uint8_t s_fifo_buf[64];
static uint16_t s_packet_size = 0;
static bool s_inited = false;
static bool s_dmp_active = false;
static uint16_t s_count = 0;

// ---- File helpers ----

static bool load_count() {
    if (!SPIFFS.exists(kFilePath)) { s_count = 0; return true; }
    File f = SPIFFS.open(kFilePath, "r");
    if (!f) { s_count = 0; return true; }
    uint32_t magic = 0;
    f.read(reinterpret_cast<uint8_t*>(&magic), 4);
    if (magic != kMagic) { f.close(); s_count = 0; return true; }
    f.read(reinterpret_cast<uint8_t*>(&s_count), 2);
    f.close();
    return true;
}

static bool create_file_if_missing() {
    if (SPIFFS.exists(kFilePath)) return true;
    File f = SPIFFS.open(kFilePath, "w");
    if (!f) return false;
    uint32_t magic = kMagic;
    uint16_t zero = 0;
    f.write(reinterpret_cast<uint8_t*>(&magic), 4);
    f.write(reinterpret_cast<uint8_t*>(&zero), 2);
    f.write(reinterpret_cast<uint8_t*>(&zero), 2);
    f.close();
    return true;
}

// ---- Public API ----

bool RecorderInit() {
    if (s_inited) return true;

    if (!SPIFFS.begin(true)) {
        ILOGN("[gesture] SPIFFS mount failed");
        return false;
    }
    if (!create_file_if_missing()) return false;
    load_count();

    // DMP init — Wire 已由 Mpu6050IMU::Init() 启动, 芯片已 initialize+calibrate
    // s_dmp 是独立 MPU6050 对象但指向同一 I2C 地址, dmpInitialize 写 DMP firmware
    uint8_t status = s_dmp.dmpInitialize();
    if (status != 0) {
        ILOGT("[gesture] DMP init failed: %u\n", status);
        return false;
    }
    s_packet_size = s_dmp.dmpGetFIFOPacketSize();
    s_dmp.setDMPEnabled(false);  // 待命, 录制时才启用
    s_inited = true;
    ILOGT("[gesture] RecorderInit OK, %u gestures stored, pkt=%u\n",
          s_count, s_packet_size);
    return true;
}

bool RecorderStart() {
    if (!s_inited) return false;
    s_dmp.resetFIFO();
    s_dmp.setDMPEnabled(true);
    s_dmp_active = true;
    return true;
}

bool RecorderSampleOne(Quat& out) {
    if (!s_dmp_active) return false;
    // 等 FIFO 有一包, 最多 50ms
    uint32_t t0 = millis();
    while (s_dmp.getFIFOCount() < s_packet_size) {
        if ((millis() - t0) > 50) return false;
        vTaskDelay(1);
    }
    if (s_dmp.getFIFOCount() >= 1024) {
        s_dmp.resetFIFO();
        return false;
    }
    s_dmp.getFIFOBytes(s_fifo_buf, s_packet_size);
    Quaternion q;
    s_dmp.dmpGetQuaternion(&q, s_fifo_buf);
    out = {q.w, q.x, q.y, q.z};
    return true;
}

bool RecorderCommit(const Quat* buf, uint16_t n) {
    if (!s_inited || buf == nullptr || n == 0) return false;
    if (s_count >= kMaxGestures) {
        ILOGN("[gesture] storage full (1000)");
        return false;
    }

    s_dmp.setDMPEnabled(false);
    s_dmp_active = false;

    File f = SPIFFS.open(kFilePath, "r+");
    if (!f) {
        ILOGN("[gesture] file open failed");
        return false;
    }

    // 更新 header 中的 count
    uint16_t new_count = s_count + 1;
    f.seek(4);
    f.write(reinterpret_cast<uint8_t*>(&new_count), 2);

    // 追加数据到末尾
    f.seek(0, SeekEnd);
    uint16_t frame_count = n;
    uint16_t reserved = 0;
    f.write(reinterpret_cast<uint8_t*>(&frame_count), 2);
    f.write(reinterpret_cast<uint8_t*>(&reserved), 2);
    f.write(reinterpret_cast<const uint8_t*>(buf), n * sizeof(Quat));
    f.close();

    s_count = new_count;
    ILOGT("[gesture] saved #%u (%u frames)\n", s_count, n);
    return true;
}

uint16_t RecorderCount() {
    return s_count;
}

}  // namespace gesture
}  // namespace cw
