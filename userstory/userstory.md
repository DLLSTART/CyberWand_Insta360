# 赛博魔杖项目需求文档

## 用户需求

### 需求1: 手势录制模式
As a user
I want to 进入手势录制模式
So that 我可以录制自定义手势以便后续识别
Given 魔杖已开机
When 我按下模式选择按钮进入录制模式时
Then 蓝色LED以1Hz频率闪烁
And LCD屏幕显示需要录制的手势类型

### 需求2: 手势类型选择
As a user
I want to 选择要录制的手势类型
So that 我可以为不同用途组织不同的手势
Given 我在录制模式中
When 我使用按键选择手势类型时
Then LCD屏幕更新显示所选的手势类型
And 系统等待录制确认

### 需求3: 手势录制启动
As a user
I want to 开始录制手势
So that 我可以捕获所选手势的运动数据
Given 我已选择了一个手势类型
When 我按下播放按键开始录制时
Then LCD屏幕显示录制指导图片
And 语音提示播报"录制开始"
And 系统开始实时记录所有四元组数据

### 需求4: 手势数据保存
As a user
I want to 保存录制的手势数据
So that 我可以使用它来训练手势识别模型
Given 录制正在进行中
When 录制完成时
Then 所有四元组数据保存到本地目录
And 语音提示播报"录制完成"
And 系统返回手势选择菜单

### 需求5: 手势检测模式
As a user
I want to 进入手势检测模式
So that 我可以使用魔杖识别并响应我的手势
Given 魔杖已开机
When 我按下模式选择按钮进入检测模式时
Then 绿色LED以1Hz频率闪烁
And 系统激活手势识别算法

### 需求6: 手势识别与蓝牙广播
As a user
I want to 根据识别的手势通过蓝牙广播特定数据
So that 我可以无线控制其他设备或发送消息
Given 我在检测模式中
When 我执行已注册的手势时
Then 系统使用深度学习模型识别该手势
And 广播与该手势关联的用户配置的蓝牙字符串
And LCD提供视觉反馈

### 需求7: 按键功能
As a user
I want to 魔杖上有物理按键
So that 我可以直观地与系统交互
Given 魔杖硬件存在
When 我按下按键时
Then 系统根据按键功能做出响应
Including 模式选择、手势选择和录制控制

### 需求8: 灯语反馈
As a user
I want to 通过LED指示器接收视觉反馈
So that 我可以了解当前系统状态
Given 魔杖正在运行
When 系统状态改变时
Then LED显示相应的颜色和闪烁模式
Including 检测模式显示绿色、录制模式显示蓝色以及其他状态指示

### 需求9: 语音提示
As a user
I want to 接收音频提示
So that 我可以在不看显示的情况下操作魔杖
Given 魔杖正在执行某个操作
When 发生重要事件时
Then 语音提示播报该事件
Including "录制开始"、"录制完成"以及其他状态消息

### 需求10: LCD显示
As a user
I want to 在LCD屏幕上查看信息
So that 我可以了解当前操作和选项
Given 魔杖有LCD显示屏
When 我浏览菜单或执行操作时
Then LCD显示屏显示相关信息
Including 手势类型、录制指导和系统状态

### 需求11: 语音检测
As a user
I want to 检测语音命令
So that 我可以使用语音输入控制魔杖
Given 魔杖具有语音检测能力
When 我说出命令时
Then 系统识别语音命令
And 执行相应操作

### 需求12: 深度学习模型部署
As a user
I want to 在魔杖上部署训练好的深度学习模型
So that 我可以实现准确的手势识别
Given 嵌入式系统有足够的资源
When 我执行手势时
Then 深度学习模型处理运动数据
And 高精度返回识别的手势

### 需求13: 蓝牙广播配置
As a user
I want to 为每个手势配置蓝牙广播字符串
So that 我可以为不同手势自定义发送的数据
Given 我在配置魔杖
When 我为手势分配蓝牙字符串时
Then 系统保存该关联
And 在识别该手势时广播该字符串

### 需求14: 四元组数据记录
As a user
I want to 在手势录制期间记录四元组数据
So that 我可以捕获准确的3D方向信息
Given 录制处于活动状态
When 魔杖移动时
Then 系统实时记录所有四元组数据
Including 时间戳和方向值

### 需求15: 本地文件存储
As a user
I want to 将录制的手势数据保存到本地存储
So that 我可以管理和传输手势数据
Given 录制已完成
When 数据准备好保存时
Then 系统将文件保存到本地目录
With 适当的命名约定和文件格式

### 需求16: 产测模式
As a user
I want to 进入产测模式
So that 我可以连接PC端上位机进行数据采集和测试
Given 魔杖已开机
When 我按下特定按键组合进入产测模式时
Then 紫色LED以2Hz频率闪烁
And LCD屏幕显示产测模式界面
And 系统启动WiFi热点或扫描可用WiFi网络

### 需求17: WiFi连接
As a user
I want to 连接PC端上位机的WiFi
So that 我可以建立数据传输通道
Given 我在产测模式中
When 我选择并连接到PC端上位机的WiFi热点时
Then 系统建立WiFi连接
And LCD屏幕显示连接状态
And LED颜色变为白色常亮表示连接成功

### 需求18: 陀螺仪数据实时上传
As a user
I want to 将收集到的陀螺仪数据通过WiFi上传到上位机
So that 我可以在PC端实时查看和保存数据
Given WiFi连接已建立
When 陀螺仪采集到新的数据时
Then 系统将四元组数据通过WiFi实时上传到上位机
And 上位机接收并保存数据到本地文件
And LCD屏幕显示数据传输状态

### 需求19: 产测数据格式
As a user
I want to 上传的陀螺仪数据包含完整信息
So that 我可以在上位机进行数据分析和模型训练
Given 数据正在上传
When 每条数据包发送时
Then 数据包包含时间戳、加速度计数据、陀螺仪数据、四元组数据
And 数据格式为JSON或二进制格式便于解析
And 数据包包含校验和确保数据完整性

### 需求20: 产测模式退出
As a user
I want to 退出产测模式
So that 我可以返回正常使用模式
Given 我在产测模式中
When 我按下退出按键或断开WiFi连接时
Then 系统停止数据上传
And 断开WiFi连接
And 返回主菜单或待机模式
And LED恢复待机状态显示
