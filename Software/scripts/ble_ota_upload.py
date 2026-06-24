#!/usr/bin/env python3
"""
BLE OTA 固件上传工具 (PC 端)
依赖: pip install bleak

用法:
    python ble_ota_upload.py firmware.bin [device_name]

默认搜索名为 "CyberWand" 的设备.
"""
import asyncio
import sys
import struct
from pathlib import Path

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("请先安装 bleak: pip install bleak")
    sys.exit(1)

# OTA Service UUIDs (16-bit 转 128-bit 标准格式)
OTA_CTRL_UUID   = "0000fe01-0000-1000-8000-00805f9b34fb"
OTA_DATA_UUID   = "0000fe02-0000-1000-8000-00805f9b34fb"
OTA_STATUS_UUID = "0000fe03-0000-1000-8000-00805f9b34fb"

# 状态码
STATUS_NAMES = {
    0x00: "IDLE", 0x01: "READY", 0x02: "RECEIVING", 0x03: "SUCCESS",
    0xE0: "ERR_BEGIN", 0xE1: "ERR_WRITE", 0xE2: "ERR_END",
    0xE3: "ERR_SIZE", 0xE4: "ERR_ABORT",
}

ota_status = None
ota_event = asyncio.Event()


def status_callback(sender, data):
    global ota_status
    if len(data) >= 1:
        ota_status = data[0]
        extra = int.from_bytes(data[1:5], "little") if len(data) >= 5 else 0
        name = STATUS_NAMES.get(ota_status, f"0x{ota_status:02X}")
        if ota_status == 0x02:
            print(f"\r  进度: {extra}%", end="", flush=True)
        else:
            print(f"\n  状态: {name} (extra={extra})")
        ota_event.set()


async def upload(fw_path: str, device_name: str = "CyberWand"):
    fw_data = Path(fw_path).read_bytes()
    fw_size = len(fw_data)
    print(f"固件: {fw_path} ({fw_size} bytes)")

    # 扫描设备
    print(f"正在扫描 BLE 设备 '{device_name}'...")
    device = await BleakScanner.find_device_by_name(device_name, timeout=10)
    if not device:
        print(f"未找到设备 '{device_name}'")
        return False

    print(f"已找到: {device.name} [{device.address}]")

    async with BleakClient(device, timeout=30) as client:
        print(f"已连接, MTU={client.mtu_size}")

        # 订阅状态通知
        await client.start_notify(OTA_STATUS_UUID, status_callback)

        # 发送 START 命令: [0x01][4B size LE]
        start_cmd = bytes([0x01]) + struct.pack("<I", fw_size)
        await client.write_gatt_char(OTA_CTRL_UUID, start_cmd, response=True)
        print("已发送 START 命令, 等待设备就绪...")

        ota_event.clear()
        await asyncio.wait_for(ota_event.wait(), timeout=5)
        if ota_status != 0x01:
            print(f"设备未就绪, 状态=0x{ota_status:02X}")
            return False

        # 分片发送固件数据
        # 使用 MTU-3 作为分片大小 (ATT header 3 bytes)
        chunk_size = min(client.mtu_size - 3, 500)
        print(f"开始传输 (chunk={chunk_size}B)...")

        offset = 0
        while offset < fw_size:
            end = min(offset + chunk_size, fw_size)
            chunk = fw_data[offset:end]
            await client.write_gatt_char(OTA_DATA_UUID, chunk, response=False)
            offset = end

        print(f"\n传输完成, 发送 END 命令...")

        # 发送 END 命令
        ota_event.clear()
        await client.write_gatt_char(OTA_CTRL_UUID, bytes([0x02]), response=True)

        try:
            await asyncio.wait_for(ota_event.wait(), timeout=10)
        except asyncio.TimeoutError:
            pass

        if ota_status == 0x03:
            print("OTA 成功! 设备即将重启.")
            return True
        else:
            print(f"OTA 失败, 最终状态=0x{ota_status:02X}")
            return False


def main():
    if len(sys.argv) < 2:
        print("用法: python ble_ota_upload.py <firmware.bin> [device_name]")
        sys.exit(1)

    fw_path = sys.argv[1]
    device_name = sys.argv[2] if len(sys.argv) > 2 else "CyberWand"

    if not Path(fw_path).exists():
        print(f"文件不存在: {fw_path}")
        sys.exit(1)

    success = asyncio.run(upload(fw_path, device_name))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
