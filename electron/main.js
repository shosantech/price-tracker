const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 900,
    height: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const url = process.env.VITE_DEV_SERVER_URL || `file://${path.join(__dirname, '..', 'dist', 'index.html')}`
  win.loadURL(url)
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  // We will keep the app running in tray later; for now quit on all windows closed (except macOS behaviour)
  if (process.platform !== 'darwin') app.quit()
})
