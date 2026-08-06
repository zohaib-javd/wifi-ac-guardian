const { app, BrowserWindow, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let tray = null;
let pythonProcess = null;
let staticServer = null;
let statusPollInterval = null;
let isQuitting = false;
let currentStatusIcon = null;

const STATIC_PORT = 39147;
const PYTHON_IPC_PORT = 39146;

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

// Built-in static server for Next.js app
function startStaticServer() {
  const outDir = path.join(__dirname, 'out');
  staticServer = http.createServer((req, res) => {
    let reqPath = req.url.split('?')[0];
    let filePath = path.join(outDir, reqPath);

    if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
      filePath = path.join(filePath, 'index.html');
    }

    fs.readFile(filePath, (err, data) => {
      if (err) {
        fs.readFile(path.join(outDir, 'index.html'), (err2, fallbackData) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not Found');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(fallbackData);
          }
        });
      } else {
        const ext = path.extname(filePath).toLowerCase();
        const contentType = mimeTypes[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
      }
    });
  });

  staticServer.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.log(`[Electron] Port ${STATIC_PORT} bound by primary instance.`);
    } else {
      console.error('[Electron] Static server error:', err);
    }
  });

  staticServer.listen(STATIC_PORT, '127.0.0.1', () => {
    console.log(`[Electron] Static UI server listening on http://127.0.0.1:${STATIC_PORT}`);
  });
}

// Spawn Python Guardian Backend with --no-tray (single system tray icon)
function startPythonBackend() {
  try {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    pythonProcess = spawn(pythonExe, ['-m', 'wifi_ac_guardian_win', '--daemon', '--no-tray'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'ignore',
      detached: false,
    });
    console.log('[Electron] Python Guardian Engine spawned in daemon mode without tray.');
  } catch (err) {
    console.error('[Electron] Failed to spawn Python backend:', err);
  }
}

// Set Windows App User Model ID for Taskbar Branding
app.setAppUserModelId('com.wifiacguardian.app');

function createWindow() {
  const windowIconPath = path.join(__dirname, 'public', 'icon.ico');

  mainWindow = new BrowserWindow({
    width: 980,
    height: 760,
    minWidth: 900,
    minHeight: 680,
    backgroundColor: '#0D0F10',
    title: 'WiFi AC Guardian',
    icon: windowIconPath,
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.loadURL(`http://127.0.0.1:${STATIC_PORT}`);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      return false;
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Dynamic Single System Tray Icon (Green = Good, Red/Cross = Failed, Amber = Retrying)
function createSystemTray() {
  const defaultIconPath = path.join(__dirname, 'public', 'status', 'good.png');
  const icon = nativeImage.createFromPath(defaultIconPath).resize({ width: 16, height: 16 });
  
  tray = new Tray(icon);
  tray.setToolTip('WiFi AC Guardian — Protected');
  currentStatusIcon = 'good';

  const contextMenu = Menu.buildFromTemplate([
    { label: 'WiFi AC Guardian', enabled: false },
    { type: 'separator' },
    {
      label: 'Open Dashboard',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        } else {
          createWindow();
        }
      },
    },
    {
      label: 'Force Reconnect',
      click: async () => {
        try {
          const fetch = (await import('node-fetch')).default || globalThis.fetch;
          await fetch(`http://127.0.0.1:${PYTHON_IPC_PORT}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'reconnect_now' }),
          });
        } catch (e) {
          console.log('[Tray] Reconnect error:', e);
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Exit',
      click: () => {
        isQuitting = true;
        if (pythonProcess) {
          try {
            pythonProcess.kill();
          } catch (e) {}
        }
        if (staticServer) {
          try {
            staticServer.close();
          } catch (e) {}
        }
        if (statusPollInterval) clearInterval(statusPollInterval);
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  // Poll Python IPC to dynamically update System Tray Icon color
  statusPollInterval = setInterval(async () => {
    try {
      const fetch = (await import('node-fetch')).default || globalThis.fetch;
      const res = await fetch(`http://127.0.0.1:${PYTHON_IPC_PORT}`);
      if (res.ok) {
        const data = await res.json();
        const status = (data.status || 'good').toLowerCase();
        
        let iconName = 'good.png';
        let tooltipText = `WiFi AC Guardian — Protected (${data.linkSpeed || 866} Mbps)`;

        if (status.includes('fail') || status.includes('disconnect')) {
          iconName = 'failed.png';
          tooltipText = 'WiFi AC Guardian — Reconnection Failed';
        } else if (status.includes('retry') || status.includes('reconnect')) {
          iconName = 'retrying.png';
          tooltipText = 'WiFi AC Guardian — Retrying Connection...';
        } else if (status.includes('standby') || status.includes('idle')) {
          iconName = 'standby.png';
          tooltipText = 'WiFi AC Guardian — Standby';
        }

        if (currentStatusIcon !== iconName) {
          currentStatusIcon = iconName;
          const statusIconPath = path.join(__dirname, 'public', 'status', iconName);
          const newIcon = nativeImage.createFromPath(statusIconPath).resize({ width: 16, height: 16 });
          tray.setImage(newIcon);
        }
        tray.setToolTip(tooltipText);
      }
    } catch (e) {
      // IPC polling fallback
    }
  }, 3000);
}

app.whenReady().then(() => {
  startStaticServer();
  startPythonBackend();
  createWindow();
  createSystemTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' && isQuitting) {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (e) {}
  }
  if (staticServer) {
    try {
      staticServer.close();
    } catch (e) {}
  }
  if (statusPollInterval) clearInterval(statusPollInterval);
});
