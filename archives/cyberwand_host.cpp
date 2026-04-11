/**
 * CyberWand Host Program - USB Bluetooth Control
 * 
 * 功能：
 * - 连接魔杖蓝牙
 * - 修改按键映射
 * - 修改功能映射
 * - GUI界面
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>

#ifdef _WIN32
#include <windows.h>
#endif

/**
 * 按键类型
 */
enum class ButtonType {
    MODE_TOGGLE,    // 模式切换
    GESTURE,        // 手势识别
    RECORD,         // 录制模式
    CONTROL,        // 控制模式
};

/**
 * 蓝牙连接状态
 */
class BluetoothConnection {
public:
    BluetoothConnection();
    ~BluetoothConnection();
    
    bool connect(const std::string& address);
    bool disconnect();
    bool send_command(const std::string& command);
    std::string receive_data();
    bool is_connected();
    
private:
    bool connected;
    int bt_handle;
};

/**
 * 按键映射配置
 */
struct ButtonMapping {
    ButtonType type;
    int action_id;
    std::string description;
};

/**
 * 魔杖配置
 */
struct CyberWandConfig {
    std::string device_name;
    std::string device_address;
    
    // 按键映射
    std::vector<ButtonMapping> button_mappings;
    
    // 功能映射
    std::map<int, std::string> gesture_functions;
    
    // 灯语配置
    std::map<std::string, std::string> led_patterns;
    
    // 命令格式
    std::string command_prefix;
    std::string command_suffix;
};

/**
 * 上位机主程序
 */
class HostProgram {
public:
    HostProgram();
    ~HostProgram();
    
    // 初始化
    bool init();
    
    // 连接魔杖
    bool connect_to_cyberwand();
    
    // 获取当前配置
    CyberWandConfig get_current_config();
    
    // 修改按键映射
    bool update_button_mapping(int button_id, const ButtonMapping& mapping);
    
    // 修改功能映射
    bool update_gesture_function(int gesture_id, const std::string& function);
    
    // 保存配置到魔杖
    bool save_config_to_device();
    
    // GUI主循环
    void run_gui();
    
private:
    BluetoothConnection bt_conn;
    CyberWandConfig current_config;
    bool initialized;
    
    // 菜单选项
    void show_main_menu();
    void show_config_menu();
    void show_button_mapping_menu();
    void show_gesture_function_menu();
};

// 实现

BluetoothConnection::BluetoothConnection() : connected(false), bt_handle(0) {}

BluetoothConnection::~BluetoothConnection() {
    if (connected) {
        disconnect();
    }
}

bool BluetoothConnection::connect(const std::string& address) {
    std::cout << "[BT] Connecting to " << address << std::endl;
    connected = true;
    std::cout << "[BT] Connected!" << std::endl;
    return true;
}

bool BluetoothConnection::disconnect() {
    std::cout << "[BT] Disconnecting..." << std::endl;
    connected = false;
    std::cout << "[BT] Disconnected!" << std::endl;
    return true;
}

bool BluetoothConnection::send_command(const std::string& command) {
    if (!connected) {
        std::cout << "[BT] Error: Not connected" << std::endl;
        return false;
    }
    std::cout << "[BT] Sending: " << command << std::endl;
    return true;
}

std::string BluetoothConnection::receive_data() {
    return "";
}

bool BluetoothConnection::is_connected() {
    return connected;
}

HostProgram::HostProgram() : initialized(false) {
    current_config.device_name = "CyberWand";
    current_config.command_prefix = "CMD:";
    current_config.command_suffix = ";";
    
    // 默认按键映射
    current_config.button_mappings = {
        {ButtonType::MODE_TOGGLE, 1, "模式切换按键"}
    };
    
    // 默认功能映射
    current_config.gesture_functions = {
        {1, "挥手: 拍照"},
        {2, "握拳: 开始录像"},
        {3, "旋转: 参数调整"},
    };
    
    // 默认灯语配置
    current_config.led_patterns = {
        {"IDLE", "闪烁"},
        {"CONTROL", "常亮"},
        {"RECORD", "快闪"},
        {"TRANS", "慢闪"},
    };
}

HostProgram::~HostProgram() {}

bool HostProgram::init() {
    std::cout << "[SYS] Initializing Host Program..." << std::endl;
    initialized = true;
    std::cout << "[SYS] Initialized!" << std::endl;
    return true;
}

