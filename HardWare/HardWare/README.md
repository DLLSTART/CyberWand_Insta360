# HardWare 硬件设计目录

## 📁 目录结构

```
HardWare/
├── README.md                       # 本文件
├── hardware_specifications.md      # 硬件规格说明（核心文档）
├── hardwarelist.md                 # 硬件元器件清单（核心文档）
├── circuit_diagram.md              # 电路图说明（核心文档）
├── cyberwand.kicad_sch             # KiCad原理图文件
├── cyberwand.kicad_pcb             # KiCad PCB文件
├── cyberwand.kicad_pro             # KiCad项目文件
├── cyberwand.kicad_prl             # KiCad项目本地设置
├── fp-info-cache                   # KiCad封装库缓存（自动生成）
└── docs/                           # 技术文档和参考资料
    ├── ESP32-S3-WROOM-1-N16R8_PINOUT.md
    ├── footprint_mapping.md
    ├── footprint_verification.md
    ├── FLOATING_PINS_FIXED.md
    ├── FLOATING_PINS_GUIDE.md
    ├── KICAD_SCHEMATIC_GENERATION_GUIDE.md
    ├── KICAD_SYMBOL_MAPPING.md
    └── SYMBOL_LIBRARY_MAPPING_COMPLETE.md
```

## 📖 核心文档说明

### hardware_specifications.md
完整的硬件规格说明，包括：
- 系统架构
- 各模块详细规格
- 电气特性
- 接口定义

### hardwarelist.md
元器件清单（BOM），包括：
- 所有元器件列表
- 型号和数量
- 参考价格
- 采购链接

### circuit_diagram.md
电路图说明文档，包括：
- 电路模块说明
- 连接关系
- 设计要点

## 🔧 KiCad项目文件

### cyberwand.kicad_pro
KiCad主项目文件，包含项目设置和配置。

### cyberwand.kicad_sch
原理图文件，由SKiDL自动生成。

**打开方式**：
```bash
# 启动KiCad
D:\kicad\bin\kicad.exe

# 打开项目
文件 → 打开项目 → cyberwand.kicad_pro
```

### cyberwand.kicad_pcb
PCB设计文件。

**导入网表**：
```
1. 打开PCB编辑器
2. 文件 → 导入 → 网表
3. 选择：../skidl/output/cyberwand_netlist.net
```

## 📚 技术文档（docs/）

### ESP32-S3-WROOM-1-N16R8_PINOUT.md
ESP32-S3模块的引脚定义和说明。

### footprint_mapping.md & footprint_verification.md
封装映射和验证文档，确保所有元器件的封装正确。

### FLOATING_PINS_*.md
浮空引脚处理指南和修复记录。

### KICAD_*.md
KiCad相关的配置和使用说明。

## 🚀 快速开始

### 1. 查看硬件设计
```bash
# 查看硬件规格
cat hardware_specifications.md

# 查看元器件清单
cat hardwarelist.md
```

### 2. 打开KiCad项目
```bash
# 启动KiCad并打开项目
D:\kicad\bin\kicad.exe
# 文件 → 打开项目 → cyberwand.kicad_pro
```

### 3. 生成或更新原理图
```bash
# 从SKiDL重新生成原理图
cd ../skidl
python generate_schematic.py
```

### 4. 导入网表到PCB
```bash
# 在KiCad PCB编辑器中
# 文件 → 导入 → 网表
# 选择：../skidl/output/cyberwand_netlist.net
```

## 🔄 与SKiDL集成

本硬件设计使用SKiDL（Python）进行电路描述和网表生成。

**工作流程**：
```
Python代码 (../skidl/) → 网表 → 原理图/PCB (这里)
```

**相关文档**：
- SKiDL代码：`../skidl/`
- 网表输出：`../skidl/output/cyberwand_netlist.net`
- 生成工具：`../skidl/generate_schematic.py`

## 📝 注意事项

### KiCad版本
- 推荐使用：**KiCad 9.0+**
- 安装路径：`D:\kicad\`

### 符号库配置
如果打开原理图时出现"找不到符号"错误，需要配置符号库：
```bash
# 运行根目录的配置脚本
..\auto_configure_kicad_symbols.bat
```

### 文件修改
- ✅ 可以直接编辑KiCad项目文件
- ⚠️ 核心MD文档请保持更新
- ❌ 不要手动修改 `fp-info-cache`

## 🛠️ 维护指南

### 更新硬件设计
1. 修改 `../skidl/cyberwand_circuit.py`
2. 重新生成网表和原理图
3. 更新核心文档
4. 提交Git

### 添加新元器件
1. 在 `../skidl/` 创建新的 `*_part.py`
2. 在 `cyberwand_circuit.py` 中引用
3. 更新 `hardwarelist.md`
4. 更新 `hardware_specifications.md`

### 文档维护
- 核心文档放在当前目录
- 技术细节和参考文档放在 `docs/`
- 保持文档与代码同步

---

**最后更新**: 2026-02-01  
**维护者**: CyberWand开发团队
