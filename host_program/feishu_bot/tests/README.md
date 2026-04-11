# CyberWand 上位机单元测试设计

**版本**: v1.0  
**创建时间**: 2026-04-08  
**状态**: 设计完成，待开发

---

## 📋 测试架构

### 测试框架
- **pytest** - 测试运行器
- **pytest-cov** - 代码覆盖率
- **pytest-asyncio** - 异步测试支持
- **pytest-mock** - Mock 支持
- **pytest-qt** - Qt GUI 测试

### 测试目录结构
```
host_program/feishu_bot/
├── src/
│   ├── cyberwand_feishu_bot.py
│   ├── websocket_handler.py
│   ├── ble_gateway.py
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 测试配置
│   ├── test_websocket.py        # WebSocket 测试
│   ├── test_ble_gateway.py      # BLE 网关测试
│   ├── test_feishu_bot.py       # 飞书机器人测试
│   ├── test_command_handler.py  # 命令处理测试
│   ├── test_integration.py      # 集成测试
│   └── fixtures/
│       ├── mock_ble_device.py   # BLE Mock
│       └── mock_feishu_api.py   # 飞书 API Mock
├── requirements.txt
├── requirements-dev.txt         # 开发依赖
├── pytest.ini                   # pytest 配置
└── README.md
```

---

## 🧪 单元测试设计

### 1. WebSocket 处理器测试

```python
# tests/test_websocket.py
import pytest
import asyncio
import websockets
from src.websocket_handler import WebSocketHandler

class TestWebSocketHandler:
    """WebSocket 处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建测试用 Handler"""
        return WebSocketHandler()
    
    @pytest.mark.asyncio
    async def test_on_connect(self, handler):
        """测试连接建立"""
        # Mock WebSocket 连接
        mock_ws = MockWebSocket()
        
        # 调用连接处理
        await handler.on_connect(mock_ws)
        
        # 验证
        assert mock_ws.sent_messages[0] == '{"type": "connected"}'
    
    @pytest.mark.asyncio
    async def test_on_scan_command(self, handler, mock_ble_gateway):
        """测试扫描设备命令"""
        mock_ws = MockWebSocket()
        command = {"cmd": "scan", "timeout": 5}
        
        # Mock BLE 扫描结果
        mock_ble_gateway.scan_devices.return_value = [
            {"name": "CyberWand_001", "address": "AA:BB:CC:DD:EE:FF"}
        ]
        
        # 执行命令
        await handler.on_message(mock_ws, json.dumps(command))
        
        # 验证返回结果
        assert "scan_result" in mock_ws.sent_messages[0]
        assert "CyberWand_001" in mock_ws.sent_messages[0]
    
    @pytest.mark.asyncio
    async def test_on_connect_command(self, handler, mock_ble_gateway):
        """测试连接设备命令"""
        mock_ws = MockWebSocket()
        command = {
            "cmd": "connect",
            "address": "AA:BB:CC:DD:EE:FF"
        }
        
        # Mock 连接成功
        mock_ble_gateway.connect.return_value = True
        
        # 执行命令
        await handler.on_message(mock_ws, json.dumps(command))
        
        # 验证
        assert mock_ble_gateway.connect.called
        assert "connected" in mock_ws.sent_messages[0]
    
    @pytest.mark.asyncio
    async def test_on_disconnect_command(self, handler, mock_ble_gateway):
        """测试断开连接命令"""
        mock_ws = MockWebSocket()
        command = {"cmd": "disconnect"}
        
        # 执行命令
        await handler.on_message(mock_ws, json.dumps(command))
        
        # 验证
        assert mock_ble_gateway.disconnect.called
    
    @pytest.mark.asyncio
    async def test_on_get_status_command(self, handler):
        """测试获取状态命令"""
        mock_ws = MockWebSocket()
        command = {"cmd": "get_status"}
        
        # 执行命令
        await handler.on_message(mock_ws, json.dumps(command))
        
        # 验证返回状态
        status = json.loads(mock_ws.sent_messages[0])
        assert "battery" in status
        assert "connected" in status
        assert "gesture_mode" in status
    
    @pytest.mark.asyncio
    async def test_invalid_command(self, handler):
        """测试无效命令"""
        mock_ws = MockWebSocket()
        command = {"cmd": "invalid_command"}
        
        # 执行命令
        await handler.on_message(mock_ws, json.dumps(command))
        
        # 验证返回错误
        assert "error" in mock_ws.sent_messages[0]
    
    @pytest.mark.asyncio
    async def test_connection_closed(self, handler):
        """测试连接断开处理"""
        mock_ws = MockWebSocket()
        mock_ws.closed = True
        
        # 验证断开处理
        await handler.on_disconnect(mock_ws)
        assert handler.active_connections == 0
```

