# CyberWand 赛博魔杖

> 直觉式空间交互设备 - 挥一挥，一切尽在掌握

**版本**: v3.0  
**状态**: 工程样机阶段  
**最后更新**: 2026-04-08

---

## 🎯 产品定位

CyberWand 是一款手势识别蓝牙遥控器，通过 6 自由度姿态追踪和 AI 手势识别，让用户通过直观的手势控制设备。

**核心场景**:
- 商务演示 - 挥一挥翻页，保持专业形象
- 直播创作 - 手势触发特效，不中断直播
- 智能家居 - 直觉式控制，老人小孩都会用
- 视频会议 - 快速静音/开关摄像头

---

## 📁 项目结构

```
CyberWand_Insta360/
├── docs/                       # 文档
│   ├── product_requirements_v3.md  # 需求文档
│   └── gstack_engineering_fix.md   # 工程修复报告
├── firmware/                   # 固件
│   └── cyberwand_esp/          # ESP32-S3 固件
├── enclosure/                  # 外壳设计
│   └── v21_final/              # v21.0 最终版
├── host_program/               # 上位机
│   └── feishu_bot/             # 飞书机器人
└── archives/                   # 归档文件（历史版本）
```

---

## 🚀 快速开始

### 固件开发
```bash
cd firmware/cyberwand_esp
idf.py build
idf.py flash
idf.py monitor
```

### 上位机
```bash
cd host_program/feishu_bot
pip install -r requirements.txt
python cyberwand_feishu_bot.py
```

---

## 📊 技术规格

| 项目 | 规格 |
|------|------|
| **主控** | ESP32-S3 |
| **传感器** | MPU6050（6 轴 IMU） |
| **连接** | BLE 5.3 |
| **电池** | 300mAh 锂电 |
| **续航** | > 8 小时 |
| **尺寸** | Φ22mm × 350mm |
| **重量** | < 150g |

---

## 📄 核心文档

| 文档 | 说明 |
|------|------|
| [产品需求](docs/product_requirements_v3.md) | 完整产品定义 |
| [工程修复](docs/gstack_engineering_fix.md) | GStack 标准修复报告 |

---

## 🛠️ 开发状态

| 阶段 | 完成度 | 说明 |
|------|--------|------|
| 产品定义 | ✅ 100% | 需求文档完成 |
| 技术设计 | ✅ 100% | 架构设计完成 |
| 固件开发 | ✅ 85% | 基础功能完成 |
| 硬件焊接 | ⏳ 待执行 | 需工程师介入 |
| 测试验证 | ⏳ 待执行 | 需真实硬件 |

---

## 📦 归档说明

`archives/` 目录包含：
- 历史版本设计文件（v34-v200）
- 旧版文档和代码
- 训练数据和参考资料
- PDF 数据手册

需要时可从归档中恢复。

---

## 📞 联系方式

- **项目负责**: 太子
- **产品负责**: 皇上
- **飞书应用**: CyberWand 控制器

---

## 📜 许可证

Apache-2.0

---

**最后更新**: 2026-04-08
