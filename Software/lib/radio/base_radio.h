#pragma once
#include <stdint.h>
#include  <string>

#define RADIO_RECV_BUFFER_SIZE 1024

namespace cw::cyberwand::radio {

// 统一的通信接口，所有具体实现都应继承并实现这些方法。
class Radio {
public:
    virtual ~Radio() = default;

    // 初始化（驱动/资源准备）
    virtual bool Init() = 0;
    // 发送数据（同步或异步由具体实现决定）
    virtual bool Send(const uint16_t* data, uint16_t size) = 0;
    virtual bool Send(const uint8_t* data, uint16_t size) = 0;
    // 非阻塞读取/接收（可返回空向量表示当前无数据）
    virtual const uint16_t* Receive(uint16_t& size) = 0;

protected:
    uint16_t recv_buffer_[RADIO_RECV_BUFFER_SIZE];
    
};

} // namespace cyberwand::radio