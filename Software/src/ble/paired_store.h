#pragma once
#include <stdint.h>
#include "base.h"

namespace cw {
namespace ble {

struct PairedRecord {
    uint8_t  token[6];
    uint8_t  mac[6];
    uint8_t  mac_valid;
    uint32_t last_link_ms;
};

class PairedStore : public base::Singleton<PairedStore> {
    friend class base::Singleton<PairedStore>;

public:
    void Init();
    void Save(const uint8_t token[6], const uint8_t mac[6], bool mac_valid);
    bool Has() const { return m_valid; }
    const PairedRecord& Get() const { return m_record; }
    void Forget();

private:
    PairedStore() = default;

    void LoadFromNvs();
    void SaveToNvs() const;

    PairedRecord m_record = {};
    bool         m_valid  = false;
    bool         m_inited = false;
};

}
}
