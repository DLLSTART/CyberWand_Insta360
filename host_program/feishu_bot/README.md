# CyberWand 飞书小程序配置

## 一、创建步骤

### 1. 登录飞书开放平台
网址：https://open.feishu.cn

### 2. 创建企业自建应用
1. 进入「应用开发」→「企业自建」
2. 点击「创建应用」
3. 填写应用信息：
   - **应用名称**: CyberWand 控制器
   - **应用图标**: 上传魔杖 logo
   - **应用描述**: 赛博魔杖上位机配置工具

### 3. 配置应用能力

#### 3.1 添加机器人
1. 进入「应用功能」→「机器人」
2. 点击「添加机器人」
3. 配置：
   - **机器人名称**: CyberWand Assistant
   - **头像**: 魔杖图标
   - **功能**: 接收消息、发送消息、交互卡片

#### 3.2 配置事件订阅
1. 进入「事件订阅」
2. 启用事件：
   - ✅ `im.message.receive_v1` - 接收消息
   - ✅ `interactive_card.action` - 卡片按钮点击
3. 配置请求地址：
   ```
   https://your-server.com/feishu/event
   ```
4. 验证令牌（Verification Token）：
   - 复制到 `.env` 文件的 `FEISHU_VERIFICATION_TOKEN`

#### 3.3 配置权限
1. 进入「权限管理」
2. 申请权限：
   - ✅ `im:message` - 发送和接收消息
   - ✅ `im:chat` - 访问群聊信息
   - ✅ `contact:user.id:readonly` - 获取用户 ID

### 4. 创建飞书小程序

#### 4.1 小程序配置
1. 进入「应用功能」→「小程序」
2. 点击「创建小程序」
3. 填写信息：
   - **小程序名称**: CyberWand 控制器
   - **分类**: 工具 - 效率工具

#### 4.2 小程序代码
```html
<!-- pages/index/index.html -->
<view class="container">
  <view class="header">
    <text class="title">CyberWand 控制器</text>
  </view>
  
  <!-- 连接状态 -->
  <view class="status-card">
    <text class="status-label">连接状态:</text>
    <text class="status-value {{connected ? 'connected' : 'disconnected'}}">
      {{connected ? '已连接' : '未连接'}}
    </text>
  </view>
  
  <!-- 设备选择 -->
  <view class="section">
    <text class="section-title">可用设备</text>
    <button class="btn-scan" bindtap="scanDevices">扫描设备</button>
    <view class="device-list">
      <view class="device-item" wx:for="{{devices}}" wx:key="address" bindtap="connectDevice" data-address="{{item.address}}">
        <text>{{item.name}}</text>
        <text class="device-address">{{item.address}}</text>
      </view>
    </view>
  </view>
  
  <!-- 动作映射 -->
  <view class="section">
    <text class="section-title">动作映射配置</text>
    <view class="mapping-list">
      <view class="mapping-item" wx:for="{{mappings}}" wx:key="action">
        <text class="mapping-action">{{item.action}}</text>
        <input class="mapping-input" value="{{item.command}}" bindchange="updateMapping" data-action="{{item.action}}" />
        <text class="mapping-desc">{{item.description}}</text>
      </view>
    </view>
  </view>
  
  <!-- 姿态参数 -->
  <view class="section">
    <text class="section-title">姿态识别参数</text>
    <view class="param-list">
      <view class="param-item">
        <text>陀螺仪阈值:</text>
        <slider value="{{poseParams.gyro_threshold}}" bindchange="updatePoseParam" data-key="gyro_threshold" min="50" max="500" />
        <text>{{poseParams.gyro_threshold}}</text>
      </view>
      <view class="param-item">
        <text>加速度阈值:</text>
        <slider value="{{poseParams.accel_threshold}}" bindchange="updatePoseParam" data-key="accel_threshold" min="100" max="500" />
        <text>{{poseParams.accel_threshold}}</text>
      </view>
      <view class="param-item">
        <text>融合权重:</text>
        <slider value="{{poseParams.fusion_weight}}" bindchange="updatePoseParam" data-key="fusion_weight" min="0" max="100" />
        <text>{{poseParams.fusion_weight / 100}}</text>
      </view>
    </view>
  </view>
  
  <!-- 实时传感器数据 -->
  <view class="section">
    <text class="section-title">实时传感器数据</text>
    <view class="sensor-data">
      <view class="data-row">
        <text>陀螺仪:</text>
        <text>X: {{sensor.gyro_x}}, Y: {{sensor.gyro_y}}, Z: {{sensor.gyro_z}}</text>
      </view>
      <view class="data-row">
        <text>加速度:</text>
        <text>X: {{sensor.acc_x}}, Y: {{sensor.acc_y}}, Z: {{sensor.acc_z}}</text>
      </view>
      <view class="data-row">
        <text>电量:</text>
        <text>{{sensor.battery}}%</text>
      </view>
    </view>
  </view>
  
  <!-- 操作按钮 -->
  <view class="actions">
    <button class="btn-primary" bindtap="saveConfig">保存配置</button>
    <button class="btn-secondary" bindtap="disconnect">断开连接</button>
  </view>
</view>
```

