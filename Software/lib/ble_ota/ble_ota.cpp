#include "ble_ota.h"

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <esp_ota_ops.h>
#include <esp_partition.h>
#include <esp_app_format.h>

namespace cw {
namespace ble_ota {

static constexpr uint16_t kOtaServiceUuid  = 0xFE00;
static constexpr uint16_t kOtaCtrlUuid     = 0xFE01;
static constexpr uint16_t kOtaDataUuid     = 0xFE02;
static constexpr uint16_t kOtaStatusUuid   = 0xFE03;
static constexpr uint16_t kOtaVersionUuid  = 0xFE04;

// =============================================================================
// Callbacks
// =============================================================================

class BleOta::ControlCallbacks : public BLECharacteristicCallbacks {
public:
    explicit ControlCallbacks(BleOta* owner) : m_owner(owner) {}
    void onWrite(BLECharacteristic* ch) override {
        std::string v = ch->getValue();
        m_owner->OnControlWrite(
            reinterpret_cast<const uint8_t*>(v.data()), v.size());
    }
private:
    BleOta* m_owner;
};

class BleOta::DataCallbacks : public BLECharacteristicCallbacks {
public:
    explicit DataCallbacks(BleOta* owner) : m_owner(owner) {}
    void onWrite(BLECharacteristic* ch) override {
        std::string v = ch->getValue();
        m_owner->OnDataWrite(
            reinterpret_cast<const uint8_t*>(v.data()), v.size());
    }
private:
    BleOta* m_owner;
};

// =============================================================================
// Init
// =============================================================================

void BleOta::Init(BLEServer* server) {
    if (m_inited || server == nullptr) return;

    BLEService* svc = server->createService(BLEUUID(kOtaServiceUuid));
    if (!svc) {
        ILOGN("[ota] createService failed");
        return;
    }

    m_ctrl_char = svc->createCharacteristic(
        BLEUUID(kOtaCtrlUuid),
        BLECharacteristic::PROPERTY_WRITE);
    m_ctrl_char->setCallbacks(new ControlCallbacks(this));

    m_data_char = svc->createCharacteristic(
        BLEUUID(kOtaDataUuid),
        BLECharacteristic::PROPERTY_WRITE_NR);
    m_data_char->setCallbacks(new DataCallbacks(this));

    m_status_char = svc->createCharacteristic(
        BLEUUID(kOtaStatusUuid),
        BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ);
    m_status_char->addDescriptor(new BLE2902());

    m_version_char = svc->createCharacteristic(
        BLEUUID(kOtaVersionUuid),
        BLECharacteristic::PROPERTY_READ);
    uint8_t ver[3] = {kCurrentVersion.major, kCurrentVersion.minor, kCurrentVersion.patch};
    m_version_char->setValue(ver, 3);

    svc->start();
    m_inited = true;
    ILOGT("[ota] OTA service ready (v%d.%d.%d)\n",
          kCurrentVersion.major, kCurrentVersion.minor, kCurrentVersion.patch);
}

// =============================================================================
// Control
// =============================================================================

void BleOta::OnControlWrite(const uint8_t* data, size_t len) {
    if (len < 1) return;
    OtaCmd cmd = static_cast<OtaCmd>(data[0]);

    switch (cmd) {
    case OtaCmd::kStart: {
        if (m_in_progress) {
            ILOGN("[ota] START rejected: already in progress");
            return;
        }
        if (len < 5) {
            ILOGN("[ota] START rejected: payload too short");
            NotifyStatus(OtaStatus::kErrSize);
            return;
        }
        m_fw_size = data[1] | (data[2] << 8) | (data[3] << 16) | (data[4] << 24);
        if (m_fw_size == 0 || m_fw_size > 0x640000) {
            ILOGT("[ota] START rejected: invalid size=%u\n", m_fw_size);
            NotifyStatus(OtaStatus::kErrSize);
            return;
        }
        const esp_partition_t* part = esp_ota_get_next_update_partition(NULL);
        if (!part) {
            ILOGN("[ota] no update partition found");
            NotifyStatus(OtaStatus::kErrBegin);
            return;
        }
        m_update_partition = part;

        esp_ota_handle_t handle = 0;
        esp_err_t err = esp_ota_begin(part, m_fw_size, &handle);
        if (err != ESP_OK) {
            ILOGT("[ota] esp_ota_begin err=0x%x\n", err);
            NotifyStatus(OtaStatus::kErrBegin);
            return;
        }
        m_ota_handle = handle;
        m_received = 0;
        m_last_notified_pct = 0;
        m_in_progress = true;
        NotifyStatus(OtaStatus::kReady);
        ILOGT("[ota] START accepted, fw_size=%u, partition=%s\n",
              m_fw_size, part->label);
        break;
    }
    case OtaCmd::kEnd: {
        if (!m_in_progress) {
            ILOGN("[ota] END ignored: no OTA in progress");
            return;
        }
        ILOGT("[ota] END received, received=%u/%u\n", m_received, m_fw_size);
        esp_err_t err = esp_ota_end(static_cast<esp_ota_handle_t>(m_ota_handle));
        if (err != ESP_OK) {
            ILOGT("[ota] esp_ota_end FAILED err=0x%x\n", err);
            NotifyStatus(OtaStatus::kErrEnd);
            Abort();
            return;
        }
        err = esp_ota_set_boot_partition(
            static_cast<const esp_partition_t*>(m_update_partition));
        if (err != ESP_OK) {
            ILOGT("[ota] esp_ota_set_boot_partition FAILED err=0x%x\n", err);
            NotifyStatus(OtaStatus::kErrEnd);
            Abort();
            return;
        }
        m_in_progress = false;
        NotifyStatus(OtaStatus::kSuccess);
        ILOGN("[ota] SUCCESS, rebooting in 1s...");
        delay(1000);
        esp_restart();
        break;
    }
    case OtaCmd::kAbort:
        ILOGN("[ota] ABORT commanded by peer");
        NotifyStatus(OtaStatus::kErrAbort);
        Abort();
        break;
    default:
        ILOGT("[ota] unknown cmd=0x%02x\n", data[0]);
        break;
    }
}

// =============================================================================
// Data
// =============================================================================

void BleOta::OnDataWrite(const uint8_t* data, size_t len) {
    if (!m_in_progress || len == 0) return;

    esp_err_t err = esp_ota_write(
        static_cast<esp_ota_handle_t>(m_ota_handle), data, len);
    if (err != ESP_OK) {
        ILOGT("[ota] esp_ota_write FAILED err=0x%x at offset=%u\n", err, m_received);
        NotifyStatus(OtaStatus::kErrWrite);
        Abort();
        return;
    }
    m_received += len;

    // Notify progress every ~10%
    uint32_t pct = (m_received * 100) / m_fw_size;
    if (pct >= m_last_notified_pct + 10 || m_received >= m_fw_size) {
        m_last_notified_pct = pct;
        NotifyStatus(OtaStatus::kReceiving, pct);
        ILOGT("[ota] progress %u%% (%u/%u)\n", pct, m_received, m_fw_size);
    }
}

// =============================================================================
// Helpers
// =============================================================================

void BleOta::NotifyStatus(OtaStatus status, uint32_t extra) {
    if (!m_status_char) return;
    uint8_t buf[5] = {
        static_cast<uint8_t>(status),
        (uint8_t)(extra & 0xFF),
        (uint8_t)((extra >> 8) & 0xFF),
        (uint8_t)((extra >> 16) & 0xFF),
        (uint8_t)((extra >> 24) & 0xFF)
    };
    m_status_char->setValue(buf, sizeof(buf));
    m_status_char->notify();
}

void BleOta::Abort() {
    if (m_in_progress) {
        esp_ota_abort(static_cast<esp_ota_handle_t>(m_ota_handle));
        ILOGT("[ota] aborted at %u/%u bytes\n", m_received, m_fw_size);
    }
    m_in_progress = false;
    m_received = 0;
    m_fw_size = 0;
    m_ota_handle = 0;
    m_update_partition = nullptr;
    m_last_notified_pct = 0;
}

void BleOta::ConfirmIfPendingVerification() {
    const esp_partition_t* running = esp_ota_get_running_partition();
    esp_ota_img_states_t state;
    if (esp_ota_get_state_partition(running, &state) == ESP_OK) {
        if (state == ESP_OTA_IMG_PENDING_VERIFY) {
            esp_ota_mark_app_valid_cancel_rollback();
            ILOGN("[ota] new firmware confirmed valid (rollback cancelled)");
        } else {
            ILOGT("[ota] partition state=%d, no confirmation needed\n", (int)state);
        }
    }
}

}  // namespace ble_ota
}  // namespace cw