bool HostProgram::connect_to_cyberwand() {
    std::cout << "[SYS] Connecting to CyberWand..." << std::endl;
    return bt_conn.connect("AA:BB:CC:DD:EE:FF");
}

CyberWandConfig HostProgram::get_current_config() {
    return current_config;
}

bool HostProgram::update_button_mapping(int button_id, const ButtonMapping& mapping) {
    if (button_id >= 0 && button_id < current_config.button_mappings.size()) {
        current_config.button_mappings[button_id] = mapping;
        return true;
    }
    return false;
}

bool HostProgram::update_gesture_function(int gesture_id, const std::string& function) {
    current_config.gesture_functions[gesture_id] = function;
    return true;
}

bool HostProgram::save_config_to_device() {
    std::cout << "[SYS] Saving config to device..." << std::endl;
    std::string config_str = "CONFIG:" + current_config.command_prefix;
    for (auto& mapping : current_config.button_mappings) {
        config_str += std::to_string(mapping.action_id) + ",";
    }
    config_str += current_config.command_suffix;
    return bt_conn.send_command(config_str);
}

void HostProgram::show_main_menu() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "  CyberWand Host Program" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "1. 连接魔杖" << std::endl;
    std::cout << "2. 查看配置" << std::endl;
    std::cout << "3. 修改按键映射" << std::endl;
    std::cout << "4. 修改功能映射" << std::endl;
    std::cout << "5. 保存配置" << std::endl;
    std::cout << "0. 退出" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "请选择: ";
}

void HostProgram::show_config_menu() {
    std::cout << "\n--- 当前配置 ---" << std::endl;
    std::cout << "设备名称: " << current_config.device_name << std::endl;
    std::cout << "蓝牙地址: " << current_config.device_address << std::endl;
    std::cout << "按键映射: " << current_config.button_mappings.size() << " 个" << std::endl;
    std::cout << "功能映射: " << current_config.gesture_functions.size() << " 个" << std::endl;
    std::cout << "灯语配置: " << current_config.led_patterns.size() << " 个" << std::endl;
}

void HostProgram::show_button_mapping_menu() {
    std::cout << "\n--- 修改按键映射 ---" << std::endl;
    for (size_t i = 0; i < current_config.button_mappings.size(); i++) {
        std::cout << i << ". " << current_config.button_mappings[i].description << std::endl;
    }
    std::cout << "输入按钮ID: ";
}

void HostProgram::show_gesture_function_menu() {
    std::cout << "\n--- 修改功能映射 ---" << std::endl;
    for (auto& pair : current_config.gesture_functions) {
        std::cout << pair.first << ". " << pair.second << std::endl;
    }
    std::cout << "输入手势ID: ";
}

void HostProgram::run_gui() {
    if (!init()) {
        std::cout << "[SYS] Failed to initialize!" << std::endl;
        return;
    }
    
    std::cout << "\n欢迎使用 CyberWand Host Program" << std::endl;
    std::cout << "使用蓝牙连接魔杖以进行配置" << std::endl;
    
    while (true) {
        show_main_menu();
        
        int choice;
        std::cin >> choice;
        
        switch (choice) {
            case 1:
                connect_to_cyberwand();
                break;
            case 2:
                show_config_menu();
                break;
            case 3:
                show_button_mapping_menu();
                int btn_id;
                std::cin >> btn_id;
                if (btn_id >= 0 && btn_id < current_config.button_mappings.size()) {
                    ButtonMapping new_mapping;
                    std::cout << "请输入新描述: ";
                    std::cin.ignore();
                    std::getline(std::cin, new_mapping.description);
                    new_mapping.type = ButtonType::MODE_TOGGLE;
                    new_mapping.action_id = btn_id;
                    
                    update_button_mapping(btn_id, new_mapping);
                    std::cout << "按键映射已更新！" << std::endl;
                }
                break;
            case 4:
                show_gesture_function_menu();
                int gesture_id;
                std::cin >> gesture_id;
                std::cout << "请输入新功能描述: ";
                std::cin.ignore();
                std::getline(std::cin, current_config.gesture_functions[gesture_id]);
                std::cout << "功能映射已更新！" << std::endl;
                break;
            case 5:
                save_config_to_device();
                break;
            case 0:
                std::cout << "再见！" << std::endl;
                return;
            default:
                std::cout << "无效选择！" << std::endl;
                break;
        }
    }
}

int main() {
    HostProgram program;
    program.run_gui();
    
    return 0;
}