```javascript
// pages/index/index.js
Page({
  data: {
    connected: false,
    devices: [],
    mappings: [],
    poseParams: {
      gyro_threshold: 150,
      accel_threshold: 200,
      fusion_weight: 70,
      debounce_ms: 100,
      sample_rate: 100
    },
    sensor: {
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: 0,
      acc_x: 0,
      acc_y: 0,
      acc_z: 0,
      battery: 0
    }
  },
  
  onLoad() {
    this.connectWebSocket();
  },
  
  // 连接 WebSocket
  connectWebSocket() {
    const socket = tt.connectSocket({
      url: 'ws://localhost:8765',
      success: () => {
        console.log('WebSocket 连接成功');
        
        socket.onMessage((res) => {
          const data = JSON.parse(res.data);
          this.handleSocketMessage(data);
        });
      }
    });
    
    this.socket = socket;
  },
  
  // 处理 WebSocket 消息
  handleSocketMessage(data) {
    switch(data.type) {
      case 'scan_result':
        this.setData({ devices: data.devices });
        break;
      case 'connect_result':
        this.setData({ connected: data.success });
        break;
      case 'sensor_update':
        this.setData({ sensor: data.sensor });
        break;
    }
  },
  
  // 扫描设备
  scanDevices() {
    this.socket.send({
      data: JSON.stringify({ command: 'scan' })
    });
  },
  
  // 连接设备
  connectDevice(e) {
    const address = e.currentTarget.dataset.address;
    this.socket.send({
      data: JSON.stringify({
        command: 'connect',
        address: address
      })
    });
  },
  
  // 更新映射
  updateMapping(e) {
    const action = e.currentTarget.dataset.action;
    const command = e.detail.value;
    
    this.socket.send({
      data: JSON.stringify({
        command: 'update_mapping',
        action: action,
        command: command
      })
    });
  },
  
  // 更新姿态参数
  updatePoseParam(e) {
    const key = e.currentTarget.dataset.key;
    const value = parseInt(e.detail.value);
    
    this.setData({
      [`poseParams.${key}`]: value
    });
    
    this.socket.send({
      data: JSON.stringify({
        command: 'update_pose_param',
        key: key,
        value: value
      })
    });
  },
  
  // 保存配置
  saveConfig() {
    tt.showToast({
      title: '配置已保存',
      icon: 'success'
    });
  },
  
  // 断开连接
  disconnect() {
    this.socket.send({
      data: JSON.stringify({ command: 'disconnect' })
    });
    this.setData({ connected: false });
  }
});
```

