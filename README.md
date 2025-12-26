<p align="center">
  <img src="logo.svg" alt="FuseeFlow Logo" width="600">
</p>

**FuseeFlow** is a modern graphical user interface for injecting payloads into a Nintendo Switch in RCM (Recovery Mode). It provides a streamlined experience for launching payloads like Hekate, Fusee, and others using a pure Python backend based on [fusee-nano](https://github.com/DavidBuchanan314/fusee-nano).

> [!IMPORTANT]
> This project was developed with the assistance of AI (Google Gemini).

![Screenshot](screenshot.png)

## Features

- 🚀 **One-Click Injection:** fast and reliable payload injection.
- 🎨 **Modern GUI:** Built with PyQt6 for a clean look.
- 📂 **Payload Management:** Easily load, manage, and favorite your payloads.
- 💻 **Cross-Platform:** Runs natively on Linux and Windows.
- 🔌 **Automatic Detection:** Identifies when a Switch is connected in RCM mode.

## Prerequisites

- **Nintendo Switch** in RCM mode (using a jig or other method).
- **USB-C cable** to connect the Switch to your PC.
- **Python 3.8+** installed.

---

## 🐧 Linux Installation

### 1. Clone the Repository
```bash
git clone https://github.com/LouBoi161/FuseeFlow.git
cd FuseeFlow
```

### 2. System Dependencies
You need `libusb`.

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-pip libusb
```

**Debian / Ubuntu / Mint:**
```bash
sudo apt update
sudo apt install python3 python3-pip libusb-1.0-0-dev
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip libusb1-devel
```

### 3. Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. USB Permissions (Critical)
To access the Switch without root, add a udev rule:

1.  Create `/etc/udev/rules.d/99-switch.rules`:
    ```bash
    sudo nano /etc/udev/rules.d/99-switch.rules
    ```
2.  Paste this line:
    ```
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0955", ATTRS{idProduct}=="7321", MODE="0666"
    ```
3.  Reload rules:
    ```bash
    sudo udevadm control --reload-rules && sudo udevadm trigger
    ```

### 5. Running
```bash
python main.py
```

---

## 🪟 Windows Installation

### 1. Install Python
Download and install Python 3.8+ from [python.org](https://www.python.org/). **Make sure to check "Add Python to PATH" during installation.**

### 2. Clone or Download
Download the repository as a ZIP or clone it:
```cmd
git clone https://github.com/LouBoi161/FuseeFlow.git
cd FuseeFlow
```

### 3. Install Dependencies
Open a command prompt (cmd) in the folder and run:
```cmd
pip install -r requirements.txt
```

### 4. Install USB Drivers (Important!)
To communicate with the Switch in RCM mode, you need to install the `libusbK` driver using **Zadig**:

1.  Download [Zadig](https://zadig.akeo.ie/).
2.  Connect your Switch in RCM mode.
3.  Open Zadig and select **Options > List All Devices**.
4.  Select **APX** from the dropdown list.
5.  Choose **libusbK (v3.1.0.0)** (or similar) as the target driver.
6.  Click **Replace Driver** (or Install Driver).

### 5. Running
Double-click `run_windows.bat` (if available) or run:
```cmd
python main.py
```

---

## ⚙️ Configuration

- **Payloads:** Place your `.bin` payloads in the `payloads/` folder to have them auto-detected.

## License

MIT License. See [LICENSE](LICENSE) file for details.