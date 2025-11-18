# RPi Car Infotainment (Lite OS · Pi 4)

A lightweight, touch-friendly car infotainment system for Raspberry Pi.

This branch targets **Raspberry Pi 4** running **Raspberry Pi OS Lite (Bookworm)**, using:
 - **Direct framebuffer** rendering (no X/Wayland) via Qt `linuxfb` + `evdev`
 - Bluetooth auto-pairing (no code) with **A2DP** audio input from phone
 - **PulseAudio (user instance)** with audio out on the **3.5 mm jack**
 - **Fixed display mode 1024×600** on both HDMI ports

> If you’re on Raspberry Pi 5 or a Desktop (with X/Wayland), refer to the Pi 5 branch/instructions.
> This document is optimized for **Pi 4 + Lite**.

## Project Structure

```bash
rpi_car_infotainment/
├── assets/             # Icons and other static assets
├── backend/            # Backend functionality
├── deployment/         # Service files, installation scripts, and deployment configs
├── gui/                # GUI components and screens
├── music/              # Music library and related files
├─ scripts/
│  ├─ start_infotainment.sh          # Launches the app (Qt linuxfb + evdev, activates venv)
│  ├─ install_rpi_car_infotainment.sh   # Install all the necessary settings to work
│  └─ (other helpers)
├── tests/              # Test files
├── tools/              # RF communication and other tools
├── config.json         # Configuration file
├── main.py             # Main application entry point
└── requirements.txt    # Python dependencies
```

## Hardware & OS
 - **Raspberry Pi 4** (2GB/4GB/8GB)
 - **Raspberry Pi OS Lite (Bookworm)** 64-bit recommended
 - 7–10″ HDMI “car” display (physical **1024×600** panel, many controllers advertise 1080p)
 - USB/serial touchscreen controller (evdev)
 - Audio output via **3.5 mm jack**

# Installation

## 1. Install git
After installing the **Raspberry Pi OS Lite** on the raspberry **with pi as a user**, install git:
```bash
sudo apt update
sudo apt install -y git
```

## 2. Clone the repo
Clone the repo in your user folder (pi):
```bash
cd /home/pi
git clone https://github.com/giulio177/rpi_car_infotainment.git
cd rpi_car_infotainment
```

## 3. Clone the repo
Enable and start the install script:
```bash
chmod +x scripts/install_rpi_car_infotainment.sh
cd /home/pi/rpi_car_infotainment
sudo ./scripts/install_rpi_car_infotainment.sh
```

## 4. Reboot
Reboot the system and you're done:
```bash
sudo reboot
```

#


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
