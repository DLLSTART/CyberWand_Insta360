// =============================================================================
// Preferences.h — 本地单元测试用桩, 替代 ESP32 Preferences NVS 库
// -----------------------------------------------------------------------------
// 实现细节:
//   - 用静态 std::map<namespace, std::map<key, value>> 模拟 flash NVS
//   - 每次 begin() 选定当前命名空间, 所有 put/get/remove 都作用其上
//   - 跨多次 begin() / 进程内重启 仍保留数据 (静态变量)
//   - 测试可通过 cw_test::ResetAllPreferencesNvs() 完全清空, 用于隔离用例
//
// 与真实 Preferences 的差异:
//   - 不真正写 flash, 没有持久化 (进程退出即丢失)
//   - readOnly 标志当前不强制约束 (写在只读模式上不会报错), 测试无需关心
//   - 不实现 putString / getString 等字符串类型 (本项目 ble 模块只用 byte/uchar)
// =============================================================================
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>

namespace cw_test {
// 清空所有命名空间的模拟 NVS 数据 (用于测试用例之间的隔离)
void ResetAllPreferencesNvs();
}  // namespace cw_test

class Preferences {
public:
    Preferences();
    ~Preferences();

    // 打开命名空间. read_only 仅作记录, 不强制约束.
    // 返回值: 是否成功 (本桩永远成功)
    bool begin(const char* nvs_namespace, bool read_only = false);

    // 关闭当前命名空间 handle
    void end();

    // 写一个无符号字节. 返回写入字节数 (1 = 成功, 0 = 未 begin)
    size_t putUChar(const char* key, uint8_t value);

    // 读一个无符号字节. key 不存在返回 default_value
    uint8_t getUChar(const char* key, uint8_t default_value = 0);

    // 写任意二进制 blob. 返回实际写入字节数
    size_t putBytes(const char* key, const void* value, size_t len);

    // 读任意二进制 blob. 返回实际读到字节数, 不足 max_len 时只读 stored_len
    size_t getBytes(const char* key, void* buf, size_t max_len);

    // 查询 blob 长度, 0 表示不存在
    size_t getBytesLength(const char* key);

    // 删除一个 key
    bool remove(const char* key);

private:
    std::string m_namespace;
    bool        m_open      = false;
    bool        m_read_only = false;
};
