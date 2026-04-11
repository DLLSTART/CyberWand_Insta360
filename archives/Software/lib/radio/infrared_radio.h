#pragma once
#include <stdint.h>
#include <base.h>
#include "base_radio.h"
#include <IRremoteESP8266.h>
#include <IRrecv.h>
#include <IRutils.h>

namespace cw::cyberwand::radio {

class InfraredRadio : public Radio , public cw::base::Singleton<InfraredRadio> {
public:
    InfraredRadio();
    ~InfraredRadio() = default;

    bool Init() override;
    bool Send(const uint8_t* data, uint16_t size) override;
    bool Send(const uint16_t* data, uint16_t size) override;
    const uint16_t* Receive(uint16_t& size) override;

private:
    uint16_t* ResultToRawArray(uint16_t& size);

    void Dump(decode_results *results);
    void Dump(const uint16_t *rawbuf, uint16_t length);
    static constexpr uint16_t kRecvPin = 14;
    static constexpr uint8_t kTimeout = 50;
    static constexpr uint8_t kTolerancePercentage = 25;
    static constexpr uint16_t kMinUnknownSize = 12;
    IRrecv irrecv;
    decode_results results;
};

}


