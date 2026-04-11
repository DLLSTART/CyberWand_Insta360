#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CyberWand 飞书机器人 - 上位机配置服务
功能：
1. 通过飞书小程序连接魔杖
2. 修改动作识别参数
3. 配置蓝牙指令映射
4. 实时查看传感器数据
"""

import asyncio
import json
import websockets
from aiohttp import web
import bleak
from bleak import BleakClient, BleakScanner
from datetime import datetime
import os

# ==================== 配置参数 ====================

# BLE UUIDs (CyberWand)
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

# 动作映射配置
ACTION_MAPPINGS = {
    "wave": {"command": "0x01", "description": "挥手切换"},
    "rotate_cw": {"command": "0x02", "description": "顺时针旋转"},
    "rotate_ccw": {"command": "0x03", "description": "逆时针旋转"},
    "tap": {"command": "0x04", "description": "轻敲"},
    "shake": {"command": "0x05", "description": "摇晃"},
    "point_up": {"command": "0x06", "description": "指向上方"},
    "point_down": {"command": "0x07", "description": "指向下方"},
    "still": {"command": "0x00", "description": "静止"},
}

# 姿态识别参数
POSE_PARAMS = {
    "gyro_threshold": 150,      # 陀螺仪阈值
    "accel_threshold": 200,     # 加速度阈值
    "fusion_weight": 0.7,       # 融合权重
    "debounce_ms": 100,         # 防抖时间
    "sample_rate": 100,         # 采样率 Hz
}

# ==================== 蓝牙连接管理 ====================

class CyberWandBLE:
    """CyberWand 蓝牙连接管理"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.device_address = None
        self.notification_callback = None
    
    async def scan(self, timeout=5.0):
        """扫描附近的 CyberWand 设备"""
        devices = []
        print(f"开始扫描 BLE 设备 ({timeout}秒)...")
        
        detection_callback = lambda d: devices.append(d)
        
        async with BleakScanner(detection_callback=detection_callback) as scanner:
            await asyncio.sleep(timeout)
        
        # 过滤 CyberWand 设备
        cyberwands = [
            d for d in devices 
            if d.name and ("CyberWand" in d.name or "Insta360" in d.name)
        ]
        
        return cyberwands
    
    async def connect(self, address):
        """连接到指定设备"""
        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected = True
            self.device_address = address
            print(f"已连接到 {address}")
            return True
        except Exception as e:
            print(f"连接失败：{e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self.connected = False
            print("已断开连接")
    
    async def send_command(self, command_bytes):
        """发送指令"""
        if not self.connected:
            return False
        
        try:
            await self.client.write_gatt_char(
                CHARACTERISTIC_UUID,
                bytes(command_bytes),
                response=True
            )
            return True
        except Exception as e:
            print(f"发送失败：{e}")
            return False
    
    async def start_notifications(self, callback):
        """启动通知接收"""
        self.notification_callback = callback
        
        def handler(sender, data):
            if callback:
                callback(data)
        
        await self.client.start_notify(CHARACTERISTIC_UUID, handler)
        print("已启动通知")
    
    async def stop_notifications(self):
        """停止通知"""
        if self.client:
            await self.client.stop_notify(CHARACTERISTIC_UUID)
    
    async def get_battery_level(self):
        """获取电量"""
        # 假设电量特征 UUID
        battery_uuid = "00002a19-0000-1000-8000-00805f9b34fb"
        try:
            data = await self.client.read_gatt_char(battery_uuid)
            return data[0]
        except:
            return None
    
    async def update_mapping(self, action, command):
        """更新动作映射"""
        cmd_bytes = [0x10, action, command]  # 0x10=配置命令
        return await self.send_command(cmd_bytes)
    
    async def update_pose_params(self, params):
        """更新姿态识别参数"""
        cmd_bytes = [
            0x11,  # 0x11=参数配置命令
            params.get("gyro_threshold", 150) & 0xFF,
            params.get("accel_threshold", 200) & 0xFF,
            params.get("fusion_weight", 70) & 0xFF,  # 0.7 -> 70
            params.get("debounce_ms", 100) & 0xFF,
            params.get("sample_rate", 100) & 0xFF,
        ]
        return await self.send_command(cmd_bytes)

# ==================== 飞书 API 处理 ====================

class FeishuBotHandler:
    """飞书机器人事件处理"""
    
    def __init__(self, wand_ble):
        self.wand = wand_ble
        self.mappings = ACTION_MAPPINGS.copy()
        self.pose_params = POSE_PARAMS.copy()
    
    async def handle_event(self, event):
        """处理飞书事件"""
        header = event.get("header", {})
        event_type = header.get("event_type")
        
        if event_type == "url_verification":
            return {"challenge": event.get("challenge")}
        
        elif event_type == "im.message.receive_v1":
            return await self.handle_message(event)
        
        elif event_type == "interactive_card.action":
            return await self.handle_card_action(event)
        
        return {}
    
    async def handle_message(self, event):
        """处理消息事件"""
        message = event.get("event", {}).get("message", {})
        content = json.loads(message.get("content", "{}"))
        text = content.get("text", "")
        
        # 解析命令
        if text.startswith("/connect"):
            return await self.cmd_connect()
        elif text.startswith("/scan"):
            return await self.cmd_scan()
        elif text.startswith("/mapping"):
            return await self.cmd_mapping(text)
        elif text.startswith("/pose"):
            return await self.cmd_pose(text)
        elif text.startswith("/status"):
            return await self.cmd_status()
        elif text.startswith("/help"):
            return await self.cmd_help()
        
        return {}
    
    async def cmd_scan(self):
        """扫描设备命令"""
        devices = await self.wand.scan(timeout=5.0)
        
        if not devices:
            return self._create_card("未找到 CyberWand 设备", "请确保魔杖已开机并靠近电脑")
        
        device_list = "\n".join([
            f"• {d.name} ({d.address})" 
            for d in devices[:5]
        ])
        
        return self._create_card(
            "发现 CyberWand 设备",
            f"找到 {len(devices)} 个设备：\n{device_list}",
            actions=[
                {"text": "连接第一个", "value": f"connect:{devices[0].address}"}
            ]
        )
    
    async def cmd_connect(self):
        """连接设备命令"""
        # 简化：自动连接第一个发现的设备
        devices = await self.wand.scan(timeout=3.0)
        
        if not devices:
            return self._create_card("连接失败", "未找到设备")
        
        success = await self.wand.connect(devices[0].address)
        
        if success:
            battery = await self.wand.get_battery_level()
            battery_text = f"{battery}%" if battery else "未知"
            
            return self._create_card(
                "✅ 连接成功",
                f"设备：{devices[0].name}\n电量：{battery_text}",
                actions=[
                    {"text": "查看映射", "value": "view_mapping"},
                    {"text": "修改参数", "value": "edit_pose"},
                    {"text": "断开连接", "value": "disconnect"}
                ]
            )
        else:
            return self._create_card("连接失败", "请重试")
    
    async def cmd_mapping(self, text):
        """查看/修改映射命令"""
        parts = text.split()
        
        if len(parts) == 1:
            # 查看当前映射
            mapping_text = "\n".join([
                f"{k}: {v['command']} ({v['description']})"
                for k, v in self.mappings.items()
            ])
            return self._create_card("动作映射表", mapping_text)
        
        elif len(parts) == 3:
            # 修改映射：/mapping wave 0x01
            action, command = parts[1], parts[2]
            
            if action in self.mappings:
                self.mappings[action]["command"] = command
                
                # 同步到设备
                if self.wand.connected:
                    await self.wand.update_mapping(
                        list(self.mappings.keys()).index(action),
                        int(command, 16)
                    )
                
                return self._create_card(
                    "✅ 映射已更新",
                    f"{action} → {command}"
                )
        
        return self._create_card("命令格式错误", "/mapping <动作> <指令>")
    
    async def cmd_pose(self, text):
        """查看/修改姿态参数命令"""
        parts = text.split()
        
        if len(parts) == 1:
            # 查看当前参数
            params_text = "\n".join([
                f"{k}: {v}"
                for k, v in self.pose_params.items()
            ])
            return self._create_card("姿态识别参数", params_text)
        
        elif len(parts) == 3:
            # 修改参数：/pose gyro_threshold 180
            key, value = parts[1], int(parts[2])
            
            if key in self.pose_params:
                self.pose_params[key] = value
                
                # 同步到设备
                if self.wand.connected:
                    await self.wand.update_pose_params(self.pose_params)
                
                return self._create_card(
                    "✅ 参数已更新",
                    f"{key} = {value}"
                )
        
        return self._create_card("命令格式错误", "/pose <参数名> <值>")
    
    async def cmd_status(self):
        """查看状态命令"""
        if not self.wand.connected:
            return self._create_card("未连接", "请先连接设备")
        
        battery = await self.wand.get_battery_level()
        
        return self._create_card(
            "设备状态",
            f"连接：✅\n电量：{battery}%\n映射：{len(self.mappings)}个动作"
        )
    
    async def cmd_help(self):
        """帮助命令"""
        help_text = """
可用命令：
/scan - 扫描设备
/connect - 连接设备
/mapping - 查看/修改动作映射
/pose - 查看/修改姿态参数
/status - 查看设备状态

卡片操作：
点击卡片按钮可快速操作
"""
        return self._create_card("CyberWand 帮助", help_text)
    
    def _create_card(self, title, content, actions=None):
        """创建飞书交互卡片"""
        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"**{title}**",
                    "text_size": "normal"
                },
                {
                    "tag": "plain_text",
                    "content": content,
                    "text_size": "normal"
                }
            ]
        }
        
        if actions:
            card["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": a["text"]},
                        "value": json.dumps({"action": a["value"]})
                    }
                    for a in actions
                ]
            })
        
        return {"card": card}

