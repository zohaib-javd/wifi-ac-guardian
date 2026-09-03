const { app, BrowserWindow, Tray, Menu, nativeImage, shell, ipcMain, dialog } = require('electron');
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
let backendRestartTimer = null;
let backendRestartAttempts = 0;
let currentStatusIcon = null;
let trayProtectionRunning = false;
let pendingSecondInstanceActivation = false;

function appendGuardianBackendLog(message) {
  try {
    const logPath = path.join(app.getPath('userData'), 'guardian-backend.log');
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.appendFileSync(logPath, `[${new Date().toISOString()}] ${message}\n`, 'utf8');
  } catch (error) {
    console.error('[Guardian backend log] Could not write startup evidence:', error);
  }
}

const STATIC_PORT = 39147;
const PYTHON_IPC_PORT = 39146;
const GUARDIAN_READY_TIMEOUT_MS = 20000;
const GUARDIAN_MAX_RESTART_ATTEMPTS = 5;
const GUARDIAN_RESTART_BASE_DELAY_MS = 3000;
const WINDOWS_RUN_KEY = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run';
const WINDOWS_RUN_VALUE = 'WiFi AC Guardian';
const WINDOWS_STARTUP_TASK = 'WiFi AC Guardian Startup';
const STATUS_ASSET_DIR = path.join(__dirname, 'public', 'status');

function guardianConfigPath() {
  return path.join(process.env.APPDATA || app.getPath('home'), 'wifi-ac-guardian', 'config.json');
}

function startupExecutablePath() {
  // Electron Builder's portable launcher exposes the original portable file.
  // Using process.execPath alone would register its temporary unpack directory,
  // which no longer exists at the next Windows sign-in.
  return process.env.PORTABLE_EXECUTABLE_FILE || process.execPath;
}

function startupCommand() {
  return `"${startupExecutablePath()}" --startup`;
}

function runRegistryCommand(args) {
  const result = require('child_process').spawnSync('reg.exe', args, {
    windowsHide: true,
    encoding: 'utf8',
  });
  return result;
}

function runTaskSchedulerCommand(args) {
  return require('child_process').spawnSync('schtasks.exe', args, {
    windowsHide: true,
    encoding: 'utf8',
  });
}

function updateWindowsStartupRegistration(autoStart, startMinimized) {
  const executable = startupExecutablePath();
  // This release uses asInvoker. A per-user Run-key entry can therefore launch
  // it at sign-in without creating an elevated scheduled task or UAC failure.
  // The reg.exe block below is the single source of truth for that entry.
  // openAtLogin is always false here so Electron's own login-item mechanism
  // never writes a second, differently-named Run-key value for the same
  // launch (it previously did, alongside the one below, leaving two
  // competing startup entries that both launched the app at every sign-in).
  app.setLoginItemSettings({ openAtLogin: false, path: executable, args: ['--startup'] });

  if (autoStart) {
    const result = runRegistryCommand([
      'ADD', WINDOWS_RUN_KEY, '/v', WINDOWS_RUN_VALUE, '/t', 'REG_SZ', '/d', startupCommand(), '/f',
    ]);
    if (result.status !== 0) {
      throw new Error((result.stderr || result.stdout || 'Windows could not create the startup entry.').trim());
    }
    const verification = runRegistryCommand(['QUERY', WINDOWS_RUN_KEY, '/v', WINDOWS_RUN_VALUE]);
    if (verification.status !== 0 || !String(verification.stdout || '').includes(WINDOWS_RUN_VALUE)) {
      throw new Error('Windows startup registration could not be verified.');
    }
    // Remove the incompatible elevated task left by earlier releases.
    runTaskSchedulerCommand(['/Delete', '/TN', WINDOWS_STARTUP_TASK, '/F']);
  } else {
    // A missing task/value is an already-disabled startup configuration.
    runTaskSchedulerCommand(['/Delete', '/TN', WINDOWS_STARTUP_TASK, '/F']);
    runRegistryCommand(['DELETE', WINDOWS_RUN_KEY, '/v', WINDOWS_RUN_VALUE, '/f']);
  }

  appendGuardianBackendLog(`Windows Run-key startup registration updated: enabled=${autoStart}, minimized=${startMinimized}, command=${startupCommand()}`);
}

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
    updateWindowsStartupRegistration(autoStart, startMinimized);
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

