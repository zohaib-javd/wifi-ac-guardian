from setuptools import setup, find_packages

setup(
    name="wifi-ac-guardian-win",
    version="1.0.0",
    description="WiFi AC Guardian for Windows 11 - Enforces Wi-Fi 5+ connection quality.",
    author="Antigravity",
    packages=find_packages(),
    package_data={"wifi_ac_guardian_win": ["assets/*.ico", "assets/*.png", "assets/fluent/*.png", "assets/router_status/*.png", "assets/tray_menu/*.bmp"]},
    install_requires=[
        "pystray>=0.19.0",
        "Pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "wifi-ac-guardian-win = wifi_ac_guardian_win.cli:main",
        ],
        "gui_scripts": [
            "wifi-ac-guardian-win-gui = wifi_ac_guardian_win.cli:main",
        ],
    },
    python_requires=">=3.8",
)