### 2. BLE 网关测试

```python
# tests/test_ble_gateway.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.ble_gateway import CyberWandBLE

class TestCyberWandBLE:
    """BLE 网关测试"""
    
    @pytest.fixture
    def ble_gateway(self):
        """创建测试用 BLE 网关"""
        return CyberWandBLE()
    
    @pytest.mark.asyncio
    async def test_scan_devices(self, ble_gateway, mock_bleak_client):
        """测试扫描设备"""
        # Mock 扫描结果
        mock_bleak_client.discovered_devices = [
            MockBLEDevice("CyberWand_001", "AA:BB:CC:DD:EE:FF")
        ]
        
        # 执行扫描
        devices = await ble_gateway.scan_devices(timeout=5)
        
        # 验证
        assert len(devices) == 1
        assert devices[0]["name"] == "CyberWand_001"
    
    @pytest.mark.asyncio
    async def test_connect_success(self, ble_gateway, mock_bleak_client):
        """测试连接成功"""
        mock_bleak_client.connect.return_value = True
        
        # 执行连接
        result = await ble_gateway.connect("AA:BB:CC:DD:EE:FF")
        
        # 验证
        assert result == True
        assert ble_gateway.is_connected == True
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, ble_gateway, mock_bleak_client):
        """测试连接失败"""
        mock_bleak_client.connect.side_effect = Exception("Connection failed")
        
        # 执行连接
        result = await ble_gateway.connect("AA:BB:CC:DD:EE:FF")
        
        # 验证
        assert result == False
        assert ble_gateway.is_connected == False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ble_gateway, mock_bleak_client):
        """测试断开连接"""
        # 先连接
        await ble_gateway.connect("AA:BB:CC:DD:EE:FF")
        
        # 断开
        await ble_gateway.disconnect()
        
        # 验证
        assert mock_bleak_client.disconnect.called
        assert ble_gateway.is_connected == False
    
    @pytest.mark.asyncio
    async def test_send_gesture_mapping(self, ble_gateway, mock_bleak_client):
        """测试发送手势映射"""
        mapping = {
            "wave_left": "page_prev",
            "wave_right": "page_next",
            "rotate_cw": "volume_up"
        }
        
        # 发送映射
        await ble_gateway.send_gesture_mapping(mapping)
        
        # 验证
        assert mock_bleak_client.write_gatt_char.called
        call_args = mock_bleak_client.write_gatt_char.call_args
        assert b"gesture_mapping" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_receive_sensor_data(self, ble_gateway, mock_bleak_client):
        """测试接收传感器数据"""
        # Mock 通知数据
        mock_data = bytes([0x01, 0x02, 0x03, 0x04])  # 模拟 IMU 数据
        
        # 启动通知
        await ble_gateway.start_sensor_notification()
        
        # 模拟数据到达
        mock_bleak_client.notification_callback(mock_data)
        
        # 验证数据处理
        assert ble_gateway.last_sensor_data is not None
    
    @pytest.mark.asyncio
    async def test_get_battery_level(self, ble_gateway, mock_bleak_client):
        """测试获取电量"""
        # Mock 电量值
        mock_bleak_client.read_gatt_char.return_value = bytes([85])  # 85%
        
        # 获取电量
        battery = await ble_gateway.get_battery_level()
        
        # 验证
        assert battery == 85
```

