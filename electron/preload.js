// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // get current stored settings
  getSettings: async () => {
    return await ipcRenderer.invoke('get-settings');
  },

  // save settings (object with keys like setPrice, buyPrice, thresholdPercent, pollingInterval)
  saveSettings: async (settings) => {
    return await ipcRenderer.invoke('save-settings', settings);
  },

  // send a notification via main
  notify: (message) => {
    ipcRenderer.send('notify', message);
  },

  // manual fetch helper (not used by core polling but available)
  manualFetch: async () => {
    return await ipcRenderer.invoke('manual-fetch');
  },

  // allow renderer to listen to arbitrary events from main if needed
  on: (channel, callback) => {
    const validChannels = ['open-settings', 'price-alert'];
    if (!validChannels.includes(channel)) return;
    ipcRenderer.on(channel, (event, ...args) => callback(...args));
  }
});
