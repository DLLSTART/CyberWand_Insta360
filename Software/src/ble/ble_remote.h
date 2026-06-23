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

    // 自最近一次 "开始广播 (上电 / 断开后重新广播)" 起、至今仍未建立连接的
    // 毫秒数. 已连接时返回 0. 主循环可据此实现 "广播超时未连接 -> 关机".
    uint32_t GetUnconnectedAdvertisingMs() const;

    // 解除当前配对: 清 PairedStore (NVS) 并立刻切回 Normal-only adv,
    // 相机的"扫 SN 唤醒"路径会因为听不到 token 而停止主动连接.
    void ForgetPaired();

    // Peer sends SHUTDOWN command to set this; main loop polls and executes deep sleep.
    // 用 latch 而不是直接关机, 避免在 BLE 任务里阻塞调用电源管理流程.
    bool ConsumeShutdownRequest();

    bool SendRecordStart();
    bool SendRecordStop();
    // Send BUTTON [device=0, button=0, state=RECORD] to let the peer
    // toggle "start/stop recording" based on current state.
    // Unlike SendRecordStart/Stop, sending while recording stops it,
    // and sending while stopped starts it.
    bool SendRecordToggle();
    bool CycleToNextSubMode();
    bool SendHighlightMark();
    bool SendButton(uint8_t device_id, uint8_t button_id, uint8_t state);
    bool SendRcVersion();

    void OnGattEvent(uint16_t event, esp_gatt_if_t gatts_if, void* param);
    void OnGapEvent(uint16_t event, void* param);

private:
    BleRemote() = default;

    enum class AdvMode { Normal, Qc };

    void ApplyCurrentAdvertisement();
    void ApplyAdvertisementPayload(AdvMode mode);
    void StartAdvertising();

    void Write(const uint8_t* data, size_t len);
    void HandleConnected(const uint8_t peer_addr[6]);
    void HandleDisconnected();
    bool PushNotify(const uint8_t* buf, size_t n, const char* tag);

    // Service creation state machine — 4 services in order:
    //   1. HID Service (0x1812)              — satisfies camera's app_hogp
    //   2. Battery Service (0x180F)          — Battery Level read
    //   3. Device Information Service (0x180A) — PnP ID + Mfr Name
    //   4. Custom Service (0xFFE0)           — application data (DG)
    enum class SvcStep : uint8_t {
        kIdle,
        // HID
        kHidSvc,
        kHidReportMap,
        kHidInfo,
        kHidProtocolMode,
        kHidBootKbInput,
        kHidBootKbInputCccd,
        kHidReport,
        kHidReportCccd,
        kHidCtrlPoint,
        kHidStart,
        // Battery
        kBatSvc,
        kBatLevel,
        kBatLevelCccd,
        kBatStart,
        // Device Info
        kDevInfoSvc,
        kPnpId,
        kMfrName,
        kDevInfoStart,
        // Custom (FFE0)
        kCustSvc,
        kCustWrite,
        kCustNotify,
        kCustNotifyCccd,
        kCustStart,
        kDone,
    };

    uint16_t m_gatts_if       = 0xFF;
    uint16_t m_conn_id        = 0;

    bool     m_inited       = false;
    bool     m_connected    = false;
    uint8_t  m_peer_addr[6] = {0};

    // HID handles
    uint16_t m_hid_svc_handle    = 0;
    uint16_t m_hid_kbin_handle   = 0;
    uint16_t m_hid_kbin_cccd     = 0;
    uint16_t m_hid_report_handle = 0;
    uint16_t m_hid_report_cccd   = 0;

    // Battery / DevInfo
    uint16_t m_bat_svc_handle    = 0;
    uint16_t m_bat_level_handle  = 0;
    uint16_t m_bat_level_cccd    = 0;
    uint16_t m_devinfo_svc_handle = 0;

    // Custom (0xFFE0)
    uint16_t m_cust_svc_handle   = 0;
    uint16_t m_cust_write_handle = 0;
    uint16_t m_cust_notify_handle = 0;
    uint16_t m_cust_notify_cccd  = 0;

    SvcStep  m_svc_step = SvcStep::kIdle;

    ModeRotator m_mode_rotator;

    AdvMode  m_current_adv_mode = AdvMode::Normal;
    uint32_t m_last_rotate_ms   = 0;
    // 最近一次 "开始广播" 的时间戳 (ms, esp_timer 单调时间).
    // 上电首次广播 / 断开后重新广播时刷新; 建立连接时清零.
    uint32_t m_adv_started_ms   = 0;
    // 收到 peer SHUTDOWN 命令后置位, 主循环 ConsumeShutdownRequest() 取走时清零.
    bool     m_shutdown_pending = false;
};

}  // namespace ble
}  // namespace cw