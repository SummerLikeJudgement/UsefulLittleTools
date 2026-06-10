@echo off
echo 正在关闭所有 WSL 实例...
wsl --shutdown

if errorlevel 1 (
    echo 错误：wsl --shutdown 执行失败，请检查 WSL 状态。
    pause
    exit /b 1
)

echo WSL 已关闭，准备压缩虚拟磁盘...

set VDISK_PATH="D:\Coding\Docker\storage\DockerDesktopWSL\disk\docker_data.vhdx"

echo 目标文件：%VDISK_PATH%
echo 正在启动 diskpart 并执行压缩...

(
echo select vdisk file=%VDISK_PATH%
echo compact vdisk
echo exit
) | diskpart

echo 压缩操作已完成。
pause