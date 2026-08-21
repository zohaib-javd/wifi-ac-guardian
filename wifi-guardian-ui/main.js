const { app, BrowserWindow, Tray, Menu, nativeImage, shell, ipcMain } = require('electron');
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
let trayProtectionRunning = false;

const STATIC_PORT = 39147;
const PYTHON_IPC_PORT = 39146;
const STATUS_ASSET_DIR = path.join(__dirname, 'public', 'status');

ipcMain.handle('open-log-file', async () => {
  const configPath = path.join(process.env.APPDATA || app.getPath('home'), 'wifi-ac-guardian', 'config.json');
  let logPath = path.join(app.getPath('home'), 'wifi_ac_guardian_win.log');
  try {
    if (fs.existsSync(configPath)) {
      const savedConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      if (typeof savedConfig.log_file_path === 'string' && savedConfig.log_file_path.trim()) {
        logPath = savedConfig.log_file_path;
      }
    }
  } catch (error) {
    console.log('[Electron] Could not read the Guardian log-file setting:', error.message);
  }
  const error = await shell.openPath(logPath);
  return { ok: !error, error: error || null, path: logPath };
});

ipcMain.handle('open-external', async (_event, rawUrl) => {
  try {
    const url = new URL(String(rawUrl));
    const safeWebsite = url.protocol === 'https:' && url.hostname === 'zeejaylab.store';
    const safeEmail = url.protocol === 'mailto:' && url.pathname === 'zeejay.lab@gmail.com';
    if (!safeWebsite && !safeEmail) {
      throw new Error('This external link is not allowed.');
    }
    await shell.openExternal(url.href);
    return { ok: true };
  } catch (error) {
    console.error('[Electron] Could not open external link:', error);
    return { ok: false, error: error instanceof Error ? error.message : 'Unable to open the link in your default browser.' };
  }
});

ipcMain.handle('set-login-startup', async (_event, options = {}) => {
  try {
    const autoStart = options.autoStart === true;
    const startMinimized = options.startMinimized === true;
    const loginOptions = {
      openAtLogin: autoStart,
      openAsHidden: startMinimized,
      path: process.execPath,
      args: app.isPackaged ? [] : [app.getAppPath()],
    };
    app.setLoginItemSettings(loginOptions);
    const legacyShortcut = path.join(
      process.env.APPDATA || '',
      'Microsoft',
      'Windows',
      'Start Menu',
      'Programs',
      'Startup',
      'WiFi AC Guardian.lnk',
    );
    if (legacyShortcut && fs.existsSync(legacyShortcut)) {
      fs.unlinkSync(legacyShortcut);
    }
    return { ok: true };
  } catch (error) {
    console.error('[Electron] Could not update login startup settings:', error);
    return { ok: false, error: error instanceof Error ? error.message : 'Unable to update Windows startup settings.' };
  }
});

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => showDashboard());
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

function startStaticServer() {
  const outDir = path.join(__dirname, 'out');
  staticServer = http.createServer((req, res) => {
    const reqPath = req.url.split('?')[0];
    let filePath = path.join(outDir, reqPath);

    if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
      filePath = path.join(filePath, 'index.html');
    }

    fs.readFile(filePath, (err, data) => {
      if (err) {
        fs.readFile(path.join(outDir, 'index.html'), (fallbackError, fallbackData) => {
          if (fallbackError) {
            res.writeHead(404);
            res.end('Not Found');
            return;
          }
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(fallbackData);
        });
        return;
      }

      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });

  staticServer.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.log(`[Electron] Port ${STATIC_PORT} bound by primary instance.`);
      return;
    }
    console.error('[Electron] Static server error:', err);
  });

  staticServer.listen(STATIC_PORT, '127.0.0.1', () => {
    console.log(`[Electron] Static UI server listening on http://127.0.0.1:${STATIC_PORT}`);
  });
}

function startPythonBackend() {
  try {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    pythonProcess = spawn(pythonExe, ['-m', 'wifi_ac_guardian_win', '--daemon', '--no-tray'], {
      cwd: app.isPackaged ? process.resourcesPath : path.join(__dirname, '..'),
      stdio: 'ignore',
      detached: false,
    });
    console.log(`[Electron] Python Guardian Engine spawned without a native tray. cwd=${app.isPackaged ? process.resourcesPath : path.join(__dirname, '..')}`);
  } catch (err) {
    console.error('[Electron] Failed to spawn Python backend:', err);
  }
}

app.setAppUserModelId('com.wifiacguardian.app');

