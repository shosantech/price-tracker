const { app, BrowserWindow, Tray, Menu, ipcMain, Notification } = require('electron');
const path = require('path');
const http = require('http');
const Store = require('electron-store');

const store = new Store({ defaults: { targetPrice: 2000, buyPrice: 1900 } });
let mainWindow, tray;

function waitForServer(url, timeout = 30000, interval = 500) {
  return new Promise((resolve, reject) => {
    const start = Date.now();

    const check = () => {
      http.get(url, () => resolve()).on('error', () => {
        if (Date.now() - start > timeout) reject(new Error('Server timeout'));
        else setTimeout(check, interval);
      });
    };

    check();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  });

  if (!app.isPackaged) {
    try {
      console.log('Waiting for Vite dev server...');
      await waitForServer('http://localhost:5173');
      console.log('Vite is ready!');
      mainWindow.loadURL('http://localhost:5173');
    } catch (err) {
      console.error('Failed to connect to Vite:', err);
    }
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.on('close', (e) => {
    e.preventDefault();
    mainWindow.hide();
  });
}

function createTray() {
  const iconPath = path.join(__dirname, 'tray-icon.png');
  tray = new Tray(iconPath);
  tray.setToolTip('Gold Price Tracker');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Show App', click: () => mainWindow.show() },
    { label: 'Quit', click: () => app.quit() }
  ]));
  tray.on('click', () => mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show());
  console.log('Tray created:', iconPath);
}

app.whenReady().then(() => {
  createWindow();
  createTray();
  console.log('App ready');
});

ipcMain.on('update-settings', (e, data) => { store.set(data); e.reply('settings-updated', store.store); });
ipcMain.on('notify', (e, message) => new Notification({ title: 'Gold Tracker', body: message }).show());

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
