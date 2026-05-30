#include "ble_remote.h"

#include <string.h>

#include "esp_log.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gatts_api.h"
#include "esp_gap_ble_api.h"
#include "esp_gatt_common_api.h"
#include "esp_timer.h"

#include "remote_frame.h"
#include "paired_store.h"
#include "command_codec.h"
#include "protocol_config.h"

static const char* TAG = "ble";

namespace cw {
namespace ble {

// UUIDs (16-bit)
static const uint16_t kServiceUuid = cfg::kRemoteServiceUuid16;
static const uint16_t kNotifyUuid  = cfg::kRemoteNotifyUuid16;
static const uint16_t kWriteUuid   = cfg::kRemoteWriteUuid16;

// Attribute handle indices (for tracking creation order)
static const uint16_t kIdxSvc          = 0;
static const uint16_t kIdxNotifyChar   = 1;
static const uint16_t kIdxNotifyVal    = 2;
static const uint16_t kIdxNotifyCccd   = 3;
static const uint16_t kIdxWriteChar    = 4;
static const uint16_t kIdxWriteVal     = 5;
static const uint16_t kIdxNb           = 6;

static uint16_t g_attr_tab[kIdxNb] = {0};

// CCCD value from peer (for notify enable tracking)
static uint16_t g_cccd_val = 0;

// Adv complete flag
static bool g_adv_config_done = false;

// --- Static trampolines ---

static void gatts_event_handler(esp_gatts_cb_event_t event,
                                 esp_gatt_if_t gatts_if,
                                 esp_ble_gatts_cb_param_t* param) {
    BleRemote::GetInstance().OnGattEvent(event, gatts_if, param);
}

static void gap_event_handler(esp_gap_ble_cb_event_t event,
                               esp_ble_gap_cb_param_t* param) {
    BleRemote::GetInstance().OnGapEvent(event, param);
}

// --- Advertising helpers ---

static esp_ble_adv_data_t make_adv_normal() {
    esp_ble_adv_data_t adv = {};
    adv.set_scan_rsp = false;
    adv.include_name = true;
    adv.include_txpower = false;
    adv.min_interval = 0x06;
    adv.max_interval = 0x12;
    adv.appearance = 0x00;
    adv.manufacturer_len = 0;
    adv.p_manufacturer_data = nullptr;
    adv.service_data_len = 0;
    adv.p_service_data = nullptr;
    adv.service_uuid_len = 0;
    adv.p_service_uuid = nullptr;
    adv.flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT);
    return adv;
}

static esp_ble_adv_data_t make_scan_rsp() {
    esp_ble_adv_data_t rsp = {};
    rsp.set_scan_rsp = true;
    rsp.include_name = true;
    rsp.include_txpower = false;
    uint8_t svc_uuid[2] = {
        (uint8_t)(kServiceUuid & 0xFF),
        (uint8_t)(kServiceUuid >> 8)
    };
    rsp.service_uuid_len = 2;
    rsp.p_service_uuid = svc_uuid;
    rsp.flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT);
    return rsp;
}

static esp_ble_adv_params_t kAdvParams = {
    .adv_int_min        = 0x0020,
    .adv_int_max        = 0x0040,
    .adv_type           = ADV_TYPE_IND,
    .own_addr_type      = BLE_ADDR_TYPE_PUBLIC,
    .peer_addr          = {0},
    .peer_addr_type     = BLE_ADDR_TYPE_PUBLIC,
    .channel_map        = ADV_CHNL_ALL,
    .adv_filter_policy  = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

// --- Init ---

void BleRemote::Init() {
    if (m_inited) return;
    PairedStore::GetInstance().Init();

    // Release classic BT memory (we only use BLE)
    esp_err_t ret = esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "bt mem release classic: %s", esp_err_to_name(ret));
    }

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ret = esp_bt_controller_init(&bt_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bt_controller_init failed: %s", esp_err_to_name(ret));
        return;
    }
    ret = esp_bt_controller_enable(ESP_BT_MODE_BLE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bt_controller_enable failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_bluedroid_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bluedroid_init failed: %s", esp_err_to_name(ret));
        return;
    }
    ret = esp_bluedroid_enable();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bluedroid_enable failed: %s", esp_err_to_name(ret));
        return;
    }

    // Set device name
    esp_ble_gap_set_device_name(cfg::kRemoteGapName);

    // Register callbacks
    esp_ble_gatts_register_callback(gatts_event_handler);
    esp_ble_gap_register_callback(gap_event_handler);

    // Register GATTS app (triggers ESP_GATTS_REG_EVT)
    esp_ble_gatts_app_register(0);

    ESP_LOGI(TAG, "Init: BLE stack started, registering GATTS app");
}