const gotTheLock = app.requestSingleInstanceLock({ appId: 'com.wifiacguardian.app' });

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // The installed app and the portable app both route a normal duplicate
    // Electron launch here. Keep the existing dashboard rather than opening a
    // second Guardian backend or surfacing a duplicate-instance error.
    pendingSecondInstanceActivation = true;
    showDashboard();
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

function startStaticServer() {
  const outDir = path.join(__dirname, 'out');
  const entryPoint = path.join(outDir, 'index.html');
  if (!fs.existsSync(entryPoint)) {
    throw new Error(
      `The packaged dashboard export is missing (${entryPoint}). ` +
      'Rebuild with "npm run dist" so the static UI is included in the application.',
    );
  }
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

  return new Promise((resolve, reject) => {
    staticServer.once('error', (err) => {
      console.error('[Electron] Static server error:', err);
      reject(new Error(`Dashboard server could not start on port ${STATIC_PORT}: ${err.message}`));
    });

    staticServer.listen(STATIC_PORT, '127.0.0.1', () => {
      console.log(`[Electron] Static UI server listening on http://127.0.0.1:${STATIC_PORT}`);
      resolve();
    });
  });
}

function startPythonBackend() {
  if (pythonProcess) return;
  // Production builds use a PyInstaller bundle. Customers never need Python,
  // pystray, Pillow, or a PATH entry to start the Guardian daemon.
  const backendPath = app.isPackaged
    ? path.join(process.resourcesPath, 'guardian-backend.exe')
    : path.join(__dirname, 'build_backend', 'guardian-backend.exe');

  if (!fs.existsSync(backendPath)) {
    const error = new Error(`Guardian backend executable is missing: ${backendPath}`);
    appendGuardianBackendLog(`FATAL: ${error.message}`);
    throw error;
  }

  appendGuardianBackendLog(`Starting packaged Guardian backend: ${backendPath}`);
  pythonProcess = spawn(backendPath, ['--daemon', '--no-tray'], {
    cwd: path.dirname(backendPath),
    detached: false,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
    env: { ...process.env, GUARDIAN_LAUNCHED_BY_ELECTRON: '1' },
  });
  pythonProcess.stdout.on('data', (data) => {
    appendGuardianBackendLog(`STDOUT: ${data.toString().trimEnd()}`);
  });
  pythonProcess.stderr.on('data', (data) => {
    appendGuardianBackendLog(`STDERR: ${data.toString().trimEnd()}`);
  });
  pythonProcess.on('error', (error) => {
    appendGuardianBackendLog(`SPAWN ERROR: ${error.message}`);
    console.error('Failed to start Guardian backend:', error);
  });
  pythonProcess.on('exit', (code, signal) => {
    appendGuardianBackendLog(`EXIT: code=${code ?? 'null'}, signal=${signal ?? 'none'}`);
    pythonProcess = null;
    if (code === 78) {
      // The backend deliberately stepped aside because a healthy primary
      // instance is already running (single-instance hand-off, not a
      // failure). Respawning here would just repeat the same hand-off
      // forever, so leave the existing instance alone.
      appendGuardianBackendLog('Guardian backend deferred to an existing primary instance; no restart needed.');
      backendRestartAttempts = 0;
      void refreshTrayStatus();
      return;
    }
    scheduleGuardianRestart(`exit code=${code ?? 'null'}, signal=${signal ?? 'none'}`);
  });
  console.log(`[Electron] Packaged Guardian backend spawned: ${backendPath}`);
}

