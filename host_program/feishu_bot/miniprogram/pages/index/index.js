// CyberWand 控制器 - 主页面逻辑
Page({
  data: {
    // 连接状态
    connected: false,
    deviceName: '',
    deviceId: '',
    batteryLevel: 0,
    
    // 设备列表
    devices: [],
    selectedDevice: null,
    
    // 动作映射
    mappings: [
      { action: 'wave', command: '0x01', description: '挥手切换' },
      { action: 'rotate_cw', command: '0x02', description: '顺时针旋转' },
      { action: 'rotate_ccw', command: '0x03', description: '逆时针旋转' },
      { action: 'tap', command: '0x04', description: '轻敲' },
      { action: 'shake', command: '0x05', description: '摇晃' },
      { action: 'point_up', command: '0x06', description: '指向上方' },
      { action: 'point_down', command: '0x07', description: '指向下方' },
      { action: 'still', command: '0x00', description: '静止' }
    ],
    
    // 姿态参数
    poseParams: {
      gyro_threshold: 150,
      accel_threshold: 200,
      fusion_weight: 70,
      debounce_ms: 100,
      sample_rate: 100
    },
    
    // 传感器数据
    sensorData: {
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: 0,
      acc_x: 0,
      acc_y: 0,
      acc_z: 0
    },
    sensorUpdating: false,
    sensorInterval: null
  },
  
  onLoad() {
    console.log('CyberWand 小程序加载');
    this.initBluetooth();
  },
  
  onUnload() {
    // 清理蓝牙连接
    if (this.data.sensorInterval) {
      clearInterval(this.data.sensorInterval);
    }
    this.disconnectBLE();
  },
  
  // 初始化蓝牙
  initBluetooth() {
    tt.openBluetoothAdapter({
      success: (res) => {
        console.log('蓝牙初始化成功', res);
      },
      fail: (err) => {
        console.error('蓝牙初始化失败', err);
        tt.showToast({
          title: '蓝牙初始化失败',
          icon: 'none'
        });
      }
    });
  },
  
  // 扫描设备
  scanDevices() {
    tt.showLoading({ title: '扫描中...' });
    
    this.setData({ devices: [] });
    
    tt.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      interval: 1000,
      services: ['0000fff0-0000-1000-8000-00805f9b34fb'],
      success: (res) => {
        console.log('开始扫描', res);
      },
      fail: (err) => {
        console.error('扫描失败', err);
        tt.hideLoading();
        tt.showToast({
          title: '扫描失败',
          icon: 'none'
        });
      }
    });
    
    // 监听设备发现
    const onDeviceFound = (res) => {
      console.log('发现设备', res);
      const device = res.devices[0];
      
      // 过滤 CyberWand 设备
      if (device.name && (device.name.includes('CyberWand') || device.name.includes('Insta360'))) {
        const devices = this.data.devices;
        // 避免重复
        const exists = devices.some(d => d.deviceId === device.deviceId);
        if (!exists) {
          devices.push(device);
          this.setData({ devices });
        }
      }
    };
    
    tt.onBluetoothDeviceFound(onDeviceFound);
    
    // 5 秒后停止扫描
    setTimeout(() => {
      tt.stopBluetoothDevicesDiscovery({
        success: () => {
          tt.offBluetoothDeviceFound(onDeviceFound);
          tt.hideLoading();
          
          if (this.data.devices.length === 0) {
            tt.showToast({
              title: '未找到设备',
              icon: 'none'
            });
          } else {
            tt.showToast({
              title: `找到${this.data.devices.length}个设备`,
              icon: 'success'
            });
          }
        }
      });
    }, 5000);
  },
  
  // 选择设备
  selectDevice(e) {
    const device = e.currentTarget.dataset.device;
    this.setData({ selectedDevice: device.deviceId });
    console.log('选择设备:', device);
  },
  
  // 连接设备
  connectDevice() {
    if (!this.data.selectedDevice) {
      tt.showToast({
        title: '请先选择设备',
        icon: 'none'
      });
      return;
    }
    
    tt.showLoading({ title: '连接中...' });
    
    const deviceId = this.data.selectedDevice;
    
    tt.createBLEConnection({
      deviceId: deviceId,
      success: (res) => {
        console.log('连接成功', res);
        this.setData({
          connected: true,
          deviceId: deviceId
        });
        
        tt.hideLoading();
        tt.showToast({
          title: '连接成功',
          icon: 'success'
        });
        
        // 获取服务特征
        this.getBLEServices(deviceId);
        
        // 开始接收传感器数据
        this.startSensorUpdate();
      },
      fail: (err) => {
        console.error('连接失败', err);
        tt.hideLoading();
        tt.showToast({
          title: '连接失败',
          icon: 'none'
        });
      }
    });
  },
  
  // 获取 BLE 服务和特征
  getBLEServices(deviceId) {
    tt.getBLEDeviceServices({
      deviceId: deviceId,
      success: (res) => {
        console.log('服务列表', res);
        
        // 找到目标服务
        const targetService = res.services.find(s => 
          s.uuid.includes('fff0') || s.uuid.includes('FFF0')
        );
        
        if (targetService) {
          console.log('找到目标服务:', targetService.uuid);
          this.getBLECharacteristics(deviceId, targetService.uuid);
        }
      },
      fail: (err) => {
        console.error('获取服务失败', err);
      }
    });
  },
  
  // 获取特征
  getBLECharacteristics(deviceId, serviceId) {
    tt.getBLEDeviceCharacteristics({
      deviceId: deviceId,
      serviceId: serviceId,
      success: (res) => {
        console.log('特征列表', res);
        
        // 找到写入和通知特征
        const writeChar = res.characteristics.find(c => 
          c.properties.write && !c.properties.notify
        );
        const notifyChar = res.characteristics.find(c => 
          c.properties.notify
        );
        
        if (writeChar && notifyChar) {
          console.log('写入特征:', writeChar.uuid);
          console.log('通知特征:', notifyChar.uuid);
          
          this.writeCharUuid = writeChar.uuid;
          this.notifyCharUuid = notifyChar.uuid;
          
          // 启动通知
          this.notifyBLE(deviceId, serviceId, notifyChar.uuid);
        }
      },
      fail: (err) => {
        console.error('获取特征失败', err);
      }
    });
  },
  
  // 启动通知
  notifyBLE(deviceId, serviceId, characteristicId) {
    tt.notifyBLECharacteristicValueChange({
      deviceId: deviceId,
      serviceId: serviceId,
      characteristicId: characteristicId,
      state: true,
      success: (res) => {
        console.log('通知启动成功', res);
        
        // 监听特征值变化
        const onCharacteristicChange = (res) => {
          const value = res.value;
          console.log('收到数据:', value);
          
          // 解析传感器数据
          this.parseSensorData(value);
        };
        
        tt.onBLECharacteristicValueChange(onCharacteristicChange);
      },
      fail: (err) => {
        console.error('启动通知失败', err);
      }
    });
  },
  
  // 解析传感器数据
  parseSensorData(value) {
    // 假设数据格式：[命令字][数据...]
    // 例如：[0x21][gyro_x_h][gyro_x_l][gyro_y_h][gyro_y_l]...
    
    if (value.length >= 13) {
      const gyro_x = (value[1] << 8 | value[2]) / 100;
      const gyro_y = (value[3] << 8 | value[4]) / 100;
      const gyro_z = (value[5] << 8 | value[6]) / 100;
      const acc_x = (value[7] << 8 | value[8]) / 100;
      const acc_y = (value[9] << 8 | value[10]) / 100;
      const acc_z = (value[11] << 8 | value[12]) / 100;
      
      this.setData({
        sensorData: {
          gyro_x, gyro_y, gyro_z,
          acc_x, acc_y, acc_z
        }
      });
    }
  },
  
  // 断开连接
  disconnect() {
    if (!this.data.deviceId) return;
    
    tt.closeBLEConnection({
      deviceId: this.data.deviceId,
      success: (res) => {
        console.log('断开成功', res);
        this.setData({
          connected: false,
          deviceId: '',
          deviceName: '',
          batteryLevel: 0
        });
        
        if (this.data.sensorInterval) {
          clearInterval(this.data.sensorInterval);
          this.setData({ sensorInterval: null, sensorUpdating: false });
        }
        
        tt.showToast({
          title: '已断开',
          icon: 'success'
        });
      },
      fail: (err) => {
        console.error('断开失败', err);
      }
    });
  },
  
  // 断开 BLE（清理）
  disconnectBLE() {
    if (this.data.deviceId) {
      tt.closeBLEConnection({
        deviceId: this.data.deviceId
      });
    }
    tt.closeBluetoothAdapter();
  },
  
  // 更新动作映射
  updateMapping(e) {
    const index = e.currentTarget.dataset.index;
    const value = e.detail.value;
    const mappings = this.data.mappings;
    
    if (index >= 0 && index < mappings.length) {
      mappings[index].command = value;
      this.setData({ mappings });
    }
  },
  
  // 保存映射到设备
  saveMappings() {
    if (!this.data.connected) {
      tt.showToast({
        title: '请先连接设备',
        icon: 'none'
      });
      return;
    }
    
    // 发送配置命令：0x10 [动作 ID][指令]
    const commands = [];
    
    this.data.mappings.forEach((mapping, index) => {
      const cmd = parseInt(mapping.command, 16);
      if (!isNaN(cmd)) {
        commands.push([0x10, index, cmd]);
      }
    });
    
    // 批量发送
    let sent = 0;
    const sendNext = () => {
      if (sent >= commands.length) {
        tt.showToast({
          title: '映射已保存',
          icon: 'success'
        });
        return;
      }
      
      this.writeBLE(commands[sent], () => {
        sent++;
        sendNext();
      });
    };
    
    sendNext();
  },
  
  // 更新姿态参数
  updatePoseParam(e) {
    const key = e.currentTarget.dataset.key;
    const value = parseInt(e.detail.value);
    
    this.setData({
      [`poseParams.${key}`]: value
    });
  },
  
  // 保存姿态参数到设备
  savePoseParams() {
    if (!this.data.connected) {
      tt.showToast({
        title: '请先连接设备',
        icon: 'none'
      });
      return;
    }
    
    // 发送配置命令：0x11 [陀螺阈值][加速度阈值][融合权重][防抖时间][采样率]
    const cmd = [
      0x11,
      this.data.poseParams.gyro_threshold & 0xFF,
      this.data.poseParams.accel_threshold & 0xFF,
      this.data.poseParams.fusion_weight & 0xFF,
      this.data.poseParams.debounce_ms & 0xFF,
      this.data.poseParams.sample_rate & 0xFF
    ];
    
    this.writeBLE(cmd, () => {
      tt.showToast({
        title: '参数已保存',
        icon: 'success'
      });
    });
  },
  
  // 写入 BLE 数据
  writeBLE(data, callback) {
    if (!this.data.deviceId || !this.writeCharUuid) {
      callback && callback();
      return;
    }
    
    // 获取服务 UUID
    tt.getBLEDeviceServices({
      deviceId: this.data.deviceId,
      success: (res) => {
        const service = res.services.find(s => 
          s.uuid.includes('fff0') || s.uuid.includes('FFF0')
        );
        
        if (service) {
          tt.writeBLECharacteristicValue({
            deviceId: this.data.deviceId,
            serviceId: service.uuid,
            characteristicId: this.writeCharUuid,
            value: new Uint8Array(data).buffer,
            success: () => {
              callback && callback();
            },
            fail: (err) => {
              console.error('写入失败', err);
              callback && callback();
            }
          });
        } else {
          callback && callback();
        }
      },
      fail: () => {
        callback && callback();
      }
    });
  },
  
  // 切换传感器数据更新
  toggleSensorUpdate() {
    if (this.data.sensorUpdating) {
      // 暂停
      if (this.data.sensorInterval) {
        clearInterval(this.data.sensorInterval);
        this.setData({ sensorInterval: null, sensorUpdating: false });
      }
    } else {
      // 开始
      this.startSensorUpdate();
    }
  },
  
  // 开始传感器数据更新
  startSensorUpdate() {
    if (this.data.sensorInterval) return;
    
    // 定时读取传感器数据（每 500ms）
    const interval = setInterval(() => {
      if (!this.data.connected) {
        clearInterval(interval);
        this.setData({ sensorInterval: null, sensorUpdating: false });
        return;
      }
      
      // 发送读取命令：0x21
      this.writeBLE([0x21], () => {
        // 数据会通过通知回调返回
      });
    }, 500);
    
    this.setData({ 
      sensorInterval: interval,
      sensorUpdating: true
    });
  }
});
