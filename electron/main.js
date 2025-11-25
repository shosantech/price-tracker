// electron/main.js
const { app, BrowserWindow, Tray, Menu, ipcMain, Notification } = require('electron');
const path = require('path');
const http = require('http');
const Store = require('electron-store');

const store = new Store({
  defaults: {
    setPrice: 2000,        // user-configurable "target" / set price
    buyPrice: 1900,
    thresholdPercent: 10,  // percent threshold for notifications
    pollingInterval: 5     // seconds (renderer polling interval; saved for completeness)
  }
});

const isDev = !app.isPackaged;
let mainWindow = null;
let tray = null;

function waitForServer(url, timeout = 30000, interval = 300) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      http.get(url, (res) => {
        // if any response arrives, assume server is up
        res.resume();
        resolve();
      }).on('error', () => {
        if (Date.now() - start > timeout) {
          reject(new Error('Server timeout'));
        } else {
          setTimeout(check, interval);
        }
      });
    };
    check();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    show: false, // start hidden; show after loaded or when user clicks tray
    webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false
        }
  });

  if (isDev) {
    try {
      console.log('Waiting for Vite dev server (http://localhost:5173) ...');
      await waitForServer('http://localhost:5173', 30000, 300);
      console.log('Vite dev server ready — loading URL.');
      await mainWindow.loadURL('http://localhost:5173');
    } catch (err) {
      console.error('Could not reach Vite dev server:', err);
      // still try to load; a blank window may appear
      mainWindow.loadURL('http://localhost:5173').catch(() => {});
    }
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  // Show when ready-to-show so content is not a blank window
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Hide to tray on close (common tray behaviour)
  mainWindow.on('close', (e) => {
    // On quit we want to actually close. We'll detect via app.isQuiting if needed.
    if (!app.isQuiting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  const iconPath = path.join(__dirname, 'tray-icon.png');
  try {
    tray = new Tray(iconPath);
  } catch (err) {
    console.error('Failed to load tray icon at', iconPath, err);
    // Fall back: create a dummy Tray only if possible — otherwise continue
    return;
  }

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show App', click: () => { if (mainWindow) mainWindow.show(); } },
    { label: 'Open Settings', click: () => { if (mainWindow) mainWindow.webContents.send('open-settings'); } },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuiting = true; app.quit(); } }
  ]);
  tray.setToolTip('Gold Price Tracker');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (!mainWindow) return;
    if (mainWindow.isVisible()) mainWindow.hide();
    else mainWindow.show();
  });

  console.log('Tray created with icon:', iconPath);
}

app.whenReady().then(() => {
  createTray();
  createWindow();
  console.log('App ready (main).');
});

// IPC handlers — renderer uses preload to call these
ipcMain.handle('get-settings', async () => {
  return store.store;
});

ipcMain.handle('save-settings', async (event, newSettings) => {
  Object.keys(newSettings).forEach(k => store.set(k, newSettings[k]));
  return store.store;
});

ipcMain.on('notify', (event, message) => {
  try {
    const n = new Notification({ title: 'Gold Tracker', body: String(message) });
    n.show();
  } catch (err) {
    console.error('Notification error', err);
  }
});

// allow renderer to request a manual fetch (optional — we return current store values)
ipcMain.handle('manual-fetch', async () => {
  return { lastSaved: store.store, timestamp: Date.now() };
});

app.on('window-all-closed', () => {
  // keep on tray — only quit on explicit Quit action
  if (process.platform !== 'darwin') {
    // do not quit automatically
  }
});
