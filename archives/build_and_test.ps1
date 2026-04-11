# CyberWand 编译和测试脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CyberWand 编译和测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 ESP-IDF 环境
$env_idf_path = $env:IDF_PATH
if (-not $env_idf_path) {
    Write-Host "[ERROR] ESP-IDF 环境未配置！" -ForegroundColor Red
    Write-Host "请先运行：" -ForegroundColor Yellow
    Write-Host "  .\esp-idf-v5.1\install.sh esp32c6" -ForegroundColor Cyan
    Write-Host "  .\esp-idf-v5.1\export.sh" -ForegroundColor Cyan
    exit 1
}

Write-Host "[OK] ESP-IDF 环境已配置：$env_idf_path" -ForegroundColor Green
Write-Host ""

# 编译 CyberWand
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  编译 CyberWand 固件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot\cyberwand_esp

Write-Host "设置目标芯片为 ESP32-C6..." -ForegroundColor Yellow
idf.py set-target esp32c6

Write-Host "开始编译..." -ForegroundColor Yellow
idf.py build

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 编译成功！" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 编译失败！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  运行 PC 模拟测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 编译 PC 模拟测试
Set-Location $PSScriptRoot\cyberwand_esp\tests

Write-Host "编译模拟测试..." -ForegroundColor Yellow
gcc -o test_pose_sim.exe test_pose_sim.c ..\main\mpu6050_sim.c ..\main\pose_model.c -lm

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 测试程序编译成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "运行测试..." -ForegroundColor Yellow
    Write-Host ""
    .\test_pose_sim.exe
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ 所有测试通过！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  ❌ 部分测试失败！" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
    }
} else {
    Write-Host "[ERROR] 测试程序编译失败！" -ForegroundColor Red
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Cyan
