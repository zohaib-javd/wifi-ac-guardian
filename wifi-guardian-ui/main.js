const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let tray = null;
let pythonProcess = null;
let isQuitting = false;

// Spawn Python Guardian Engine in background
function startPythonBackend() {
  try {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    pythonProcess = spawn(pythonExe, ['-m', 'wifi_ac_guardian_win', '--daemon'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'ignore',
      detached: false,
    });
    console.log('[Electron] Python Guardian Engine spawned successfully.');
  } catch (err) {
    console.error('[Electron] Failed to spawn Python backend:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1100,
    minHeight: 760,
    backgroundColor: '#0D0F10',
    title: 'WiFi AC Guardian',
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Load Next.js production build or dev server
  const isDev = process.env.NODE_ENV === 'development';
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'out', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Minimize to System Tray on Close
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

function createSystemTray() {
  const iconPath = path.join(__dirname, 'public', 'router.png');
  const icon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  
  tray = new Tray(icon);
  tray.setToolTip('WiFi AC Guardian — Protected');

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
          await fetch('http://127.0.0.1:39146', {
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
}

app.whenReady().then(() => {
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
});
