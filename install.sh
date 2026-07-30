#!/usr/bin/env bash
set -e

# ==============================================================================
# WiFi AC Guardian Installation Script
# Platform: Ubuntu 22.04+ / Debian-based Linux
# ==============================================================================

echo "======================================================"
echo "          Installing WiFi AC Guardian                 "
echo "======================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="$HOME"
SYSTEMD_USER_DIR="$USER_HOME/.config/systemd/user"
AUTOSTART_DIR="$USER_HOME/.config/autostart"
BIN_DIR="$USER_HOME/.local/bin"

# 1. Verify Platform & Prerequisites
echo "[1/5] Checking environment requirements..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed." >&2
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python version: $PY_VERSION"

# 2. Install System Dependencies via apt if available
echo "[2/5] Installing system dependencies (iw, network-manager, libnotify-bin, python3-pip)..."
if command -v apt-get >/dev/null 2>&1; then
    echo "Running apt-get update & install (sudo may prompt for password if required)..."
    sudo apt-get update -qq || true
    sudo apt-get install -y -qq \
        iw \
        network-manager \
        libnotify-bin \
        python3-pip \
        python3-pil \
        python3-setuptools \
        python3-wheel \
        gir1.2-ayatanaappindicator3-0.1 || true
fi

# 3. Install Python Package
echo "[3/5] Installing WiFi AC Guardian Python package..."
cd "$SCRIPT_DIR"
python3 -m pip install --upgrade --break-system-packages . || python3 -m pip install --upgrade .

mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:$PATH"

if ! command -v wifi-ac-guardian >/dev/null 2>&1; then
    echo "WARNING: wifi-ac-guardian binary not found in PATH ($BIN_DIR). Ensure ~/.local/bin is in your PATH."
fi

# 4. Install Systemd User Service
echo "[4/5] Configuring systemd user service..."
mkdir -p "$SYSTEMD_USER_DIR"

# Expand executable path dynamically in service unit
EXECUTABLE_PATH="$(which wifi-ac-guardian || echo "$BIN_DIR/wifi-ac-guardian")"

cat <<EOF > "$SYSTEMD_USER_DIR/wifi-ac-guardian.service"
[Unit]
Description=WiFi AC Guardian Continuous PHY Mode Monitor
Documentation=https://github.com/example/wifi-ac-guardian
After=network.target NetworkManager.service
Wants=network.target

[Service]
Type=simple
ExecStart=$EXECUTABLE_PATH --daemon
Restart=always
RestartSec=5s
Environment="PATH=$USER_HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DISPLAY=:0"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable wifi-ac-guardian.service || true
systemctl --user restart wifi-ac-guardian.service || true

# 5. Configure Desktop Autostart Entry
echo "[5/5] Configuring desktop autostart..."
mkdir -p "$AUTOSTART_DIR"

cat <<EOF > "$AUTOSTART_DIR/wifi_ac_guardian.desktop"
[Desktop Entry]
Type=Application
Name=WiFi AC Guardian
Comment=Ensures continuous Wi-Fi 5 (802.11ac) or higher negotiation
Exec=$EXECUTABLE_PATH --daemon
Icon=network-wireless
Categories=Network;Monitor;
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

echo "======================================================"
echo "   WiFi AC Guardian Installation Complete!            "
echo "======================================================"
echo "Service Status:"
systemctl --user status wifi-ac-guardian.service --no-pager || true
echo ""
echo "Quick CLI test:"
echo "  wifi-ac-guardian --status"
echo ""
echo "Log file location:"
echo "  ~/wifi_ac_guardian.log"
echo "======================================================"
