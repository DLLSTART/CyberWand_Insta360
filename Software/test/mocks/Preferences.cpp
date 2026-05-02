#include "Preferences.h"

#include <cstring>
#include <map>
#include <vector>

namespace {
// 数据存储模型: namespace -> (key -> bytes)
// 静态生命周期, 进程内多次 begin() 可保留状态
using KeyMap = std::map<std::string, std::vector<uint8_t>>;
using NsMap  = std::map<std::string, KeyMap>;

NsMap& Storage() {
    static NsMap s;
    return s;
}
}  // namespace

namespace cw_test {
void ResetAllPreferencesNvs() { Storage().clear(); }
}  // namespace cw_test

Preferences::Preferences() = default;
Preferences::~Preferences() = default;

bool Preferences::begin(const char* nvs_namespace, bool read_only) {
    if (nvs_namespace == nullptr) {
        return false;
    }
    m_namespace = nvs_namespace;
    m_read_only = read_only;
    m_open      = true;
    // 真实 Preferences begin(read_only=true) 在命名空间不存在时也成功打开
    // (返回空数据), 这里行为一致, 不做特殊区分
    return true;
}

void Preferences::end() {
    m_open      = false;
    m_namespace.clear();
}

size_t Preferences::putUChar(const char* key, uint8_t value) {
    if (!m_open || key == nullptr) {
        return 0;
    }
    auto& km = Storage()[m_namespace];
    km[key] = std::vector<uint8_t>{value};
    return 1;
}

uint8_t Preferences::getUChar(const char* key, uint8_t default_value) {
    if (!m_open || key == nullptr) {
        return default_value;
    }
    auto ns_it = Storage().find(m_namespace);
    if (ns_it == Storage().end()) {
        return default_value;
    }
    auto k_it = ns_it->second.find(key);
    if (k_it == ns_it->second.end() || k_it->second.empty()) {
        return default_value;
    }
    return k_it->second[0];
}

size_t Preferences::putBytes(const char* key, const void* value, size_t len) {
    if (!m_open || key == nullptr || (len > 0 && value == nullptr)) {
        return 0;
    }
    auto& km = Storage()[m_namespace];
    auto* p = static_cast<const uint8_t*>(value);
    km[key].assign(p, p + len);
    return len;
}

size_t Preferences::getBytes(const char* key, void* buf, size_t max_len) {
    if (!m_open || key == nullptr) {
        return 0;
    }
    auto ns_it = Storage().find(m_namespace);
    if (ns_it == Storage().end()) return 0;
    auto k_it = ns_it->second.find(key);
    if (k_it == ns_it->second.end()) return 0;

    size_t want = k_it->second.size();
    size_t copy = (want < max_len) ? want : max_len;
    if (copy > 0 && buf != nullptr) {
        std::memcpy(buf, k_it->second.data(), copy);
    }
    return copy;
}

size_t Preferences::getBytesLength(const char* key) {
    if (!m_open || key == nullptr) return 0;
    auto ns_it = Storage().find(m_namespace);
    if (ns_it == Storage().end()) return 0;
    auto k_it = ns_it->second.find(key);
    if (k_it == ns_it->second.end()) return 0;
    return k_it->second.size();
}

bool Preferences::remove(const char* key) {
    if (!m_open || key == nullptr) return false;
    auto ns_it = Storage().find(m_namespace);
    if (ns_it == Storage().end()) return false;
    return ns_it->second.erase(key) > 0;
}
