"""
环境设置脚本: 下载安装 Java JRE + Freerouter
- Java: Adoptium JRE 21 (Temurin)
- Freerouter: v2.1.0
- 安装到 D:\freerouter
- 添加到系统PATH
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil

INSTALL_DIR = r'D:\freerouter'
JAVA_DIR = os.path.join(INSTALL_DIR, 'jre')
FR_DIR = os.path.join(INSTALL_DIR, 'app')

# Adoptium JRE 21 Windows x64
JAVA_URL = 'https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse?project=jdk'
JAVA_ZIP = os.path.join(INSTALL_DIR, 'jre.zip')

# Freerouter v2.1.0 JAR
FR_URL = 'https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar'
FR_JAR = os.path.join(FR_DIR, 'freerouting-2.1.0.jar')


def download_file(url, dest, desc=""):
    """下载文件"""
    print(f"  下载 {desc}: {url}")
    print(f"  目标: {dest}")

    os.makedirs(os.path.dirname(dest), exist_ok=True)

    if os.path.exists(dest):
        print(f"  已存在, 跳过下载")
        return True

    try:
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest) / 1024 / 1024
        print(f"  下载完成 ({size:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ⚠ 下载失败: {e}")
        return False


def install_java():
    """安装 Java JRE"""
    print("\n[1/3] 安装 Java JRE 21...")

    # 检查是否已安装
    java_exe = os.path.join(JAVA_DIR, 'bin', 'java.exe')

    # 在JAVA_DIR下查找java.exe (可能在子目录中)
    if os.path.exists(JAVA_DIR):
        for root, dirs, files in os.walk(JAVA_DIR):
            if 'java.exe' in files:
                java_exe = os.path.join(root, 'java.exe')
                print(f"  Java已安装: {java_exe}")
                return java_exe

    if not download_file(JAVA_URL, JAVA_ZIP, "Adoptium JRE 21"):
        return None

    # 解压
    print("  解压 JRE...")
    os.makedirs(JAVA_DIR, exist_ok=True)

    with zipfile.ZipFile(JAVA_ZIP, 'r') as zf:
        zf.extractall(JAVA_DIR)

    # 找到java.exe
    for root, dirs, files in os.walk(JAVA_DIR):
        if 'java.exe' in files:
            java_exe = os.path.join(root, 'java.exe')
            print(f"  Java安装完成: {java_exe}")
            return java_exe

    print("  ⚠ 解压后未找到java.exe")
    return None


def install_freerouter():
    """安装 Freerouter"""
    print("\n[2/3] 安装 Freerouter v2.1.0...")

    os.makedirs(FR_DIR, exist_ok=True)

    if os.path.exists(FR_JAR):
        print(f"  Freerouter已安装: {FR_JAR}")
        return FR_JAR

    if download_file(FR_URL, FR_JAR, "Freerouter v2.1.0"):
        print(f"  Freerouter安装完成: {FR_JAR}")
        return FR_JAR

    return None


def setup_path(java_exe):
    """添加到系统PATH"""
    print("\n[3/3] 配置环境变量...")

    java_bin = os.path.dirname(java_exe)

    # 创建freerouter批处理启动脚本
    bat_file = os.path.join(INSTALL_DIR, 'freerouter.bat')
    with open(bat_file, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'"{java_exe}" -jar "{FR_JAR}" %*\n')
    print(f"  创建启动脚本: {bat_file}")

    # 创建DSN路由脚本
    route_bat = os.path.join(INSTALL_DIR, 'freeroute.bat')
    with open(route_bat, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'echo Freerouter v2.1.0 - 自动布线\n')
        f.write(f'echo 输入: %1\n')
        f.write(f'echo 输出: %2\n')
        f.write(f'"{java_exe}" -jar "{FR_JAR}" -gui.enabled=false -de %1 -do %2\n')
        f.write(f'echo 布线完成!\n')
    print(f"  创建路由脚本: {route_bat}")

    # 添加到系统PATH (使用setx)
    try:
        # 获取当前用户PATH
        result = subprocess.run(
            ['powershell', '-Command',
             '[Environment]::GetEnvironmentVariable("PATH", "User")'],
            capture_output=True, text=True
        )
        current_path = result.stdout.strip()

        if INSTALL_DIR not in current_path:
            new_path = f"{current_path};{INSTALL_DIR}"
            subprocess.run(
                ['powershell', '-Command',
                 f'[Environment]::SetEnvironmentVariable("PATH", "{new_path}", "User")'],
                capture_output=True, text=True
            )
            print(f"  已添加到用户PATH: {INSTALL_DIR}")
        else:
            print(f"  PATH中已包含: {INSTALL_DIR}")

        # 同时设置当前会话
        os.environ['PATH'] = f"{INSTALL_DIR};{java_bin};{os.environ.get('PATH', '')}"

    except Exception as e:
        print(f"  ⚠ PATH设置失败: {e}")
        print(f"  请手动添加到PATH: {INSTALL_DIR}")

    return bat_file


def verify():
    """验证安装"""
    print("\n验证安装...")

    # 查找java
    for root, dirs, files in os.walk(JAVA_DIR):
        if 'java.exe' in files:
            java_exe = os.path.join(root, 'java.exe')
            result = subprocess.run(
                [java_exe, '-version'],
                capture_output=True, text=True
            )
            print(f"  Java: {result.stderr.strip().split(chr(10))[0]}")
            break

    if os.path.exists(FR_JAR):
        size = os.path.getsize(FR_JAR) / 1024 / 1024
        print(f"  Freerouter: {FR_JAR} ({size:.1f} MB)")

    bat = os.path.join(INSTALL_DIR, 'freerouter.bat')
    if os.path.exists(bat):
        print(f"  启动脚本: {bat}")


def main():
    print("=" * 60)
    print("CyberWand - 环境设置")
    print("=" * 60)

    os.makedirs(INSTALL_DIR, exist_ok=True)

    java_exe = install_java()
    fr_jar = install_freerouter()

    if java_exe and fr_jar:
        setup_path(java_exe)
        verify()
        print("\n✅ 安装完成!")
        print(f"\n使用方法:")
        print(f"  freerouter.bat                     # 打开GUI")
        print(f"  freeroute.bat input.dsn output.ses  # 命令行自动布线")
    else:
        print("\n⚠ 安装未完成, 请检查网络连接")


if __name__ == '__main__':
    main()
