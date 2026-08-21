const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  send: (channel, data) => ipcRenderer.send(channel, data),
  on: (channel, func) => ipcRenderer.on(channel, (event, ...args) => func(...args)),
  openLogFile: () => ipcRenderer.invoke('open-log-file'),
  setLoginStartup: (options) => ipcRenderer.invoke('set-login-startup', options),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
});

