"""Setup script for WiFi AC Guardian."""
from setuptools import setup, find_packages

setup(
    name="wifi-ac-guardian",
    version="1.0.0",
    description="Continuously ensures Wi-Fi is negotiated using Wi-Fi 5 (802.11ac) or higher.",
    author="Antigravity Engineering",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "pystray>=0.19.5",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "wifi-ac-guardian=wifi_ac_guardian.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking :: Monitoring",
    ],
)
