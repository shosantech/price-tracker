const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  // placeholder APIs we will implement later
  ping: () => 'pong'
})
