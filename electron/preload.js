const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getPrice: () => ipcRenderer.invoke('get-price'),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  notify: (message) => ipcRenderer.send('notify', message),
  manualFetch: () => ipcRenderer.invoke('manual-fetch'),
  on: (channel, callback) => {
    const validChannels = ['open-settings', 'price-alert'];
    if (!validChannels.includes(channel)) return;
    ipcRenderer.on(channel, (event, ...args) => callback(...args));
  }
});