# ==================== WebSocket 服务器 ====================

async def websocket_handler(websocket, path):
    """WebSocket 处理 - 用于飞书小程序实时通信"""
    print("小程序已连接")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get("command")
            
            if cmd == "scan":
                # 扫描设备
                devices = await wand.scan(timeout=3.0)
                response = {
                    "type": "scan_result",
                    "devices": [
                        {"name": d.name, "address": d.address}
                        for d in devices
                    ]
                }
                await websocket.send(json.dumps(response))
            
            elif cmd == "connect":
                # 连接设备
                address = data.get("address")
                success = await wand.connect(address)
                await websocket.send(json.dumps({
                    "type": "connect_result",
                    "success": success
                }))
            
            elif cmd == "update_mapping":
                # 更新映射
                action = data.get("action")
                command = data.get("command")
                await ws.send(json.dumps({"status": "ok", "message": "映射已更新"}))
            
            elif cmd == "get_sensor_data":
                # 获取传感器数据
                sensor_data = {"gyro_x": 0, "gyro_y": 0, "gyro_z": 0, "acc_x": 0, "acc_y": 0, "acc_z": 0}
                await ws.send(json.dumps({"status": "ok", "data": sensor_data}))
    
    except websockets.exceptions.ConnectionClosed:
        print("小程序已断开")

# ==================== 主程序 ====================

wand = CyberWandBLE()
handler = FeishuBotHandler(wand)

async def main():
    # 启动 WebSocket 服务器（飞书小程序连接）
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("WebSocket 服务器已启动：ws://localhost:8765")
    
    # 保持运行
    await asyncio.Future()

if __name__ == "__main__":
    print("CyberWand 飞书机器人启动中...")
    asyncio.run(main())
