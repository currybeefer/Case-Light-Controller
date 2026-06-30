# CaseLight / 风扇灯控制

A desktop tool to control motherboard ARGB lighting via **OpenRGB**.

Supports major motherboard brands: ASUS (AURA), MSI (Mystic Light), Gigabyte (RGB Fusion), ASRock (Polychrome), Razer (Chroma), Corsair (iCUE), and more.

---

## Prerequisites / 使用前提

- **Windows OS**
- **Python 3.8+** (Download from [python.org](https://python.org), check "Add Python to PATH" during installation)

## Quick Start / 快速开始

```bash
# Install Python dependencies / 安装依赖
pip install -r requirements.txt

# Launch / 启动
双击 start.bat    (Chinese Windows)
```

The program will auto-detect missing dependencies and download OpenRGB if needed.

---

## Features / 功能

- Toggle light ON / OFF  — 一键开关灯
- Pick ARGB color (auto-saved)  — 自由选择颜色（自动保存）
- Auto-connect to OpenRGB SDK  — 自动连接

## How it works / 工作原理

1. Check `openrgb` Python package → auto `pip install` if missing
2. Check OpenRGB.exe → auto download from GitHub to `_openrgb/` if missing
3. Launch OpenRGB (`--server` mode), control lighting via SDK

## FAQ / 常见问题

**"Connection failed" on startup**
- Check if another OpenRGB instance is running
- Verify your motherboard RGB chip is [supported by OpenRGB](https://openrgb.org/compatible.html)

**OpenRGB download fails**
- Ensure `github.com` is accessible from your network
- Manually download the portable ZIP from [OpenRGB Releases](https://github.com/OpenRGB/OpenRGB/releases) and extract to `_openrgb/`