### 3. 飞书机器人测试

```python
# tests/test_feishu_bot.py
import pytest
from unittest.mock import AsyncMock, patch
from src.cyberwand_feishu_bot import FeishuBotHandler

class TestFeishuBotHandler:
    """飞书机器人测试"""
    
    @pytest.fixture
    def bot_handler(self, mock_wand):
        """创建测试用机器人处理器"""
        return FeishuBotHandler(mock_wand)
    
    @pytest.mark.asyncio
    async def test_help_command(self, bot_handler, mock_feishu_client):
        """测试/help 命令"""
        mock_event = create_mock_event("/help")
        
        # 执行命令
        await bot_handler.handle_message(mock_event)
        
        # 验证回复
        assert mock_feishu_client.im.message.create.called
        reply = mock_feishu_client.im.message.create.call_args[1]["content"]
        assert "帮助" in reply
        assert "/scan" in reply
        assert "/connect" in reply
    
    @pytest.mark.asyncio
    async def test_scan_command(self, bot_handler, mock_feishu_client, mock_wand):
        """测试/scan 命令"""
        mock_event = create_mock_event("/scan")
        
        # Mock 扫描结果
        mock_wand.scan_devices.return_value = [
            {"name": "CyberWand_001", "address": "AA:BB:CC:DD:EE:FF"}
        ]
        
        # 执行命令
        await bot_handler.handle_message(mock_event)
        
        # 验证回复
        assert mock_feishu_client.im.message.create.called
        reply = mock_feishu_client.im.message.create.call_args[1]["content"]
        assert "CyberWand_001" in reply
    
    @pytest.mark.asyncio
    async def test_connect_command(self, bot_handler, mock_feishu_client, mock_wand):
        """测试/connect 命令"""
        mock_event = create_mock_event("/connect AA:BB:CC:DD:EE:FF")
        
        # Mock 连接成功
        mock_wand.connect.return_value = True
        
        # 执行命令
        await bot_handler.handle_message(mock_event)
        
        # 验证回复
        reply = mock_feishu_client.im.message.create.call_args[1]["content"]
        assert "连接成功" in reply
    
    @pytest.mark.asyncio
    async def test_status_command(self, bot_handler, mock_feishu_client, mock_wand):
        """测试/status 命令"""
        mock_event = create_mock_event("/status")
        
        # Mock 状态数据
        mock_wand.get_status.return_value = {
            "battery": 85,
            "connected": True,
            "gesture_mode": "demo"
        }
        
        # 执行命令
        await bot_handler.handle_message(mock_event)
        
        # 验证回复
        reply = mock_feishu_client.im.message.create.call_args[1]["content"]
        assert "电量：85%" in reply
        assert "已连接" in reply
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, bot_handler, mock_feishu_client):
        """测试未知命令"""
        mock_event = create_mock_event("/unknown_command")
        
        # 执行命令
        await bot_handler.handle_message(mock_event)
        
        # 验证回复错误
        reply = mock_feishu_client.im.message.create.call_args[1]["content"]
        assert "未知命令" in reply
```

### 4. 命令处理器测试

