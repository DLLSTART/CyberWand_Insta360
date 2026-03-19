#include "infrared_radio.h"
#include <common.h>

namespace cw::cyberwand::radio {

InfraredRadio::InfraredRadio()
    : irrecv(kRecvPin, RADIO_RECV_BUFFER_SIZE, kTimeout, true) {
}

bool InfraredRadio::Init() {
    // 初始化红外通信模块
    irrecv.setUnknownThreshold(kMinUnknownSize);
    irrecv.setTolerance(kTolerancePercentage);  // Override the default tolerance.
    irrecv.enableIRIn();  // Start the receiver
    return true;
}

bool InfraredRadio::Send(const uint16_t* data, uint16_t size) {
    // 发送红外数据
    return true;
}

bool InfraredRadio::Send(const uint8_t* data, uint16_t size) {
    // 发送红外数据
    return true;
}

uint16_t* InfraredRadio::ResultToRawArray(uint16_t& size) {
    uint16_t pos = 0;
    memset(recv_buffer_, 0, sizeof(recv_buffer_));
    size = std::min(results.rawlen, (uint16_t)RADIO_RECV_BUFFER_SIZE);
    for (uint16_t i = 1; i < size; i++) {
        uint32_t usecs = results.rawbuf[i] * kRawTick;
        while (usecs > UINT16_MAX) {  // Keep truncating till it fits.
        recv_buffer_[pos++] = UINT16_MAX;
        recv_buffer_[pos++] = 0;  // A 0 in a sendRaw() array basically means skip.
        usecs -= UINT16_MAX;
        }
        recv_buffer_[pos++] = usecs;
    }
    #if defined(CY_DEBUG)
    Dump(recv_buffer_, size);
    #endif
    return recv_buffer_;
}

const uint16_t* InfraredRadio::Receive(uint16_t& size) {
    if (irrecv.decode(&results)) {
        return ResultToRawArray(size);
    }
    return nullptr;
}

void InfraredRadio::Dump(decode_results *results) {
  uint16_t count = results->rawlen;
  if (results->decode_type == UNKNOWN) {
    Serial.print("Unknown encoding: ");
  } else if (results->decode_type == NEC) {
    Serial.print("Decoded NEC: ");
  } else if (results->decode_type == SONY) {
    Serial.print("Decoded SONY: ");
  } else if (results->decode_type == RC5) {
    Serial.print("Decoded RC5: ");
  } else if (results->decode_type == RC5X) {
    Serial.print("Decoded RC5X: ");
  } else if (results->decode_type == RC6) {
    Serial.print("Decoded RC6: ");
  } else if (results->decode_type == RCMM) {
    Serial.print("Decoded RCMM: ");
  } else if (results->decode_type == PANASONIC) {
    Serial.print("Decoded PANASONIC - Address: ");
    Serial.print(results->address, HEX);
    Serial.print(" Value: ");
  } else if (results->decode_type == LG) {
    Serial.print("Decoded LG: ");
  } else if (results->decode_type == JVC) {
    Serial.print("Decoded JVC: ");
  } else if (results->decode_type == AIWA_RC_T501) {
    Serial.print("Decoded AIWA RC T501: ");
  } else if (results->decode_type == WHYNTER) {
    Serial.print("Decoded Whynter: ");
  } else if (results->decode_type == NIKAI) {
    Serial.print("Decoded Nikai: ");
  }
  serialPrintUint64(results->value, 16);
  Serial.print(" (");
  Serial.print(results->bits, DEC);
  Serial.println(" bits)");
  Serial.print("Raw (");
  Serial.print(count, DEC);
  Serial.print("): {");

  for (uint16_t i = 1; i < count; i++) {
    if (i % 100 == 0)
      yield();  // Preemptive yield every 100th entry to feed the WDT.
    if (i & 1) {
      Serial.print(results->rawbuf[i] * kRawTick, DEC);
    } else {
      Serial.print(", ");
      Serial.print(static_cast<uint32_t>(results->rawbuf[i] * kRawTick), DEC);
    }
  }
  Serial.println("};");
}

void InfraredRadio::Dump(const uint16_t *rawbuf, uint16_t length) {
  Serial.print("Raw (");
  Serial.print(length, DEC);
  Serial.print("): {");
  for (uint16_t i = 0; i < length; i++) {
    if (i % 100 == 0)
      yield();  // Preemptive yield every 100th entry to feed the WDT.
    if (i & 1) {
      Serial.print(rawbuf[i], DEC);
    } else {
      Serial.print(", ");
      Serial.print(rawbuf[i], DEC);
    }
  }
  Serial.println("};");
}
}
