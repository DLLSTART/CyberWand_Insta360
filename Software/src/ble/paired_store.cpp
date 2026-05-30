#include "paired_store.h"
#include <string.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_timer.h"

static const char* TAG = "paired";

namespace cw {
namespace ble {

namespace {
constexpr const char* kNvsNamespace = "cw_paired";
constexpr const char* kNvsKeyLast   = "last";
constexpr const char* kNvsKeyValid  = "valid";
}

void PairedStore::Init() {
    if (m_inited) return;
    LoadFromNvs();
    m_inited = true;
}

void PairedStore::LoadFromNvs() {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(kNvsNamespace, NVS_READONLY, &handle);
    if (err != ESP_OK) {
        ESP_LOGI(TAG, "NVS open(ro, ns=%s) failed -> treat as unpaired", kNvsNamespace);
        m_valid = false;
        return;
    }

    uint8_t valid = 0;
    nvs_get_u8(handle, kNvsKeyValid, &valid);

    size_t blen = 0;
    nvs_get_blob(handle, kNvsKeyLast, nullptr, &blen);

    if (valid && blen >= sizeof(PairedRecord)) {
        nvs_get_blob(handle, kNvsKeyLast, &m_record, &blen);
        m_valid = true;
        ESP_LOGI(TAG, "NVS load OK: token=%c%c%c%c%c%c mac_valid=%u",
                 m_record.token[0], m_record.token[1], m_record.token[2],
                 m_record.token[3], m_record.token[4], m_record.token[5],
                 (unsigned)m_record.mac_valid);
    } else {
        ESP_LOGI(TAG, "NVS load: no record (valid=%u blen=%u)", (unsigned)valid, (unsigned)blen);
        m_valid = false;
    }
    nvs_close(handle);
}

void PairedStore::SaveToNvs() const {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(kNvsNamespace, NVS_READWRITE, &handle);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "NVS open(rw) FAILED, paired record NOT persisted");
        return;
    }

    uint8_t valid = m_valid ? 1 : 0;
    nvs_set_u8(handle, kNvsKeyValid, valid);

    if (m_valid) {
        err = nvs_set_blob(handle, kNvsKeyLast, &m_record, sizeof(PairedRecord));
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "NVS save blob failed: %s", esp_err_to_name(err));
        } else {
            nvs_commit(handle);
            ESP_LOGI(TAG, "NVS save OK: token=%c%c%c%c%c%c",
                     m_record.token[0], m_record.token[1], m_record.token[2],
                     m_record.token[3], m_record.token[4], m_record.token[5]);
        }
    } else {
        nvs_erase_key(handle, kNvsKeyLast);
        nvs_commit(handle);
        ESP_LOGI(TAG, "NVS save: record cleared");
    }
    nvs_close(handle);
}

void PairedStore::Save(const uint8_t token[6], const uint8_t mac[6], bool mac_valid) {
    if (token == nullptr) {
        ESP_LOGW(TAG, "Save drop: token is null");
        return;
    }
    memcpy(m_record.token, token, 6);
    if (mac_valid && mac != nullptr) {
        memcpy(m_record.mac, mac, 6);
        m_record.mac_valid = 1;
    } else {
        memset(m_record.mac, 0, 6);
        m_record.mac_valid = 0;
    }
    m_record.last_link_ms = (uint32_t)(esp_timer_get_time() / 1000);
    m_valid = true;
    SaveToNvs();
}

void PairedStore::Forget() {
    ESP_LOGI(TAG, "Forget: clear paired record");
    memset(&m_record, 0, sizeof(m_record));
    m_valid = false;
    SaveToNvs();
}

}
}