// --- GATTS event handler ---

void BleRemote::OnGattEvent(uint16_t event, esp_gatt_if_t gatts_if, void* raw_param) {
    auto* param = (esp_ble_gatts_cb_param_t*)raw_param;

    switch (event) {
    case ESP_GATTS_REG_EVT: {
        m_gatts_if = gatts_if;  // IDF 6.0.1: gatts_if from callback parameter

        // Create service
        esp_gatt_srvc_id_t svc_id = {};
        svc_id.is_primary = true;
        svc_id.id.inst_id = 0;
        svc_id.id.uuid.len = ESP_UUID_LEN_16;
        svc_id.id.uuid.uuid.uuid16 = kServiceUuid;

        esp_ble_gatts_create_service(m_gatts_if, &svc_id, 20);
        break;
    }

    case ESP_GATTS_CREATE_EVT: {
        m_service_handle = param->create.service_handle;
        ESP_LOGI(TAG, "service created, handle=%d", m_service_handle);

        // Add Notify characteristic (properties: READ | NOTIFY)
        esp_bt_uuid_t notify_uuid = {};
        notify_uuid.len = ESP_UUID_LEN_16;
        notify_uuid.uuid.uuid16 = kNotifyUuid;

        esp_gatt_perm_t notify_perm = ESP_GATT_PERM_READ;
        esp_gatt_char_prop_t notify_prop = ESP_GATT_CHAR_PROP_BIT_READ |
                                          ESP_GATT_CHAR_PROP_BIT_NOTIFY;

        esp_attr_value_t notify_val = {};
        uint8_t notify_init[240] = {0};
        notify_val.attr_max_len = sizeof(notify_init);
        notify_val.attr_len = 0;
        notify_val.attr_value = notify_init;

        esp_ble_gatts_add_char(m_service_handle, &notify_uuid,
                               notify_perm, notify_prop, &notify_val, nullptr);
        break;
    }

    case ESP_GATTS_ADD_CHAR_EVT: {
        uint16_t char_uuid = param->add_char.char_uuid.uuid.uuid16;
        if (char_uuid == kNotifyUuid) {
            g_attr_tab[kIdxNotifyVal] = param->add_char.attr_handle;
            m_notify_handle = param->add_char.attr_handle;
            ESP_LOGI(TAG, "notify char added, handle=%d", m_notify_handle);

            // Add CCCD descriptor (0x2902)
            esp_bt_uuid_t cccd_uuid = {};
            cccd_uuid.len = ESP_UUID_LEN_16;
            cccd_uuid.uuid.uuid16 = 0x2902;

            esp_ble_gatts_add_char_descr(m_service_handle, &cccd_uuid,
                                          ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
                                          nullptr, nullptr);
        } else if (char_uuid == kWriteUuid) {
            g_attr_tab[kIdxWriteVal] = param->add_char.attr_handle;
            m_write_handle = param->add_char.attr_handle;
            ESP_LOGI(TAG, "write char added, handle=%d", m_write_handle);

            // All characteristics added — start service
            esp_ble_gatts_start_service(m_service_handle);
        }
        break;
    }

    case ESP_GATTS_ADD_CHAR_DESCR_EVT: {
        g_attr_tab[kIdxNotifyCccd] = param->add_char_descr.attr_handle;
        ESP_LOGI(TAG, "CCCD descriptor added, handle=%d",
                 param->add_char_descr.attr_handle);

        // Now add Write characteristic (properties: WRITE | WRITE_NR)
        esp_bt_uuid_t write_uuid = {};
        write_uuid.len = ESP_UUID_LEN_16;
        write_uuid.uuid.uuid16 = kWriteUuid;

        esp_gatt_perm_t write_perm = ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE;
        esp_gatt_char_prop_t write_prop = ESP_GATT_CHAR_PROP_BIT_WRITE |
                                           ESP_GATT_CHAR_PROP_BIT_WRITE_NR;

        esp_attr_value_t write_val = {};
        uint8_t write_init[240] = {0};
        write_val.attr_max_len = sizeof(write_init);
        write_val.attr_len = 0;
        write_val.attr_value = write_init;

        esp_ble_gatts_add_char(m_service_handle, &write_uuid,
                               write_perm, write_prop, &write_val, nullptr);
        break;
    }

    case ESP_GATTS_START_EVT: {
        ESP_LOGI(TAG, "service started");
        ApplyCurrentAdvertisement();
        StartAdvertising();
        m_inited = true;

        if (PairedStore::GetInstance().Has()) {
            const auto& paired = PairedStore::GetInstance().Get();
            ESP_LOGI(TAG, "Init OK as \"%s\" (paired, token=%c%c%c%c%c%c)",
                     cfg::kRemoteGapName,
                     paired.token[0], paired.token[1], paired.token[2],
                     paired.token[3], paired.token[4], paired.token[5]);
        } else {
            ESP_LOGI(TAG, "Init OK as \"%s\" (unpaired, normal adv)",
                     cfg::kRemoteGapName);
        }
        break;
    }

    case ESP_GATTS_CONNECT_EVT: {
        m_conn_id = param->connect.conn_id;
        HandleConnected(param->connect.remote_bda);
        break;
    }

    case ESP_GATTS_DISCONNECT_EVT: {
        HandleDisconnected();
        break;
    }

    case ESP_GATTS_WRITE_EVT: {
        if (param->write.handle == g_attr_tab[kIdxNotifyCccd]) {
            // CCCD write from peer
            if (param->write.len >= 2) {
                g_cccd_val = param->write.value[0] | (param->write.value[1] << 8);
                ESP_LOGI(TAG, "CCCD written: 0x%04X", g_cccd_val);
            }
        } else if (param->write.handle == g_attr_tab[kIdxWriteVal]) {
            // Data write from peer
            Write(param->write.value, param->write.len);
        }

        // Send response for write-with-response
        if (!param->write.is_prep) {
            esp_ble_gatts_send_response(m_gatts_if, param->write.conn_id,
                                         param->write.trans_id,
                                         ESP_GATT_OK, nullptr);
        }
        break;
    }

    case ESP_GATTS_MTU_EVT: {
        ESP_LOGI(TAG, "MTU negotiated: %d", param->mtu.mtu);
        break;
    }

    default:
        break;
    }
}