function scheduleGuardianRestart(reason) {
  if (isQuitting || backendRestartTimer || pythonProcess) return;
  if (backendRestartAttempts >= GUARDIAN_MAX_RESTART_ATTEMPTS) {
    appendGuardianBackendLog(`Guardian restart limit reached after ${GUARDIAN_MAX_RESTART_ATTEMPTS} attempts; manual restart required.`);
    return;
  }

  const delay = Math.min(30000, GUARDIAN_RESTART_BASE_DELAY_MS * (2 ** backendRestartAttempts));
  backendRestartAttempts += 1;
  appendGuardianBackendLog(`Guardian restart ${backendRestartAttempts}/${GUARDIAN_MAX_RESTART_ATTEMPTS} scheduled in ${delay} ms (${reason}).`);

  backendRestartTimer = setTimeout(async () => {
    backendRestartTimer = null;
    if (isQuitting || pythonProcess) return;
    try {
      startPythonBackend();
      await waitForGuardianReady();
      backendRestartAttempts = 0;
      appendGuardianBackendLog('Guardian backend watchdog restart completed and IPC is ready.');
      await refreshTrayStatus();
    } catch (error) {
      appendGuardianBackendLog(`Guardian watchdog restart failed: ${error instanceof Error ? error.message : String(error)}`);
      if (pythonProcess) {
        try { pythonProcess.kill(); } catch (_) {}
        pythonProcess = null;
      }
      scheduleGuardianRestart('previous watchdog restart failed');
    }
  }, delay);
}

function waitForGuardianReady(timeoutMs = GUARDIAN_READY_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const probe = () => {
      if (!pythonProcess) {
        reject(new Error('Guardian backend exited before it became ready.'));
        return;
      }
      const request = http.get({ host: '127.0.0.1', port: PYTHON_IPC_PORT, path: '/', timeout: 1200 }, (response) => {
        response.resume();
        if (response.statusCode === 200) {
          appendGuardianBackendLog('Guardian IPC is ready.');
          resolve();
          return;
        }
        retry(new Error(`Guardian IPC returned HTTP ${response.statusCode}.`));
      });
      request.on('timeout', () => request.destroy(new Error('Guardian IPC readiness probe timed out.')));
      request.on('error', retry);
    };

    const retry = (lastError) => {
      if (Date.now() >= deadline) {
        appendGuardianBackendLog(`FATAL: Guardian IPC did not become ready: ${lastError.message}`);
        reject(new Error(`Guardian backend did not become ready within ${Math.round(timeoutMs / 1000)} seconds. See guardian-backend.log for details.`));
        return;
      }
      setTimeout(probe, 250);
    };

    probe();
  });
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
    let startMinimized = false;
    try {
      if (fs.existsSync(guardianConfigPath())) {
        startMinimized = JSON.parse(fs.readFileSync(guardianConfigPath(), 'utf-8')).start_minimized === true;
      }
    } catch (error) {
      console.log('[Electron] Could not read config for start_minimized:', error.message);
    }
    const launchedAtStartup = process.argv.includes('--startup');
    if (!(launchedAtStartup && startMinimized)) mainWindow.show();
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
  if (!app.isReady()) {
    pendingSecondInstanceActivation = true;
    return;
  }
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow();
    return;
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.moveTop();
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
  if (backendRestartTimer) clearTimeout(backendRestartTimer);
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

app.whenReady().then(async () => {
  try {
    await startStaticServer();
    startPythonBackend();
    await waitForGuardianReady();
    createWindow();
    createSystemTray();
    if (pendingSecondInstanceActivation) showDashboard();
  } catch (error) {
    console.error('[Electron] Fatal startup error:', error);
    dialog.showErrorBox(
      'WiFi AC Guardian could not start',
      error instanceof Error ? error.message : 'The dashboard could not be loaded.',
    );
    app.quit();
    return;
  }
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' && isQuitting) app.quit();
});

app.on('will-quit', () => {
  if (backendRestartTimer) clearTimeout(backendRestartTimer);
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
