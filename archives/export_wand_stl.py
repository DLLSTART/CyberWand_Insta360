#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
魔杖 STL 自动导出脚本
功能：调用 OpenSCAD 命令行将 wand_reverse_v1.scad 渲染为 STL 文件
"""

import subprocess
import sys
import os
from pathlib import Path

# 配置
SCRIPT_DIR = Path(__file__).parent
SCAD_FILE = SCRIPT_DIR / "wand_reverse_v1.scad"
STL_FILE = SCRIPT_DIR / "wand_reverse_v1.stl"
OPENSCAD_PATHS = [
    r"C:\Program Files\OpenSCAD\openscad.exe",
    r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
    r"$env:LOCALAPPDATA\Programs\OpenSCAD\openscad.exe",
]

def find_openscad():
    """查找 OpenSCAD 安装路径"""
    for path in OPENSCAD_PATHS:
        # 处理环境变量路径
        if path.startswith("$env:"):
            env_var = path.split("\\")[0].replace("$env:", "")
            base_path = os.environ.get(env_var, "")
            path = path.replace(f"$env:{env_var}\\", base_path + "\\")
        
        if Path(path).exists():
            return path
    
    # 尝试从 PATH 中查找
    try:
        result = subprocess.run(["where", "openscad"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass
    
    return None

def export_stl():
    """导出 STL 文件"""
    print("=" * 60)
    print("魔杖 STL 导出工具")
    print("=" * 60)
    
    # 检查输入文件
    if not SCAD_FILE.exists():
        print(f"❌ 错误：找不到 SCAD 文件：{SCAD_FILE}")
        return False
    
    print(f"✓ 输入文件：{SCAD_FILE}")
    
    # 查找 OpenSCAD
    openscad = find_openscad()
    if not openscad:
        print("❌ 错误：找不到 OpenSCAD，请先安装！")
        print("   安装命令：winget install OpenSCAD.OpenSCAD")
        return False
    
    print(f"✓ OpenSCAD 路径：{openscad}")
    
    # 构建命令
    cmd = [
        openscad,
        "-o", str(STL_FILE),
        "--render",
        "--preview=throwaway",
        str(SCAD_FILE)
    ]
    
    print(f"✓ 输出文件：{STL_FILE}")
    print(f"\n执行命令：{' '.join(cmd)}\n")
    print("⏳ 正在渲染 STL 文件（约需 1-3 分钟）...")
    
    # 执行渲染
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 分钟超时
        )
        
        if result.returncode != 0:
            print(f"❌ 渲染失败！")
            print(f"错误输出：{result.stderr}")
            return False
        
        # 检查输出文件
        if STL_FILE.exists():
            file_size = STL_FILE.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✅ 渲染成功！")
            print(f"   文件：{STL_FILE}")
            print(f"   大小：{file_size:.2f} MB")
            print(f"\n📦 下一步：")
            print(f"   1. 用切片软件打开 STL 文件（如 Cura, PrusaSlicer）")
            print(f"   2. 设置打印参数（层高 0.15-0.2mm, 填充 15-20%）")
            print(f"   3. 生成 G-code 并发送到 3D 打印机")
            return True
        else:
            print(f"❌ 渲染完成但找不到输出文件！")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 渲染超时（>5 分钟），请手动运行 OpenSCAD！")
        return False
    except Exception as e:
        print(f"❌ 发生错误：{e}")
        return False

if __name__ == "__main__":
    success = export_stl()
    sys.exit(0 if success else 1)
