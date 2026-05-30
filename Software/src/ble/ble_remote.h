#pragma once
#include <stdint.h>
#include "esp_gatts_api.h"
#include "esp_gap_ble_api.h"
#include "base.h"
#include "command_codec.h"

namespace cw {
namespace ble {

class BleRemote : public base::Singleton<BleRemote> {
    friend class base::Singleton<BleRemote>;

public:
    void Init();
    void SwitchAdvByTick();
    bool IsConnected() const { return m_connected; }

    bool SendRecordStart();
    bool SendRecordStop();
    bool CycleToNextSubMode();
    bool SendHighlightMark();
    bool SendButton(uint8_t device_id, uint8_t button_id, uint8_t state);

    void OnGattEvent(uint16_t event, esp_gatt_if_t gatts_if, void* param);
    void OnGapEvent(uint16_t event, void* param);

private:
    BleRemote() = default;

    enum class AdvMode { Normal, Wakeup };

    void ApplyCurrentAdvertisement();
    void ApplyAdvertisementPayload(AdvMode mode);
    void StartAdvertising();

    void Write(const uint8_t* data, size_t len);
    void HandleConnected(const uint8_t peer_addr[6]);
    void HandleDisconnected();
    bool PushNotify(const uint8_t* buf, size_t n, const char* tag);

    // Bluedroid state
    uint16_t m_gatts_if       = 0xFF;  // ESP_GATT_IF_NONE
    uint16_t m_service_handle = 0;
    uint16_t m_notify_handle  = 0;
    uint16_t m_write_handle   = 0;
    uint16_t m_conn_id        = 0;

    bool     m_inited       = false;
    bool     m_connected    = false;
    uint8_t  m_peer_addr[6] = {0};

    ModeRotator m_mode_rotator;

    AdvMode  m_current_adv_mode = AdvMode::Normal;
    uint32_t m_last_rotate_ms   = 0;
};

}
}
