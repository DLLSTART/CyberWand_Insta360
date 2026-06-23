#include "ble_remote.h"

#include <string.h>
#include <stdio.h>

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

// ===== Standard BLE UUIDs =====
static const uint16_t HID_SVC      = 0x1812;
static const uint16_t BAT_SVC      = 0x180F;
static const uint16_t DEVINFO_SVC  = 0x180A;
static const uint16_t REPORT_MAP   = 0x2A4B;
static const uint16_t REPORT       = 0x2A4D;
static const uint16_t HID_INFO     = 0x2A4A;
static const uint16_t HID_CTRL_PT  = 0x2A4C;
static const uint16_t PROTO_MODE   = 0x2A4E;
static const uint16_t BOOT_KB_IN   = 0x2A22;
static const uint16_t BAT_LEVEL    = 0x2A19;
static const uint16_t PNP_ID       = 0x2A50;
static const uint16_t MFR_NAME     = 0x2A29;
static const uint16_t CCCD_UUID    = 0x2902;

// ===== Custom BTCTRL service (peer scans for this) =====
// UUIDs come from protocol_config.h.
// The peer hard-codes the matching 128-bit form internally;
// the standard 16-bit expansion is what we register here.
static const uint16_t CUST_SVC     = cfg::kRemoteServiceUuid16;
static const uint16_t CUST_NOTIFY  = cfg::kRemoteNotifyUuid16;
static const uint16_t CUST_WRITE   = cfg::kRemoteWriteUuid16;

// ===== HID Report Map (vendor-defined, 1-byte input) =====
static const uint8_t kRmap[] = {
    0x06, 0x00, 0xFF, 0x09, 0x01, 0xA1, 0x01,
    0x85, 0x01, 0x09, 0x02,
    0x15, 0x00, 0x26, 0xFF, 0x00,
    0x75, 0x08, 0x95, 0x01,
    0x81, 0x02, 0xC0,
};
static const uint8_t kHidInfo[]   = { 0x11, 0x01, 0x00, 0x01 };
static const uint8_t kProtoMode   = 0x01;
// PnP ID: generic remote control. Vendor source 0x01 = BT SIG.
static const uint8_t kPnpIdVal[]  = { 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01 };
static const char    kMfrStr[]    = "CyberWand";
static uint8_t       s_bat        = 85;

// Static attr value backing buffers
static uint8_t b_rmap[sizeof(kRmap)] = {};
static uint8_t b_hinfo[4]            = {};
static uint8_t b_pmode[1]            = {};
static uint8_t b_kbin[8]             = {};
static uint8_t b_report[8]           = {};
static uint8_t b_bat[1]              = {};
static uint8_t b_pnp[7]              = {};
static uint8_t b_mfr[16]             = {};
static uint8_t b_cust_notify[240]    = {};
static uint8_t b_cust_write[240]     = {};

static bool g_adv_ok = false;

static void av_init(esp_attr_value_t* v, const uint8_t* d, uint16_t n,
                    uint8_t* b, uint16_t c) {
    memset(v, 0, sizeof(*v));
    v->attr_max_len = c;
    v->attr_len     = (n > 0 && n <= c) ? n : 1;
    v->attr_value   = b;
    if (d && n > 0 && n <= c) memcpy(b, d, n);
}

static void av_empty(esp_attr_value_t* v, uint8_t* b, uint16_t c) {
    memset(v, 0, sizeof(*v));
    v->attr_max_len = c;
    v->attr_len     = 1;  // non-zero avoids Bluedroid 4.4.7 deep_copy bug
    v->attr_value   = b;
    memset(b, 0, c);
}

static void gatts_cb(esp_gatts_cb_event_t e, esp_gatt_if_t i, esp_ble_gatts_cb_param_t* p) {
    BleRemote::GetInstance().OnGattEvent(e, i, p);
}
static void gap_cb(esp_gap_ble_cb_event_t e, esp_ble_gap_cb_param_t* p) {
    BleRemote::GetInstance().OnGapEvent(e, p);
}

// Advertising — name only, plus HID svc UUID hint (peer uses both
// name match AND HOGP to qualify the device)
static esp_ble_adv_data_t adv_normal() {
    esp_ble_adv_data_t a = {};
    a.set_scan_rsp = false;
    a.include_name = true;
    // Appearance = HID Generic Remote Control (0x0180 / category 0x180-0x183)
    a.appearance = 0x03C0;  // HID Generic
    a.flag = ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT;
    return a;
}