```css
/* pages/index/index.wxss */
.container {
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
}

.status-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  background: #f5f5f5;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

.status-label {
  font-size: 28rpx;
  color: #666;
}

.status-value {
  font-size: 28rpx;
  font-weight: bold;
}

.status-value.connected {
  color: #07c160;
}

.status-value.disconnected {
  color: #ee0a24;
}

.section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
  display: block;
}

.btn-scan {
  width: 100%;
  background: #3480f0;
  color: white;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.device-list,
.mapping-list,
.param-list {
  background: #fff;
  border-radius: 12rpx;
  overflow: hidden;
}

.device-item {
  padding: 30rpx;
  border-bottom: 1px solid #eee;
}

.device-address {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.mapping-item,
.param-item {
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  border-bottom: 1px solid #eee;
}

.mapping-action {
  width: 120rpx;
  font-weight: bold;
}

.mapping-input {
  flex: 1;
  height: 60rpx;
  border: 1px solid #ddd;
  border-radius: 8rpx;
  padding: 0 16rpx;
  margin: 0 20rpx;
}

.mapping-desc {
  width: 150rpx;
  font-size: 24rpx;
  color: #999;
}

.param-item {
  justify-content: space-between;
}

.param-item slider {
  flex: 1;
  margin: 0 20rpx;
}

.sensor-data {
  background: #f5f5f5;
  padding: 30rpx;
  border-radius: 12rpx;
}

.data-row {
  display: flex;
  justify-content: space-between;
  padding: 10rpx 0;
  font-size: 28rpx;
}

.actions {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  border-radius: 12rpx;
}

.btn-primary {
  background: #3480f0;
  color: white;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}
```

### 5. 部署与测试

#### 5.1 本地测试
```bash
# 安装依赖
pip install aiohttp websockets bleak

# 配置环境变量
export FEISHU_APP_ID=xxx
export FEISHU_APP_SECRET=xxx
export FEISHU_VERIFICATION_TOKEN=xxx

# 启动服务
python cyberwand_feishu_bot.py
```

#### 5.2 飞书小程序上传
1. 进入「版本管理」
2. 上传小程序代码包
3. 提交审核

#### 5.3 发布应用
1. 审核通过后发布
2. 在飞书中添加该应用
3. 开始使用

---

## 二、飞书机器人命令

### 可用命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `/scan` | 扫描附近魔杖 | `/scan` |
| `/connect` | 连接设备 | `/connect` |
| `/mapping` | 查看映射表 | `/mapping` |
| `/mapping <动作> <指令>` | 修改映射 | `/mapping wave 0x01` |
| `/pose` | 查看参数 | `/pose` |
| `/pose <参数> <值>` | 修改参数 | `/pose gyro_threshold 180` |
| `/status` | 查看状态 | `/status` |
| `/help` | 帮助 | `/help` |

### 交互卡片示例

```json
{
  "config": {
    "wide_screen_mode": true
  },
  "elements": [
    {
      "tag": "plain_text",
      "content": "**CyberWand 设备状态**",
      "text_size": "normal"
    },
    {
      "tag": "plain_text",
      "content": "连接：✅\n电量：85%\n动作映射：8 个",
      "text_size": "normal"
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "查看映射"
          },
          "value": "{\"action\": \"view_mapping\"}"
        },
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "修改参数"
          },
          "value": "{\"action\": \"edit_pose\"}"
        },
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "断开连接"
          },
          "value": "{\"action\": \"disconnect\"}"
        }
      ]
    }
  ]
}
```

---

## 三、BLE 通信协议

### 指令格式

```
[命令字] [参数 1] [参数 2] ... [校验和]
```

### 命令列表

| 命令字 | 功能 | 参数 |
|--------|------|------|
| `0x01-0x0F` | 动作指令 | 无 |
| `0x10` | 更新映射 | [动作 ID][新指令] |
| `0x11` | 更新参数 | [陀螺阈值][加速度阈值][融合权重][防抖时间][采样率] |
| `0x20` | 查询电量 | 无 |
| `0x21` | 查询传感器 | 无 |

### 示例

```python
# 更新挥手动作为 0x01
cmd = [0x10, 0x00, 0x01]  # 0x00=挥手动作 ID
checksum = sum(cmd) % 256
cmd.append(checksum)
await client.write_gatt_char(uuid, bytes(cmd))

# 更新姿态参数
cmd = [0x11, 180, 200, 70, 100, 100]  # 阈值 180/200，权重 0.7，防抖 100ms，采样 100Hz
checksum = sum(cmd) % 256
cmd.append(checksum)
await client.write_gatt_char(uuid, bytes(cmd))
```

---

## 四、部署清单

- [ ] 飞书开放平台创建应用
- [ ] 配置机器人和事件订阅
- [ ] 申请权限
- [ ] 创建小程序
- [ ] 上传小程序代码
- [ ] 配置本地服务
- [ ] 测试连接
- [ ] 提交审核
- [ ] 发布应用

---

**创建时间**: 2026-04-07  
**创建人**: 太子