function createWindow() {
  const windowIconPath = path.join(__dirname, 'public', 'icon.ico');
  mainWindow = new BrowserWindow({
    width: 430,
    height: 720,
    resizable: false,
    maximizable: false,
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
    const configPath = path.join(process.env.APPDATA || path.join(require('os').homedir(), '.config'), 'wifi-ac-guardian', 'config.json');
    let startMinimized = false;
    try {
      if (fs.existsSync(configPath)) {
        startMinimized = JSON.parse(fs.readFileSync(configPath, 'utf-8')).start_minimized === true;
      }
    } catch (error) {
      console.log('[Electron] Could not read config for start_minimized:', error.message);
    }
    if (!startMinimized) mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function showDashboard() {
  if (!mainWindow) {
    createWindow();
    return;
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
}

function statusPresentation(data) {
  const status = String(data?.status || '').trim().toUpperCase();
  const running = data?.protectionRunning === true;
  const speed = Number(data?.linkSpeed || 0);

  if (!running || status === 'IDLE' || status === 'STANDBY') {
    return { iconName: 'standby.png', tooltip: 'WiFi AC Guardian — Standby', running: false };
  }
  if (status === 'RECONNECTING' || status === 'RETRYING') {
    return { iconName: 'retrying.png', tooltip: 'WiFi AC Guardian — Retrying Connection', running: true };
  }
  if (status === 'DOWNGRADED' || status === 'FAILED' || status === 'DISCONNECTED' || data?.connected === false) {
    return { iconName: 'failed.png', tooltip: 'WiFi AC Guardian — Protection Needs Attention', running: true };
  }
  if (status === 'GOOD' && data?.connected === true) {
    return { iconName: 'good.png', tooltip: `WiFi AC Guardian — Protected${speed > 0 ? ` (${Math.round(speed)} Mbps)` : ''}`, running: true };
  }
  return { iconName: 'standby.png', tooltip: 'WiFi AC Guardian — Standby', running: false };
}

function rebuildTrayMenu() {
  if (!tray) return;
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open Dashboard', click: showDashboard },
    {
      label: trayProtectionRunning ? 'Stop Engine' : 'Start Engine',
      click: () => {
        void toggleEngineFromTray();
      },
    },
    { type: 'separator' },
    {
      label: 'Exit',
      click: quitApplication,
    },
  ]));
}

function updateTray(data) {
  if (!tray) return;
  const visual = statusPresentation(data);
  trayProtectionRunning = visual.running;
  if (currentStatusIcon !== visual.iconName) {
    currentStatusIcon = visual.iconName;
    const icon = nativeImage.createFromPath(path.join(STATUS_ASSET_DIR, visual.iconName)).resize({ width: 16, height: 16 });
    tray.setImage(icon);
  }
  tray.setToolTip(visual.tooltip);
  rebuildTrayMenu();
}

async function getGuardianStatus() {
  const response = await fetch(`http://127.0.0.1:${PYTHON_IPC_PORT}`);
  if (!response.ok) throw new Error(`Guardian backend returned HTTP ${response.status}`);
  return response.json();
}

async function refreshTrayStatus() {
  try {
    updateTray(await getGuardianStatus());
  } catch (error) {
    updateTray({ protectionRunning: false, status: 'IDLE' });
  }
}

async function toggleEngineFromTray() {
  try {
    const response = await fetch(`http://127.0.0.1:${PYTHON_IPC_PORT}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'toggle_protection' }),
    });
    if (!response.ok) throw new Error(`Guardian backend returned HTTP ${response.status}`);
    const result = await response.json();
    updateTray({ protectionRunning: result.protectionRunning, status: result.protectionRunning ? 'GOOD' : 'IDLE', connected: result.protectionRunning });
    await refreshTrayStatus();
  } catch (error) {
    console.error('[Tray] Unable to toggle protection:', error);
    await refreshTrayStatus();
  }
}

function createSystemTray() {
  const initialIcon = nativeImage.createFromPath(path.join(STATUS_ASSET_DIR, 'standby.png')).resize({ width: 16, height: 16 });
  tray = new Tray(initialIcon);
  currentStatusIcon = 'standby.png';
  tray.setToolTip('WiFi AC Guardian — Standby');
  rebuildTrayMenu();
  tray.on('double-click', showDashboard);
  void refreshTrayStatus();
  statusPollInterval = setInterval(() => {
    void refreshTrayStatus();
  }, 2000);
}

function quitApplication() {
  isQuitting = true;
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (_) {}
  }
  if (staticServer) {
    try {
      staticServer.close();
    } catch (_) {}
  }
  if (statusPollInterval) clearInterval(statusPollInterval);
  app.quit();
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
  if (process.platform !== 'darwin' && isQuitting) app.quit();
});

app.on('will-quit', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (_) {}
  }
  if (staticServer) {
    try {
      staticServer.close();
    } catch (_) {}
  }
  if (statusPollInterval) clearInterval(statusPollInterval);
});
