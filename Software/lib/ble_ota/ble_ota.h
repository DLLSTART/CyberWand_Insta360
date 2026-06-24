#pragma once
#include <Arduino.h>
#include <stdint.h>

#include "base.h"

class BLEServer;
class BLECharacteristic;

namespace cw {
namespace ble_ota {

// 固件版本 (语义化版本, 构建时确定)
// 格式: major.minor.patch 编码为 3 字节, 便于 BLE 传输和比较
struct FwVersion {
    uint8_t major;
    uint8_t minor;
    uint8_t patch;
};

// 当前固件版本 - 每次发布新版本时修改此处
constexpr FwVersion kCurrentVersion = {1, 0, 0};

/// OTA 状态码
enum class OtaStatus : uint8_t {
    kIdle       = 0x00,
    kReady      = 0x01,
    kReceiving  = 0x02,
    kSuccess    = 0x03,
    kErrBegin   = 0xE0,
    kErrWrite   = 0xE1,
    kErrEnd     = 0xE2,
    kErrSize    = 0xE3,
    kErrAbort   = 0xE4,
};

/// 控制命令
enum class OtaCmd : uint8_t {
    kStart = 0x01,  // payload: [4B firmware_size LE]
    kEnd   = 0x02,
    kAbort = 0x03,
};

class BleOta : public base::Singleton<BleOta> {
    friend class base::Singleton<BleOta>;

public:
    void Init(BLEServer* server);
    bool IsOtaInProgress() const { return m_in_progress; }
    static void ConfirmIfPendingVerification();

private:
    BleOta() = default;

    void OnControlWrite(const uint8_t* data, size_t len);
    void OnDataWrite(const uint8_t* data, size_t len);
    void NotifyStatus(OtaStatus status, uint32_t extra = 0);
    void Abort();

    class ControlCallbacks;
    class DataCallbacks;

    BLECharacteristic* m_ctrl_char    = nullptr;
    BLECharacteristic* m_data_char    = nullptr;
    BLECharacteristic* m_status_char  = nullptr;
    BLECharacteristic* m_version_char = nullptr;  // 版本号只读

    bool     m_inited       = false;
    bool     m_in_progress  = false;
    uint32_t m_fw_size      = 0;
    uint32_t m_received     = 0;
    uint32_t m_ota_handle   = 0;
    const void* m_update_partition = nullptr;
    uint32_t m_last_notified_pct = 0;
};

}  // namespace ble_ota
}  // namespace cw
