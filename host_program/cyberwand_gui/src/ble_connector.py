"""
CyberWand Control Center - BLE 连接器

协议说明 (与固件 protocol_config.h 保持一致):
  - 设备名         : "CyberWand"
  - 主服务         : 0xFFE0  (BTCTRL service)
  - Write 特征     : 0xFFE1  (Host -> Wand 命令)
  - Notify 特征    : 0xFFE2  (Wand -> Host 通知)
  - Battery 服务   : 0x180F, Battery Level 特征 0x2A19 (标准 GATT)

帧格式 (出向, Host -> Wand):
  [HEAD 3B: AA BB CC][CMD 1B][END|SN 1B][SIZE 1B][DATA SIZE B]

帧格式 (入向, Wand -> Host):
  [HEAD 3B: CC BB AA][CMD 1B][END|SN 1B][SIZE 1B][DATA SIZE B]

支持的入向命令 (Wand -> Host):
  BUTTON  : [device_id 1B][button_id 1B][state 1B]
            button_id=0/state=0 -> 单击 (录像切换 / 拍照)
  RC_VER  : [maj 1B][min 1B][rev 1B][build 1B] 固件版本

支持的出向命令 (Host -> Wand) -- 见 protocol_config.h kCmdTx*:
  RecordStart / RecordStop / Mark / Button / SetMode
"""

from PySide6.QtCore import QObject, Signal, Slot
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import asyncio
import struct
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# BLE UUID 常量 (与固件 protocol_config.h 严格对齐)
# =============================================================================

# BTCTRL 自定义服务 (0xFFE0/0xFFE1/0xFFE2)
CYBERWAND_SERVICE_UUID  = "0000ffe0-0000-1000-8000-00805f9b34fb"
CYBERWAND_WRITE_UUID    = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Host -> Wand
CYBERWAND_NOTIFY_UUID   = "0000ffe2-0000-1000-8000-00805f9b34fb"  # Wand -> Host (NOTIFY)

# 标准 GATT Battery Service
BATTERY_SERVICE_UUID   = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID     = "00002a19-0000-1000-8000-00805f9b34fb"

# 固件协议帧头
FRAME_HEAD_OUTBOUND = bytes([0xAA, 0xBB, 0xCC])   # Host -> Wand
FRAME_HEAD_INBOUND  = bytes([0xCC, 0xBB, 0xAA])   # Wand -> Host
FRAME_END_BIT       = 0x80

# 命令字 (出向 Host -> Wand)
CMD_TX_RECORD_START   = 0x23
CMD_TX_RECORD_STOP    = 0x24
CMD_TX_MARK           = 0x25
CMD_TX_SET_MODE       = 0x21
CMD_TX_BUTTON         = 0x10
CMD_TX_RC_VERSION     = 0x11

# 命令字 (入向 Wand -> Host)
CMD_RX_PEER_TOKEN     = 0x01
CMD_RX_SHUTDOWN       = 0x02
CMD_RX_DISCONNECT     = 0x03
CMD_RX_BATTERY_VALUE  = 0x50
CMD_RX_CAMERA_MODE    = 0x52


def build_frame(cmd: int, payload: bytes = b'') -> bytes:
    """
    组装出向帧: [HEAD 3B][CMD 1B][END|SN 1B][SIZE 1B][DATA]
    单帧: END_BIT=0x80, SN=0, 即 END|SN = 0x80
    """
    sn_end = FRAME_END_BIT  # 单帧模式
    size = len(payload)
    frame = FRAME_HEAD_OUTBOUND + bytes([cmd, sn_end, size]) + payload
    return frame


