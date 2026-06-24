#!/usr/bin/env python3
"""
上传固件到 OTA 服务器.

用法:
    python upload_firmware_to_server.py <version> [firmware.bin]

示例:
    python upload_firmware_to_server.py 1.0.0
    python upload_firmware_to_server.py 1.1.0 path/to/firmware.bin
"""
import sys
import requests
from pathlib import Path

SERVER = "http://39.96.83.115:6666"
DEFAULT_FW = Path(__file__).parent.parent / ".pio/build/cyberwand/firmware.bin"


def main():
    if len(sys.argv) < 2:
        print("用法: python upload_firmware_to_server.py <version> [firmware.bin]")
        sys.exit(1)

    version = sys.argv[1]
    fw_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_FW

    if not fw_path.exists():
        print(f"固件文件不存在: {fw_path}")
        sys.exit(1)

    print(f"上传固件 v{version} ({fw_path.stat().st_size} bytes) 到 {SERVER}...")

    resp = requests.post(
        f"{SERVER}/firmware/upload",
        data={"product": "cyberwand", "version": version},
        files={"file": ("firmware.bin", fw_path.open("rb"), "application/octet-stream")}
    )

    if resp.ok:
        data = resp.json()
        print(f"上传成功!")
        print(f"  版本: {data.get('version')}")
        print(f"  大小: {data.get('size')} bytes")
        print(f"  SHA256: {data.get('sha256')}")
    else:
        print(f"上传失败: {resp.status_code} {resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
