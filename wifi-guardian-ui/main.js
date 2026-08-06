const { app, BrowserWindow, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let tray = null;
let pythonProcess = null;
let staticServer = null;
let isQuitting = false;

const STATIC_PORT = 39147;

// Ensure single desktop instance
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

// Start Built-in Node Static Server for Next.js App
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
      console.log(`[Electron] Port ${STATIC_PORT} already bound by active primary instance.`);
    } else {
      console.error('[Electron] Static server error:', err);
    }
  });

  staticServer.listen(STATIC_PORT, '127.0.0.1', () => {
    console.log(`[Electron] Static UI server running on http://127.0.0.1:${STATIC_PORT}`);
  });
}

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
    width: 960,
    height: 740,
    minWidth: 880,
    minHeight: 660,
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

  // Load from local static server
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

function createSystemTray() {
  const iconPath = path.join(__dirname, 'public', 'wifi_icon.png');
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
        if (staticServer) {
          try {
            staticServer.close();
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
});