def parse_frame(data: bytes):
    """
    解析入向帧. 返回 (cmd, payload_bytes) 或 (None, None) 表示解析失败.
    帧结构: [HEAD 3B][CMD 1B][END|SN 1B][SIZE 1B][DATA SIZE B]
    """
    if len(data) < 6:
        return None, None
    if data[:3] != FRAME_HEAD_INBOUND:
        logger.debug(f"parse_frame: bad HEAD {data[:3].hex()}")
        return None, None
    cmd  = data[3]
    size = data[5]
    if len(data) < 6 + size:
        logger.debug(f"parse_frame: truncated, need {6+size}, got {len(data)}")
        return None, None
    payload = data[6:6 + size]
    return cmd, payload


class BLEConnector(QObject):
    """BLE 连接器 (BTCTRL 协议)"""
    
    # 信号定义
    device_found = Signal(dict)    # 设备发现信号：{name, address, rssi}
    connected = Signal(dict)       # 连接成功信号：{name, address}
    disconnected = Signal()        # 断开连接信号
    data_received = Signal(bytes)  # 原始数据接收信号 (已解帧 payload)
    battery_updated = Signal(int)  # 电量更新信号 (0-100)
    gesture_received = Signal(int) # 手势按键信号: button_id (0=Button1 单击)
    error_occurred = Signal(str)   # 错误信号
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.is_connected = False
        self.current_address = None
    
    @Slot(float)
    async def scan(self, timeout=5.0):
        """扫描设备 (自动过滤 CyberWand)"""
        logger.info(f"开始扫描 BLE 设备，超时：{timeout}秒")

        def callback(device, advertisement_data):
            """设备发现回调"""
            name = device.name or ''
            # 只上报 CyberWand 相关设备, 避免列表过长
            if 'CyberWand' in name:
                device_info = {
                    'name': name or 'Unknown',
                    'address': device.address,
                    'rssi': advertisement_data.rssi
                }
                logger.debug(f"发现目标设备：{device_info}")
                self.device_found.emit(device_info)

        try:
            await BleakScanner.discover(timeout=timeout, callback=callback)
            logger.info("扫描完成")
        except Exception as e:
            logger.error(f"扫描失败：{e}")
            self.error_occurred.emit(f"扫描失败：{str(e)}")
    
    @Slot(str)
    async def connect(self, address):
        """连接设备 (BTCTRL 协议)"""
        logger.info(f"尝试连接设备：{address}")

        try:
            self.client = BleakClient(address, disconnected_callback=self._on_disconnect_cb)
            await self.client.connect()
            self.is_connected = True
            self.current_address = address

            device_info = {
                'name': (self.client.device.name if self.client.device else None) or 'CyberWand',
                'address': address
            }
            logger.info(f"连接成功：{device_info}")
            self.connected.emit(device_info)

            # 启动 Notify 通知监听
            await self.start_notifications()

            # 读取标准 Battery Level
            await self.read_battery_level()

        except BleakError as e:
            logger.error(f"连接失败：{e}")
            self.error_occurred.emit(f"连接失败：{str(e)}")
        except Exception as e:
            logger.error(f"未知错误：{e}")
            self.error_occurred.emit(f"未知错误：{str(e)}")
    
    def _on_disconnect_cb(self, client):
        """Bleak 断开回调 (在 asyncio 线程调用)"""
        logger.info("BLE 连接已断开 (bleak callback)")
        self.is_connected = False
        self.current_address = None
        self.disconnected.emit()

    @Slot()
    async def disconnect(self):
        """断开连接"""
        if self.client and self.is_connected:
            logger.info("断开连接")
            try:
                await self.client.disconnect()
                self.is_connected = False
                self.current_address = None
                self.disconnected.emit()
                logger.info("已断开连接")
            except Exception as e:
                logger.error(f"断开连接失败：{e}")
                self.error_occurred.emit(f"断开连接失败：{str(e)}")

    async def start_notifications(self):
        """启动通知监听"""
        if not self.client or not self.is_connected:
            return

        try:
            await self.client.start_notify(
                CYBERWAND_NOTIFY_UUID,
                self.notification_handler
            )
            logger.info("已启动通知监听")
        except Exception as e:
            logger.error(f"启动通知失败：{e}")
            self.error_occurred.emit(f"启动通知失败：{str(e)}")
    
    def notification_handler(self, sender, data):
        """通知处理回调"""
        logger.debug(f"收到数据：{data.hex()}")
        self.data_received.emit(data)
        
        # 解析数据并处理
        self.parse_notification_data(data)
    
    def parse_notification_data(self, data):
        """解析通知数据"""
        if len(data) < 1:
            return
        
        # 数据类型标识
        data_type = data[0]
        
        if data_type == 0x01:  # 传感器数据
            self.parse_sensor_data(data[1:])
        elif data_type == 0x02:  # 手势事件
            self.parse_gesture_event(data[1:])
        elif data_type == 0x03:  # 电量更新
            if len(data) > 1:
                self.battery_updated.emit(data[1])
    
    def parse_sensor_data(self, data):
        """解析传感器数据"""
        # 数据格式：[Ax, Ay, Az, Gx, Gy, Gz] (各 2 字节)
        if len(data) < 12:
            return
        
        # 解析加速度和陀螺仪数据
        # 这里可以根据实际协议解析
        pass
    
    def parse_gesture_event(self, data):
        """解析手势事件"""
        if len(data) < 1:
            return
        
        gesture_id = data[0]
        # 根据 gesture_id 触发相应事件
        # 0x01: 挥舞向左
        # 0x02: 挥舞向右
        # 0x03: 顺时针旋转
        # 0x04: 逆时针旋转
        # 0x05: 画圈
        # 0x06: 双击
    
    async def read_battery_level(self):
        """读取电量"""
        if not self.client or not self.is_connected:
            return

        try:
            battery_data = await self.client.read_gatt_char(BATTERY_LEVEL_UUID)
            if battery_data:
                battery_level = battery_data[0]
                self.battery_updated.emit(battery_level)
                logger.info(f"电量：{battery_level}%")
        except Exception as e:
            logger.error(f"读取电量失败：{e}")
    
    async def send_command(self, command):
        """发送命令"""
        if not self.client or not self.is_connected:
            logger.warning("设备未连接，无法发送命令")
            return

        try:
            if isinstance(command, str):
                command = command.encode('utf-8')

            await self.client.write_gatt_char(
                CYBERWAND_WRITE_UUID,
                command
            )
            logger.debug(f"发送命令：{command.hex()}")
        except Exception as e:
            logger.error(f"发送命令失败：{e}")
            self.error_occurred.emit(f"发送命令失败：{str(e)}")
    
    async def send_gesture_mapping(self, mapping):
        """发送手势映射配置"""
        # 编码手势映射为二进制协议
        # 协议格式：[命令字 0x10][手势 ID][动作 ID][手势 ID][动作 ID]...
        command = bytes([0x10])  # 手势配置命令
        
        gesture_map = {
            'wave_left': 0x01,
            'wave_right': 0x02,
            'rotate_cw': 0x03,
            'rotate_ccw': 0x04,
            'circle': 0x05,
            'double_tap': 0x06
        }
        
        action_map = {
            'page_prev': 0x01,
            'page_next': 0x02,
            'volume_up': 0x03,
            'volume_down': 0x04,
            'play_pause': 0x05,
            'screenshot': 0x06,
            'none': 0x00
        }
        
        for gesture_name, action_name in mapping.items():
            if gesture_name in gesture_map and action_name in action_map:
                command += bytes([gesture_map[gesture_name], action_map[action_name]])
        
        await self.send_command(command)
    
    async def send_sensitivity(self, sensitivity):
        """发送灵敏度配置"""
        # 协议格式：[命令字 0x11][灵敏度值 0-100]
        command = bytes([0x11, sensitivity])
        await self.send_command(command)
    
    def get_connection_status(self):
        """获取连接状态"""
        return {
            'is_connected': self.is_connected,
            'address': self.current_address,
            'client': self.client is not None
        }