// --- GAP event handler ---

void BleRemote::OnGapEvent(uint16_t event, void* /*raw_param*/) {
    switch (event) {
    case ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT:
        g_adv_config_done = true;
        esp_ble_gap_start_advertising(&kAdvParams);
        break;

    case ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT:
        g_adv_config_done = true;
        esp_ble_gap_start_advertising(&kAdvParams);
        break;

    case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        ESP_LOGI(TAG, "advertising started (%s mode)",
                 m_current_adv_mode == AdvMode::Wakeup ? "wakeup" : "normal");
        break;

    case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        ESP_LOGI(TAG, "advertising stopped");
        break;

    default:
        break;
    }
}

// --- Advertising ---

void BleRemote::ApplyCurrentAdvertisement() {
    if (PairedStore::GetInstance().Has()) {
        m_current_adv_mode = AdvMode::Wakeup;
    } else {
        m_current_adv_mode = AdvMode::Normal;
    }
    m_last_rotate_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ApplyAdvertisementPayload(m_current_adv_mode);
}

void BleRemote::ApplyAdvertisementPayload(AdvMode mode) {
    g_adv_config_done = false;

    auto& store = PairedStore::GetInstance();
    const bool can_wakeup = (mode == AdvMode::Wakeup) && store.Has();

    if (can_wakeup) {
        // Wakeup mode: manufacturer data in adv
        uint8_t mfr[64] = {0};
        const auto& paired = store.Get();
        size_t mfr_len = CommandCodec::BuildWakeupAdvManufacturerData(
            paired.token, mfr, sizeof(mfr));
        if (mfr_len == 0) {
            ESP_LOGE(TAG, "BuildWakeupAdvManufacturerData failed");
            return;
        }

        esp_ble_adv_data_t adv = {};
        adv.set_scan_rsp = false;
        adv.include_name = true;
        adv.manufacturer_len = mfr_len;
        adv.p_manufacturer_data = mfr;
        adv.flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT);
        esp_ble_gap_config_adv_data(&adv);
    } else {
        // Normal mode: name in adv
        esp_ble_adv_data_t adv = make_adv_normal();
        esp_ble_gap_config_adv_data(&adv);
    }
}

void BleRemote::StartAdvertising() {
    if (g_adv_config_done) {
        esp_ble_gap_start_advertising(&kAdvParams);
    }
    // If not done yet, the GAP_ADV_DATA_SET_COMPLETE callback will start it
}

void BleRemote::SwitchAdvByTick() {
    if (!m_inited || m_connected) return;
    if (!PairedStore::GetInstance().Has()) return;

    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    if ((now - m_last_rotate_ms) < cfg::kWakeupAdvRotatePeriodMs) return;
    m_last_rotate_ms = now;

    m_current_adv_mode = (m_current_adv_mode == AdvMode::Normal)
                       ? AdvMode::Wakeup : AdvMode::Normal;

    esp_ble_gap_stop_advertising();
    ApplyAdvertisementPayload(m_current_adv_mode);
}

// --- Business commands ---

