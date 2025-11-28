const { app, BrowserWindow, Tray, Menu, ipcMain, Notification } = require('electron');
const path = require('path');
const http = require('http');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const Store = require('electron-store');
require('dotenv').config(); // load .env

const API_URL = process.env.VITE_PRICE_API;

const store = new Store({
  defaults: {
    setPrice: 2000,
    buyPrice: 1900,
    thresholdPercent: 10,
    pollingInterval: 5
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
        res.resume();
        resolve();
      }).on('error', () => {
        if (Date.now() - start > timeout) reject(new Error('Server timeout'));
        else setTimeout(check, interval);
      });
    };
    check();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    try {
      console.log('Waiting for Vite dev server...');
      await waitForServer('http://localhost:5173', 30000, 300);
      console.log('Vite ready');
      await mainWindow.loadURL('http://localhost:5173');
    } catch (err) {
      console.error('Vite server unreachable', err);
      mainWindow.loadURL('http://localhost:5173').catch(() => {});
    }
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());

  mainWindow.on('close', (e) => {
    if (!app.isQuiting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  const iconPath = path.join(__dirname, 'tray-icon.png');
  tray = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show App', click: () => mainWindow?.show() },
    { label: 'Open Settings', click: () => mainWindow?.webContents.send('open-settings') },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuiting = true; app.quit(); } }
  ]);
  tray.setToolTip('Price Tracker');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => mainWindow?.isVisible() ? mainWindow.hide() : mainWindow.show());
  console.log('Tray created');
}

app.whenReady().then(() => {
  createTray();
  createWindow();
});

// ---------------- IPC ----------------

// fetch price from AT / standard spreadProfile
ipcMain.handle('get-price', async () => {
  try {
    
    const res = await fetch(API_URL);
    const data = await res.json();
    const at = data.find(item => item.topo?.platform === 'AT');
    if (!at) throw new Error('AT platform not found');
    const standard = at.spreadProfilePrices.find(p => p.spreadProfile === 'standard');
    if (!standard) throw new Error('standard profile not found');
    return {
      bid: standard.bid,
      ask: standard.ask,
      mid: (standard.bid + standard.ask) / 2,
      spreadProfile: 'standard',
      timestamp: at.ts
    };
  } catch (err) {
    console.error('get-price error:', err);
    return null;
  }
});

ipcMain.handle('get-settings', async () => store.store);

ipcMain.handle('save-settings', async (event, newSettings) => {
  Object.keys(newSettings).forEach(k => store.set(k, newSettings[k]));
  return store.store;
});

ipcMain.on('notify', (event, message) => {
  try { new Notification({ title: 'Price Tracker', body: message }).show(); }
  catch (err) { console.error('Notification error', err); }
});

ipcMain.handle('manual-fetch', async () => ({ lastSaved: store.store, timestamp: Date.now() }));

app.on('window-all-closed', () => { });