```python
# tests/test_command_handler.py
import pytest
from src.command_handler import CommandHandler, CommandError

class TestCommandHandler:
    """命令处理器测试"""
    
    @pytest.fixture
    def command_handler(self):
        """创建测试用命令处理器"""
        return CommandHandler()
    
    def test_register_command(self, command_handler):
        """测试注册命令"""
        @command_handler.register("test_cmd")
        async def test_cmd(args):
            return "test_result"
        
        assert "test_cmd" in command_handler.commands
    
    def test_execute_registered_command(self, command_handler):
        """测试执行已注册命令"""
        @command_handler.register("test_cmd")
        async def test_cmd(args):
            return f"result: {args}"
        
        result = command_handler.execute("test_cmd", "arg1")
        assert result == "result: arg1"
    
    def test_execute_unknown_command(self, command_handler):
        """测试执行未知命令"""
        with pytest.raises(CommandError) as exc_info:
            command_handler.execute("unknown_cmd", "args")
        
        assert "Unknown command" in str(exc_info.value)
    
    def test_command_with_validation(self, command_handler):
        """测试带验证的命令"""
        @command_handler.register("connect")
        async def connect(args):
            # 验证 MAC 地址格式
            if not is_valid_mac_address(args):
                raise CommandError("Invalid MAC address")
            return f"Connected to {args}"
        
        # 有效 MAC 地址
        result = command_handler.execute("connect", "AA:BB:CC:DD:EE:FF")
        assert "Connected" in result
        
        # 无效 MAC 地址
        with pytest.raises(CommandError):
            command_handler.execute("connect", "invalid_mac")
```

---

## 🔧 集成测试

```python
# tests/test_integration.py
import pytest
import asyncio
from src.cyberwand_feishu_bot import main as bot_main

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 启动机器人服务
        # 2. 飞书发送/help 命令
        # 3. 验证回复
        # 4. 飞书发送/scan 命令
        # 5. 验证扫描结果
        # 6. 飞书发送/connect 命令
        # 7. 验证连接状态
        # 8. 小程序连接 WebSocket
        # 9. 小程序发送手势配置
        # 10. 验证 BLE 设备收到配置
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """测试错误恢复"""
        # 1. 模拟 BLE 连接失败
        # 2. 验证错误处理
        # 3. 模拟重连
        # 4. 验证恢复成功
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """测试并发连接"""
        # 1. 多个小程序同时连接
        # 2. 验证每个连接独立工作
        # 3. 验证资源正确分配
        pass
```

---

## 📊 测试覆盖率要求

| 模块 | 行覆盖率 | 分支覆盖率 |
|------|---------|-----------|
| WebSocket 处理器 | ≥ 90% | ≥ 85% |
| BLE 网关 | ≥ 90% | ≥ 85% |
| 飞书机器人 | ≥ 85% | ≥ 80% |
| 命令处理器 | ≥ 95% | ≥ 90% |
| **总计** | **≥ 90%** | **≥ 85%** |

---

## 🚀 运行测试

### 安装开发依赖
```bash
pip install -r requirements-dev.txt
```

### 运行所有测试
```bash
pytest tests/ -v --cov=src --cov-report=html
```

### 运行特定测试
```bash
pytest tests/test_websocket.py -v
pytest tests/test_ble_gateway.py -v
pytest tests/test_feishu_bot.py -v
```

### 生成覆盖率报告
```bash
pytest --cov=src --cov-report=html
# 打开 htmlcov/index.html 查看报告
```

### CI/CD 集成
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/ -v --cov=src
      - run: coverage report --fail-under=90
```

---

## 📊 Mock 对象

### BLE Mock
```python
# tests/fixtures/mock_ble_device.py
class MockBLEDevice:
    def __init__(self, name, address):
        self.name = name
        self.address = address

class MockBleakClient:
    def __init__(self):
        self.is_connected = False
        self.discovered_devices = []
        self.notification_callback = None
    
    async def connect(self):
        self.is_connected = True
        return True
    
    async def disconnect(self):
        self.is_connected = False
    
    async def start_notify(self, uuid, callback):
        self.notification_callback = callback
```

### 飞书 API Mock
```python
# tests/fixtures/mock_feishu_api.py
class MockFeishuClient:
    def __init__(self):
        self.im = MockIM()

class MockIM:
    def __init__(self):
        self.message = MockMessage()

class MockMessage:
    def __init__(self):
        self.create = AsyncMock()
```

---

**设计人**: 太子  
**日期**: 2026-04-08