// QC adv: embed PairedStore token (peer SN tail) into manufacturer-data,
// so the peer's standby scanner sees its own SN and initiates connection;
// after wake-up, suffix bytes trigger the QC (Quick Capture) flow.
// Alternates with Normal adv every kQcAdvRotatePeriodMs in the main loop,
// covering both "standby SN-scan wake" and "active remote discovery" modes.
//
// manufacturer-data 字节布局 (由 CommandCodec::BuildQcAdvManufacturerData 拼装):
//   [prefix N B][token 6 B][suffix M B]
// 其中 prefix 已含 CompanyID 2 B (LE).
static uint8_t s_qc_mfr[64] = {0};
static esp_ble_adv_data_t adv_qc(size_t mfr_len) {
    esp_ble_adv_data_t a = {};
    a.set_scan_rsp = false;
    a.include_name = false;             // 31B 广播包紧张, 名字交给 normal adv 那一片
    a.flag = ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT;
    a.p_manufacturer_data = s_qc_mfr;
    a.manufacturer_len = mfr_len;
    return a;
}

static esp_ble_adv_params_t kAdvParams = {
    // Fast adv: 30ms interval — camera re-scans every ~5s after Bt_Restart,
    // we need to be visible immediately when it re-scans.
    .adv_int_min = 0x0030, .adv_int_max = 0x0050, .adv_type = ADV_TYPE_IND,
    .own_addr_type = BLE_ADDR_TYPE_PUBLIC, .peer_addr = {0},
    .peer_addr_type = BLE_ADDR_TYPE_PUBLIC, .channel_map = ADV_CHNL_ALL,
    .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

void BleRemote::Init() {
    if (m_inited) return;
    PairedStore::GetInstance().Init();

    esp_err_t r = esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT);
    if (r != ESP_OK) ESP_LOGW(TAG, "bt mem: %s", esp_err_to_name(r));

    esp_bt_controller_config_t cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    r = esp_bt_controller_init(&cfg);
    if (r != ESP_OK) { ESP_LOGE(TAG, "bt init: %s", esp_err_to_name(r)); return; }
    r = esp_bt_controller_enable(ESP_BT_MODE_BLE);
    if (r != ESP_OK) { ESP_LOGE(TAG, "bt en: %s", esp_err_to_name(r)); return; }
    r = esp_bluedroid_init();
    if (r != ESP_OK) { ESP_LOGE(TAG, "bd init: %s", esp_err_to_name(r)); return; }
    r = esp_bluedroid_enable();
    if (r != ESP_OK) { ESP_LOGE(TAG, "bd en: %s", esp_err_to_name(r)); return; }

    esp_ble_gap_set_device_name(cfg::kRemoteGapName);

    // ★ Peer reissues BLE restart after first connection. Without a
    //   stored Link Key, every reconnect re-runs first-connect → loops.
    //   Enable LE Secure Connections + Bonding so the link key survives.
    esp_ble_auth_req_t ar = ESP_LE_AUTH_REQ_SC_BOND;
    esp_ble_io_cap_t   ic = ESP_IO_CAP_NONE;          // just-works
    uint8_t key_size      = 16;
    uint8_t init_key      = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
    uint8_t rsp_key       = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
    uint8_t auth_option   = ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_DISABLE;
    esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE, &ar, sizeof(ar));
    esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE,      &ic, sizeof(ic));
    esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE,    &key_size, sizeof(key_size));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY,    &init_key, sizeof(init_key));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY,     &rsp_key, sizeof(rsp_key));
    esp_ble_gap_set_security_param(ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH,
                                   &auth_option, sizeof(auth_option));

    esp_ble_gatts_register_callback(gatts_cb);
    esp_ble_gap_register_callback(gap_cb);

    m_svc_step = SvcStep::kHidSvc;
    esp_ble_gatts_app_register(0);
    ESP_LOGI(TAG, "Init: HID + Battery + DevInfo + Custom(FFE0) start");
}