bool BleRemote::PushNotify(const uint8_t* buf, size_t n, const char* tag) {
    if (!m_inited) {
        ESP_LOGW(TAG, "notify %s drop: not inited", tag ? tag : "?");
        return false;
    }
    if (!m_connected) {
        ESP_LOGW(TAG, "notify %s drop: not connected", tag ? tag : "?");
        return false;
    }
    if (buf == nullptr || n == 0) {
        ESP_LOGW(TAG, "notify %s drop: empty data", tag ? tag : "?");
        return false;
    }

    // Set attribute value and send indication (notify)
    esp_ble_gatts_set_attr_value(m_notify_handle, n, buf);
    esp_err_t ret = esp_ble_gatts_send_indicate(
        m_gatts_if, m_conn_id, m_notify_handle,
        n, const_cast<uint8_t*>(buf), false /* no confirm */);

    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "notify %s OK (%u bytes)", tag ? tag : "?", (unsigned)n);
        return true;
    }
    ESP_LOGW(TAG, "notify %s FAILED: %s", tag ? tag : "?", esp_err_to_name(ret));
    return false;
}

bool BleRemote::SendRecordStart() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildRecordStartFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "RecordStart");
}

bool BleRemote::SendRecordStop() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildRecordStopFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "RecordStop");
}

bool BleRemote::CycleToNextSubMode() {
    if (cfg::kModeSwitchSeqLen == 0) return false;
    uint8_t sub_mode = m_mode_rotator.NextSubMode();

    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildSetModeFrame(sub_mode, buf, sizeof(buf));
    return PushNotify(buf, n, "SetMode");
}

bool BleRemote::SendHighlightMark() {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildHighlightMarkFrame(buf, sizeof(buf));
    return PushNotify(buf, n, "Mark");
}

bool BleRemote::SendButton(uint8_t device_id, uint8_t button_id, uint8_t state) {
    uint8_t buf[64] = {0};
    size_t n = CommandCodec::BuildButtonFrame(device_id, button_id, state,
                                               buf, sizeof(buf));
    return PushNotify(buf, n, "Button");
}

// --- Connection events ---

void BleRemote::HandleConnected(const uint8_t peer_addr[6]) {
    m_connected = true;
    if (peer_addr) memcpy(m_peer_addr, peer_addr, 6);
    ESP_LOGI(TAG, "connected: %02X:%02X:%02X:%02X:%02X:%02X",
             m_peer_addr[0], m_peer_addr[1], m_peer_addr[2],
             m_peer_addr[3], m_peer_addr[4], m_peer_addr[5]);
}

void BleRemote::HandleDisconnected() {
    ESP_LOGI(TAG, "disconnected from %02X:%02X:%02X:%02X:%02X:%02X",
             m_peer_addr[0], m_peer_addr[1], m_peer_addr[2],
             m_peer_addr[3], m_peer_addr[4], m_peer_addr[5]);
    m_connected = false;
    g_cccd_val = 0;
    ApplyCurrentAdvertisement();
    StartAdvertising();
}

// --- Write handler ---

void BleRemote::Write(const uint8_t* data, size_t len) {
    if (data == nullptr || len < RemoteFrame::HeaderLength()) {
        ESP_LOGW(TAG, "write drop: bad input (len=%u)", (unsigned)len);
        return;
    }
    InboundFrame frame{};
    if (!RemoteFrame::DecodeInboundFrame(data, len, frame)) {
        ESP_LOGW(TAG, "write header mismatch");
        return;
    }
    ESP_LOGI(TAG, "write: cmd=0x%02X end=%d sn=%u size=%u",
             frame.cmd, frame.end ? 1 : 0,
             (unsigned)frame.sn, (unsigned)frame.size);

    if (frame.cmd == cfg::kCmdRxPeerToken) {
        if (frame.size != cfg::kFramePeerTokenPayloadLen || frame.data == nullptr) {
            ESP_LOGW(TAG, "peer-token bad size=%u", (unsigned)frame.size);
            return;
        }
        PairedStore::GetInstance().Save(frame.data, m_peer_addr, true);
        ApplyCurrentAdvertisement();
        ESP_LOGI(TAG, "paired: token=%c%c%c%c%c%c",
                 frame.data[0], frame.data[1], frame.data[2],
                 frame.data[3], frame.data[4], frame.data[5]);
        return;
    }

    if (frame.cmd == cfg::kCmdRxShutdown || frame.cmd == cfg::kCmdRxDisconnect) {
        ESP_LOGI(TAG, "peer cmd=0x%02X (ignored)", frame.cmd);
        return;
    }

    ESP_LOGI(TAG, "unhandled cmd=0x%02X", frame.cmd);
}

}
}
