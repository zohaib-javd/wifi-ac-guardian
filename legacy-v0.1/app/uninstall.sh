#!/usr/bin/env bash
set -e

# ==============================================================================
# WiFi AC Guardian Uninstallation Script
# ==============================================================================

echo "======================================================"
echo "         Uninstalling WiFi AC Guardian                "
echo "======================================================"

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"

# 1. Stop and disable systemd service
echo "[1/3] Stopping and disabling systemd service..."
if systemctl --user is-active --quiet wifi-ac-guardian.service 2>/dev/null; then
    systemctl --user stop wifi-ac-guardian.service || true
fi

if systemctl --user is-enabled --quiet wifi-ac-guardian.service 2>/dev/null; then
    systemctl --user disable wifi-ac-guardian.service || true
fi

# Remove unit file and autostart desktop entry
rm -f "$SYSTEMD_USER_DIR/wifi-ac-guardian.service"
rm -f "$AUTOSTART_DIR/wifi_ac_guardian.desktop"

systemctl --user daemon-reload || true

# 2. Uninstall Python package
echo "[2/3] Uninstalling Python package..."
python3 -m pip uninstall -y wifi-ac-guardian --break-system-packages 2>/dev/null || python3 -m pip uninstall -y wifi-ac-guardian 2>/dev/null || true

# 3. Clean up icon cache
echo "[3/3] Cleaning up icon cache..."
rm -rf "$HOME/.local/share/wifi_ac_guardian"

echo "======================================================"
echo "      WiFi AC Guardian Successfully Uninstalled.     "
echo "======================================================"