// ============================================================================
// GATTS event handler — 4-service state machine
// ============================================================================
void BleRemote::OnGattEvent(uint16_t e, esp_gatt_if_t gi, void* rp) {
    auto* p = (esp_ble_gatts_cb_param_t*)rp;
    auto st = m_svc_step;
    esp_attr_value_t av;
    esp_bt_uuid_t u;
    esp_err_t r;
    uint16_t h;

    switch (e) {

    case ESP_GATTS_REG_EVT:
        m_gatts_if = gi;
        ESP_LOGI(TAG, "REG gatts_if=%d", gi);
        if (st == SvcStep::kHidSvc) {
            esp_gatt_srvc_id_t s = {};
            s.is_primary = true; s.id.inst_id = 0;
            s.id.uuid.len = ESP_UUID_LEN_16;
            s.id.uuid.uuid.uuid16 = HID_SVC;
            r = esp_ble_gatts_create_service(m_gatts_if, &s, 30);
            ESP_LOGI(TAG, "create HID svc: %s", esp_err_to_name(r));
        }
        break;

    case ESP_GATTS_CREATE_EVT:
        h = p->create.service_handle;
        ESP_LOGI(TAG, "CREATE handle=%d step=%d", h, (int)st);
        u.len = ESP_UUID_LEN_16;

        if (st == SvcStep::kHidSvc) {
            m_hid_svc_handle = h;
            u.uuid.uuid16 = REPORT_MAP;
            av_init(&av, kRmap, sizeof(kRmap), b_rmap, sizeof(b_rmap));
            r = esp_ble_gatts_add_char(h, &u, ESP_GATT_PERM_READ_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_READ, &av, nullptr);
            ESP_LOGI(TAG, "add ReportMap: %s", esp_err_to_name(r));
            m_svc_step = SvcStep::kHidReportMap;
        } else if (st == SvcStep::kBatSvc) {
            m_bat_svc_handle = h;
            s_bat = 85;
            u.uuid.uuid16 = BAT_LEVEL;
            av_init(&av, &s_bat, 1, b_bat, sizeof(b_bat));
            r = esp_ble_gatts_add_char(h, &u, ESP_GATT_PERM_READ,
                    ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY,
                    &av, nullptr);
            ESP_LOGI(TAG, "add BatLevel: %s", esp_err_to_name(r));
            m_svc_step = SvcStep::kBatLevel;
        } else if (st == SvcStep::kDevInfoSvc) {
            m_devinfo_svc_handle = h;
            u.uuid.uuid16 = PNP_ID;
            av_init(&av, kPnpIdVal, sizeof(kPnpIdVal), b_pnp, sizeof(b_pnp));
            r = esp_ble_gatts_add_char(h, &u, ESP_GATT_PERM_READ,
                    ESP_GATT_CHAR_PROP_BIT_READ, &av, nullptr);
            ESP_LOGI(TAG, "add PnpId: %s", esp_err_to_name(r));
            m_svc_step = SvcStep::kPnpId;
        } else if (st == SvcStep::kCustSvc) {
            m_cust_svc_handle = h;
            // Write FIRST in custom service (low handle = preferred by some clients)
            u.uuid.uuid16 = CUST_WRITE;
            av_init(&av, nullptr, 0, b_cust_write, sizeof(b_cust_write));
            r = esp_ble_gatts_add_char(h, &u,
                    ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
                    ESP_GATT_CHAR_PROP_BIT_WRITE | ESP_GATT_CHAR_PROP_BIT_WRITE_NR,
                    &av, nullptr);
            ESP_LOGI(TAG, "add CustWrite 0x%04X: %s", CUST_WRITE, esp_err_to_name(r));
            m_svc_step = SvcStep::kCustWrite;
        }
        break;

    case ESP_GATTS_ADD_CHAR_EVT: {
        uint16_t u16 = p->add_char.char_uuid.uuid.uuid16;
        h = p->add_char.attr_handle;
        ESP_LOGI(TAG, "ADD_CHAR uuid=0x%04X h=%d step=%d", u16, h, (int)st);
        u.len = ESP_UUID_LEN_16;

        // ---- HID service chain ----
        if (st == SvcStep::kHidReportMap && u16 == REPORT_MAP) {
            m_svc_step = SvcStep::kHidInfo;
            u.uuid.uuid16 = HID_INFO;
            av_init(&av, kHidInfo, sizeof(kHidInfo), b_hinfo, sizeof(b_hinfo));
            r = esp_ble_gatts_add_char(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_READ, &av, nullptr);
            ESP_LOGI(TAG, "add HIDInfo: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidInfo && u16 == HID_INFO) {
            m_svc_step = SvcStep::kHidProtocolMode;
            u.uuid.uuid16 = PROTO_MODE;
            av_init(&av, &kProtoMode, 1, b_pmode, sizeof(b_pmode));
            r = esp_ble_gatts_add_char(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED | ESP_GATT_PERM_WRITE_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_WRITE_NR,
                    &av, nullptr);
            ESP_LOGI(TAG, "add ProtoMode: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidProtocolMode && u16 == PROTO_MODE) {
            m_svc_step = SvcStep::kHidBootKbInput;
            u.uuid.uuid16 = BOOT_KB_IN;
            av_empty(&av, b_kbin, sizeof(b_kbin));
            r = esp_ble_gatts_add_char(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY,
                    &av, nullptr);
            ESP_LOGI(TAG, "add BootKbIn: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidBootKbInput && u16 == BOOT_KB_IN) {
            m_hid_kbin_handle = h;
            m_svc_step = SvcStep::kHidBootKbInputCccd;
            u.uuid.uuid16 = CCCD_UUID;
            r = esp_ble_gatts_add_char_descr(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED | ESP_GATT_PERM_WRITE_ENCRYPTED,
                    nullptr, nullptr);
            ESP_LOGI(TAG, "add KBin CCCD: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidReport && u16 == REPORT) {
            m_hid_report_handle = h;
            m_svc_step = SvcStep::kHidReportCccd;
            u.uuid.uuid16 = CCCD_UUID;
            r = esp_ble_gatts_add_char_descr(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED | ESP_GATT_PERM_WRITE_ENCRYPTED,
                    nullptr, nullptr);
            ESP_LOGI(TAG, "add Report CCCD: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidCtrlPoint && u16 == HID_CTRL_PT) {
            m_svc_step = SvcStep::kHidStart;
            r = esp_ble_gatts_start_service(m_hid_svc_handle);
            ESP_LOGI(TAG, "start HID svc: %s", esp_err_to_name(r));

        // ---- Battery service chain ----
        } else if (st == SvcStep::kBatLevel && u16 == BAT_LEVEL) {
            m_bat_level_handle = h;
            m_svc_step = SvcStep::kBatLevelCccd;
            u.uuid.uuid16 = CCCD_UUID;
            r = esp_ble_gatts_add_char_descr(m_bat_svc_handle, &u,
                    ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE, nullptr, nullptr);
            ESP_LOGI(TAG, "add Bat CCCD: %s", esp_err_to_name(r));

        // ---- Device Info service chain ----
        } else if (st == SvcStep::kPnpId && u16 == PNP_ID) {
            m_svc_step = SvcStep::kMfrName;
            u.uuid.uuid16 = MFR_NAME;
            av_init(&av, (const uint8_t*)kMfrStr, strlen(kMfrStr),
                    b_mfr, sizeof(b_mfr));
            r = esp_ble_gatts_add_char(m_devinfo_svc_handle, &u,
                    ESP_GATT_PERM_READ, ESP_GATT_CHAR_PROP_BIT_READ,
                    &av, nullptr);
            ESP_LOGI(TAG, "add MfrName: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kMfrName && u16 == MFR_NAME) {
            m_svc_step = SvcStep::kDevInfoStart;
            r = esp_ble_gatts_start_service(m_devinfo_svc_handle);
            ESP_LOGI(TAG, "start DEVINFO svc: %s", esp_err_to_name(r));

        // ---- Custom service chain ----
        } else if (st == SvcStep::kCustWrite && u16 == CUST_WRITE) {
            m_cust_write_handle = h;
            m_svc_step = SvcStep::kCustNotify;
            u.uuid.uuid16 = CUST_NOTIFY;
            av_init(&av, nullptr, 0, b_cust_notify, sizeof(b_cust_notify));
            r = esp_ble_gatts_add_char(m_cust_svc_handle, &u, ESP_GATT_PERM_READ,
                    ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY,
                    &av, nullptr);
            ESP_LOGI(TAG, "add CustNotify 0x%04X: %s",
                     CUST_NOTIFY, esp_err_to_name(r));
        } else if (st == SvcStep::kCustNotify && u16 == CUST_NOTIFY) {
            m_cust_notify_handle = h;
            m_svc_step = SvcStep::kCustNotifyCccd;
            u.uuid.uuid16 = CCCD_UUID;
            r = esp_ble_gatts_add_char_descr(m_cust_svc_handle, &u,
                    ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE, nullptr, nullptr);
            ESP_LOGI(TAG, "add CustNotify CCCD: %s", esp_err_to_name(r));
        }
        break;
    }

    case ESP_GATTS_ADD_CHAR_DESCR_EVT: {
        uint16_t dh = p->add_char_descr.attr_handle;
        ESP_LOGI(TAG, "ADD_DESCR h=%d step=%d", dh, (int)st);
        u.len = ESP_UUID_LEN_16;

        if (st == SvcStep::kHidBootKbInputCccd) {
            m_hid_kbin_cccd = dh;
            m_svc_step = SvcStep::kHidReport;
            u.uuid.uuid16 = REPORT;
            av_empty(&av, b_report, sizeof(b_report));
            r = esp_ble_gatts_add_char(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_READ_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY,
                    &av, nullptr);
            ESP_LOGI(TAG, "add Report: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kHidReportCccd) {
            m_hid_report_cccd = dh;
            m_svc_step = SvcStep::kHidCtrlPoint;
            u.uuid.uuid16 = HID_CTRL_PT;
            r = esp_ble_gatts_add_char(m_hid_svc_handle, &u,
                    ESP_GATT_PERM_WRITE_ENCRYPTED,
                    ESP_GATT_CHAR_PROP_BIT_WRITE_NR,
                    nullptr, nullptr);
            ESP_LOGI(TAG, "add CtrlPt: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kBatLevelCccd) {
            m_bat_level_cccd = dh;
            m_svc_step = SvcStep::kBatStart;
            r = esp_ble_gatts_start_service(m_bat_svc_handle);
            ESP_LOGI(TAG, "start BAT svc: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kCustNotifyCccd) {
            m_cust_notify_cccd = dh;
            m_svc_step = SvcStep::kCustStart;
            r = esp_ble_gatts_start_service(m_cust_svc_handle);
            ESP_LOGI(TAG, "start CUST svc: %s", esp_err_to_name(r));
        }
        break;
    }

    case ESP_GATTS_START_EVT: {
        ESP_LOGI(TAG, "START handle=%d status=%d step=%d",
                 p->start.service_handle, p->start.status, (int)st);
        if (st == SvcStep::kHidStart) {
            m_svc_step = SvcStep::kBatSvc;
            esp_gatt_srvc_id_t s = {};
            s.is_primary = true; s.id.inst_id = 0;
            s.id.uuid.len = ESP_UUID_LEN_16;
            s.id.uuid.uuid.uuid16 = BAT_SVC;
            r = esp_ble_gatts_create_service(m_gatts_if, &s, 10);
            ESP_LOGI(TAG, "create BAT svc: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kBatStart) {
            m_svc_step = SvcStep::kDevInfoSvc;
            esp_gatt_srvc_id_t s = {};
            s.is_primary = true; s.id.inst_id = 0;
            s.id.uuid.len = ESP_UUID_LEN_16;
            s.id.uuid.uuid.uuid16 = DEVINFO_SVC;
            r = esp_ble_gatts_create_service(m_gatts_if, &s, 10);
            ESP_LOGI(TAG, "create DEVINFO svc: %s", esp_err_to_name(r));
        } else if (st == SvcStep::kDevInfoStart) {
            // Camera scans for the custom service after connect; we MUST expose it
            // (with Write + Notify + CCCD), otherwise the camera
            // logs "write_handle is missing" and every send fails.
            m_svc_step = SvcStep::kCustSvc;
            esp_gatt_srvc_id_t s = {};
            s.is_primary = true; s.id.inst_id = 0;
            s.id.uuid.len = ESP_UUID_LEN_16;
            s.id.uuid.uuid.uuid16 = CUST_SVC;
            r = esp_ble_gatts_create_service(m_gatts_if, &s, 10);
            ESP_LOGI(TAG, "create CUST svc 0x%04X: %s",
                     CUST_SVC, esp_err_to_name(r));
        } else if (st == SvcStep::kCustStart) {
            m_svc_step = SvcStep::kDone;
            ApplyCurrentAdvertisement();
            m_inited = true;
            ESP_LOGI(TAG, "ALL services ready: HID(svc=%d) BAT(svc=%d) "
                          "DEVINFO(svc=%d) CUST(svc=%d notify=%d write=%d)",
                     m_hid_svc_handle, m_bat_svc_handle, m_devinfo_svc_handle,
                     m_cust_svc_handle, m_cust_notify_handle,
                     m_cust_write_handle);
        }
        break;
    }

    case ESP_GATTS_CONNECT_EVT:
        m_conn_id = p->connect.conn_id;
        ESP_LOGI(TAG, ">>> CONNECT_EVT conn_id=%d <<<", m_conn_id);
        HandleConnected(p->connect.remote_bda);
        break;

    case ESP_GATTS_DISCONNECT_EVT:
        ESP_LOGW(TAG, ">>> DISCONNECT_EVT reason=0x%02X <<<",
                 p->disconnect.reason);
        HandleDisconnected();
        break;

    case ESP_GATTS_READ_EVT:
        ESP_LOGI(TAG, "READ h=%d trans=%lu offset=%d need_rsp=%d is_long=%d",
                 p->read.handle, (unsigned long)p->read.trans_id,
                 p->read.offset, p->read.need_rsp, p->read.is_long);
        break;

    case ESP_GATTS_WRITE_EVT: {
        uint16_t wh = p->write.handle;
        ESP_LOGI(TAG, "WRITE h=%d len=%u offset=%d need_rsp=%d is_prep=%d",
                 wh, (unsigned)p->write.len, p->write.offset,
                 p->write.need_rsp, p->write.is_prep);
        if (p->write.len > 0 && p->write.len <= 64) {
            char hex[200] = {0};
            int pos = 0;
            for (uint16_t i = 0; i < p->write.len && pos < 190; ++i) {
                pos += snprintf(hex + pos, sizeof(hex) - pos, "%02X ",
                                p->write.value[i]);
            }
            ESP_LOGI(TAG, "  data: %s", hex);
        }
        if (p->write.len >= 2 &&
            (wh == m_hid_kbin_cccd || wh == m_hid_report_cccd ||
             wh == m_bat_level_cccd || wh == m_cust_notify_cccd)) {
            uint16_t cccd_v = p->write.value[0] | (p->write.value[1] << 8);
            ESP_LOGI(TAG, "  → CCCD h=%d v=0x%04X", wh, cccd_v);
            // When host enables HID input notifications, push a "device alive"
            // empty report so it doesn't idle-timeout the connection.
            if (cccd_v == 0x0001 &&
                (wh == m_hid_kbin_cccd || wh == m_hid_report_cccd)) {
                uint16_t h = (wh == m_hid_kbin_cccd) ? m_hid_kbin_handle
                                                     : m_hid_report_handle;
                uint8_t empty[1] = { 0x00 };
                esp_ble_gatts_send_indicate(m_gatts_if, m_conn_id, h,
                                            sizeof(empty), empty, false);
                ESP_LOGI(TAG, "  pushed HID alive notify on h=%d", h);
            }
        } else if (wh == m_cust_write_handle) {
            Write(p->write.value, p->write.len);
        }
        if (p->write.need_rsp && !p->write.is_prep) {
            esp_ble_gatts_send_response(m_gatts_if, p->write.conn_id,
                                        p->write.trans_id, ESP_GATT_OK, nullptr);
        }
        break;
    }

    case ESP_GATTS_EXEC_WRITE_EVT:
        esp_ble_gatts_send_response(m_gatts_if, p->exec_write.conn_id,
                                    p->exec_write.trans_id, ESP_GATT_OK, nullptr);
        break;

    case ESP_GATTS_CONF_EVT:
        ESP_LOGI(TAG, "CONF (notify ack) h=%d status=%d",
                 p->conf.handle, p->conf.status);
        break;

    case ESP_GATTS_MTU_EVT:
        ESP_LOGI(TAG, "MTU=%d conn_id=%d", p->mtu.mtu, p->mtu.conn_id);
        break;

    default:
        ESP_LOGI(TAG, "GATTS unhandled event=%d", (int)e);
        break;
    }
}

void BleRemote::OnGapEvent(uint16_t e, void* rp) {
    auto* gp = (esp_ble_gap_cb_param_t*)rp;
    switch (e) {
    case ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT:
        ESP_LOGI(TAG, "GAP: ADV_DATA_SET_OK status=%d",
                 gp->adv_data_cmpl.status);
        g_adv_ok = true;
        esp_ble_gap_start_advertising(&kAdvParams);
        break;
    case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        ESP_LOGI(TAG, "GAP: >>> ADV STARTED status=%d <<<",
                 gp->adv_start_cmpl.status);
        break;
    case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        ESP_LOGI(TAG, "GAP: adv stopped"); break;
    case ESP_GAP_BLE_UPDATE_CONN_PARAMS_EVT:
        ESP_LOGI(TAG, "GAP: conn_upd st=%d int=%d lat=%d to=%d",
                 gp->update_conn_params.status,
                 gp->update_conn_params.conn_int,
                 gp->update_conn_params.latency,
                 gp->update_conn_params.timeout);
        break;
    case ESP_GAP_BLE_SEC_REQ_EVT:
        esp_ble_gap_security_rsp(gp->ble_security.ble_req.bd_addr, true);
        break;
    case ESP_GAP_BLE_AUTH_CMPL_EVT:
        ESP_LOGI(TAG, "GAP: AUTH %s reason=0x%02X",
                 gp->ble_security.auth_cmpl.success ? "OK" : "FAIL",
                 gp->ble_security.auth_cmpl.fail_reason);
        break;
    default:
        ESP_LOGI(TAG, "GAP unhandled event=%d", (int)e);
        break;
    }
}

void BleRemote::ApplyCurrentAdvertisement() {
    // 已配对 -> 优先发 QC adv (让相机的扫 SN 唤醒 + Quick Capture 路径生效);
    // 未配对 -> 普通可发现广播.
    m_current_adv_mode = PairedStore::GetInstance().Has()
                       ? AdvMode::Qc
                       : AdvMode::Normal;
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    m_last_rotate_ms = now_ms;
    m_adv_started_ms = now_ms;
    ApplyAdvertisementPayload(m_current_adv_mode);
}

uint32_t BleRemote::GetUnconnectedAdvertisingMs() const {
    if (!m_inited || m_connected || m_adv_started_ms == 0) {
        return 0;
    }
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    return now_ms - m_adv_started_ms;
}

void BleRemote::ApplyAdvertisementPayload(AdvMode mode) {
    g_adv_ok = false;
    if (mode == AdvMode::Qc && PairedStore::GetInstance().Has()) {
        const auto& rec = PairedStore::GetInstance().Get();
        size_t n = CommandCodec::BuildQcAdvManufacturerData(
            rec.token, s_qc_mfr, sizeof(s_qc_mfr));
        if (n > 0) {
            esp_ble_adv_data_t a = adv_qc(n);
            esp_err_t r = esp_ble_gap_config_adv_data(&a);
            ESP_LOGI(TAG, "config ADV(Qc, mfr_len=%u): %s",
                     (unsigned)n, esp_err_to_name(r));
            return;
        }
        ESP_LOGW(TAG, "qc mfr build failed, fallback to Normal adv");
    }
    esp_ble_adv_data_t a = adv_normal();
    esp_err_t r = esp_ble_gap_config_adv_data(&a);
    ESP_LOGI(TAG, "config ADV(Normal): %s", esp_err_to_name(r));
}

void BleRemote::StartAdvertising() {}

void BleRemote::SwitchAdvByTick() {
    if (!m_inited || m_connected) return;
    // 未配对: 一直发 Normal adv, 不需要轮换
    if (!PairedStore::GetInstance().Has()) return;

    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    if (now_ms - m_last_rotate_ms < cfg::kQcAdvRotatePeriodMs) return;

    // 在 Qc ↔ Normal 之间轮换:
    //   Qc 帧让相机的"扫 SN 唤醒 + Quick Capture"路径生效
    //   Normal 帧让相机的"按名字发现"路径生效
    m_current_adv_mode = (m_current_adv_mode == AdvMode::Qc)
                       ? AdvMode::Normal
                       : AdvMode::Qc;
    m_last_rotate_ms = now_ms;
    // 切换前先停广播, 让新 payload config 立即生效
    esp_ble_gap_stop_advertising();
    ApplyAdvertisementPayload(m_current_adv_mode);
}

void BleRemote::ForgetPaired() {
    ESP_LOGW(TAG, "ForgetPaired: clear NVS + back to Normal-only adv");
    PairedStore::GetInstance().Forget();
    if (m_inited && !m_connected) {
        // 立刻切回 Normal adv: 相机以后再扫不到这台 wand 的 SN-token,
        // 自然不会被"反向唤醒"了.
        esp_ble_gap_stop_advertising();
        m_current_adv_mode = AdvMode::Normal;
        m_last_rotate_ms = (uint32_t)(esp_timer_get_time() / 1000);
        m_adv_started_ms = m_last_rotate_ms;
        ApplyAdvertisementPayload(m_current_adv_mode);
    }
}

// ============================================================================
// Outbound notify path — custom BTCTRL service only.
// HID + Battery + DevInfo are kept purely as a "looks like a sane peripheral"
// dressing; they don't carry application data.
// ============================================================================
bool BleRemote::PushNotify(const uint8_t* buf, size_t n, const char* tag) {
    // Route through custom Notify (BTCTRL protocol).
    if (!m_inited || !m_connected || m_cust_notify_handle == 0) {
        ESP_LOGW(TAG, "notify %s drop (inited=%d conn=%d h=%d)",
                 tag, m_inited, m_connected, m_cust_notify_handle);
        return false;
    }
    esp_ble_gatts_set_attr_value(m_cust_notify_handle, n, buf);
    esp_err_t r = esp_ble_gatts_send_indicate(m_gatts_if, m_conn_id,
            m_cust_notify_handle, n, const_cast<uint8_t*>(buf), false);
    ESP_LOGI(TAG, "notify %s len=%u: %s", tag, (unsigned)n, esp_err_to_name(r));
    return r == ESP_OK;
}

bool BleRemote::SendRecordStart() {
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildRecordStartFrame(b, sizeof(b));
    return PushNotify(b, n, "RecordStart");
}
bool BleRemote::SendRecordStop() {
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildRecordStopFrame(b, sizeof(b));
    return PushNotify(b, n, "RecordStop");
}
bool BleRemote::CycleToNextSubMode() {
    if (cfg::kModeSwitchSeqLen == 0) return false;
    uint8_t sub = m_mode_rotator.NextSubMode();
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildSetModeFrame(sub, b, sizeof(b));
    return PushNotify(b, n, "SetMode");
}
bool BleRemote::SendHighlightMark() {
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildHighlightMarkFrame(b, sizeof(b));
    return PushNotify(b, n, "Mark");
}
bool BleRemote::SendButton(uint8_t d, uint8_t bt, uint8_t st) {
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildButtonFrame(d, bt, st, b, sizeof(b));
    return PushNotify(b, n, "Button");
}
bool BleRemote::SendRecordToggle() {
    // BUTTON [device=0, button=BUTTON1 (id=0), state=SINGLE_CLICK (0)].
    // Peer routes BUTTON1 single-click to the record toggle handler,
    // which decides "start/stop recording" or "take photo" based on current mode.
    // Other states for the same button can be extended as needed:
    //   double-click (state=1) / triple-click (state=2) / long-press 3s (state=3) / long-press 1s (state=4)
    constexpr uint8_t kBtnIdButton1        = 0;
    constexpr uint8_t kBtnStateSingleClick = 0;
    return SendButton(/*device_id=*/0, kBtnIdButton1, kBtnStateSingleClick);
}
bool BleRemote::SendRcVersion() {
    uint8_t b[64] = {};
    size_t n = CommandCodec::BuildRcVersionFrame(b, sizeof(b));
    return PushNotify(b, n, "RcVersion");
}

void BleRemote::HandleConnected(const uint8_t pa[6]) {
    m_connected = true;
    m_adv_started_ms = 0;  // 已连接, 重置广播计时
    if (pa) memcpy(m_peer_addr, pa, 6);
    ESP_LOGI(TAG, "conn %02X:%02X:%02X:%02X:%02X:%02X",
        m_peer_addr[0],m_peer_addr[1],m_peer_addr[2],
        m_peer_addr[3],m_peer_addr[4],m_peer_addr[5]);
}
void BleRemote::HandleDisconnected() {
    ESP_LOGI(TAG, "disc");
    m_connected = false;
    ApplyCurrentAdvertisement();
}

void BleRemote::Write(const uint8_t* data, size_t len) {
    if (!data || len == 0) return;
    if (len < RemoteFrame::HeaderLength()) {
        ESP_LOGW(TAG, "write too short: %u", (unsigned)len);
        return;
    }
    InboundFrame frame{};
    if (!RemoteFrame::DecodeInboundFrame(data, len, frame)) {
        ESP_LOGW(TAG, "frame decode fail");
        return;
    }
    ESP_LOGI(TAG, "  → frame cmd=0x%02X end=%d sn=%u size=%u",
             frame.cmd, frame.end ? 1 : 0,
             (unsigned)frame.sn, (unsigned)frame.size);

    switch (frame.cmd) {
    case cfg::kCmdRxPeerToken:
        // WAKEUP_SN: payload = peer SN tail (6 ASCII bytes).
        // Persist as pairing token, then on reconnect use QC adv to wake peer.
        // Also reply RC_VERSION to signal protocol handshake completion.
        if (frame.size == cfg::kFramePeerTokenPayloadLen && frame.data) {
            PairedStore::GetInstance().Save(frame.data, m_peer_addr, true);
            ESP_LOGI(TAG, "  paired with token (camera SN tail)");
            SendRcVersion();
        } else {
            ESP_LOGW(TAG, "  WAKEUP_SN bad size=%u (expect %u)",
                     (unsigned)frame.size, (unsigned)cfg::kFramePeerTokenPayloadLen);
        }
        break;

    case cfg::kCmdRxDisconnect:
        // DISCONNECT: payload = 4 bytes { is_delete (1B), rsv[3] }.
        //   is_delete = 0: just disconnect, keep SN (token), peer can still
        //                  be woken via QC adv on next encounter.
        //   is_delete = 1: delete device, wand must clear flash-stored SN.
        // On receiving DISCONNECT, check payload byte 0: if 1, clear flash
        // SN; then wait for peer to drop the BLE link (don't close it ourselves).
        if (frame.size >= 1 && frame.data) {
            uint8_t is_delete = frame.data[0];
            ESP_LOGW(TAG, "  RX DISCONNECT is_delete=%u", (unsigned)is_delete);
            if (is_delete) {
                ForgetPaired();   // 清 NVS + 切回 Normal-only adv
            }
            // is_delete=0 不动 token; BLE 链路由相机侧主动断开,
            // 走 HandleDisconnected() 即可恢复 qc/normal 轮换.
        } else {
            ESP_LOGW(TAG, "  RX DISCONNECT bad payload size=%u, keep token",
                     (unsigned)frame.size);
        }
        break;

    case cfg::kCmdRxShutdown:
        // SHUTDOWN: peer requests wand power-off. Don't deep sleep directly
        // in the BLE task (that would prevent BLE stack cleanup), instead
        // latch -> main loop ConsumeShutdownRequest() picks it up and runs
        // the standard enter_deep_sleep() flow.
        ESP_LOGW(TAG, "  RX SHUTDOWN -> deferred power-off");
        m_shutdown_pending = true;
        break;

    default:
        // 其它命令 (0x50 BATTERY_VALUE / 0x52 CAMERA_MODE / 0x55 WORK_STATE 等)
        // 当前只记日志, 后续按需扩展.
        break;
    }
}

bool BleRemote::ConsumeShutdownRequest() {
    if (!m_shutdown_pending) return false;
    m_shutdown_pending = false;
    return true;
}

}  // namespace ble
}  // namespace cw