#!/bin/bash
# =============================================================================
# setup.sh — EDEMI Smart Glasses
# Run this ONCE on Pi after cloning project
# Installs all dependencies and configures hardware interfaces
# Usage: chmod +x setup.sh && sudo ./setup.sh
# =============================================================================

set -e  # Stop on any error

echo "=================================================="
echo "  EDEMI Smart Glasses — Pi Setup Script"
echo "=================================================="
echo ""

# --- Check running as root ---
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root: sudo ./setup.sh"
  exit 1
fi

# --- Check Pi Zero 2W ---
echo "[1/8] Checking hardware..."
PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | head -1)
echo "      Device: $PI_MODEL"

# --- Update system ---
echo "[2/8] Updating system packages..."
apt-get update -q
apt-get upgrade -y -q
echo "      Done."

# --- Install system dependencies ---
echo "[3/8] Installing system dependencies..."
apt-get install -y -q \
  python3-pip \
  python3-dev \
  python3-pil \
  python3-numpy \
  python3-pygame \
  python3-smbus \
  i2c-tools \
  libasound2-dev \
  portaudio19-dev \
  libportaudio2 \
  hostapd \
  dnsmasq \
  git \
  fonts-dejavu-core
echo "      Done."

# --- Install Python packages ---
echo "[4/8] Installing Python packages..."
pip3 install --break-system-packages \
  vosk \
  sounddevice \
  numpy \
  pillow \
  flask \
  smbus2 \
  RPi.GPIO \
  ST7735 \
  pyalsaaudio
echo "      Done."

# --- Enable hardware interfaces ---
echo "[5/8] Enabling I2S, SPI, I2C..."

CONFIG="/boot/config.txt"

# Enable SPI
if ! grep -q "dtparam=spi=on" $CONFIG; then
  echo "dtparam=spi=on" >> $CONFIG
fi

# Enable I2C
if ! grep -q "dtparam=i2c_arm=on" $CONFIG; then
  echo "dtparam=i2c_arm=on" >> $CONFIG
fi

# Enable I2S for INMP441 microphone
if ! grep -q "dtoverlay=i2s-mems-mic" $CONFIG; then
  echo "dtoverlay=i2s-mems-mic" >> $CONFIG
fi

# HDMI force on for AR display
if ! grep -q "hdmi_force_hotplug=1" $CONFIG; then
  echo "hdmi_force_hotplug=1"   >> $CONFIG
  echo "hdmi_group=2"           >> $CONFIG
  echo "hdmi_mode=87"           >> $CONFIG
  echo "hdmi_cvt=640 480 60"    >> $CONFIG
fi

# GPU memory — minimum for framebuffer
if ! grep -q "gpu_mem=" $CONFIG; then
  echo "gpu_mem=64" >> $CONFIG
fi

echo "      Done."

# --- Configure ALSA for I2S microphone ---
echo "[6/8] Configuring ALSA for INMP441..."
cat > /etc/asound.conf << 'ALSA'
pcm.!default {
  type asym
  capture.pcm "mic"
}
pcm.mic {
  type plug
  slave {
    pcm "hw:1,0"
    rate 16000
    channels 1
    format S16_LE
  }
}
ALSA
echo "      Done."

# --- Configure WiFi Hotspot ---
echo "[7/8] Configuring EDEMI WiFi hotspot..."

# Stop services during config
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# hostapd config
cat > /etc/hostapd/hostapd.conf << 'HOSTAPD'
interface=wlan0
driver=nl80211
ssid=EDEMI_Glasses
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=edemi2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
HOSTAPD

# Point hostapd to config
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

# dnsmasq config
cat > /etc/dnsmasq.conf << 'DNSMASQ'
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
DNSMASQ

# Static IP for hotspot
cat >> /etc/dhcpcd.conf << 'DHCPCD'
interface wlan0
  static ip_address=192.168.4.1/24
  nohook wpa_supplicant
DHCPCD

# Enable services
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

echo "      Hotspot: EDEMI_Glasses"
echo "      Password: edemi2024"
echo "      IP: 192.168.4.1:5000"
echo "      Done."

# --- Install systemd autoboot service ---
echo "[8/8] Installing autoboot service..."

cat > /etc/systemd/system/edemi.service << 'SERVICE'
[Unit]
Description=EDEMI Smart Glasses System
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/edemi
ExecStart=/usr/bin/python3 /home/pi/edemi/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=SDL_VIDEODRIVER=fbcon
Environment=SDL_FBDEV=/dev/fb0
Environment=SDL_NOMOUSE=1

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable edemi.service

echo "      Autoboot enabled."
echo ""
echo "=================================================="
echo "  Setup complete!"
echo ""
echo "  IMPORTANT — Next steps:"
echo "  1. Move project to: /home/pi/edemi/"
echo "  2. Copy Vosk model to: /home/pi/edemi/"
echo "  3. Edit config.py: set RUNNING_ON_PI = True"
echo "  4. Reboot: sudo reboot"
echo ""
echo "  After reboot:"
echo "  - EDEMI starts automatically"
echo "  - WiFi: EDEMI_Glasses / Password: edemi2024"
echo "  - Settings: http://192.168.4.1:5000"
echo "=================================================="
