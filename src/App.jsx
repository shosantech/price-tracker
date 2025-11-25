// src/App.jsx
import React, { useEffect, useState, useRef } from 'react'
import axios from 'axios'
import PriceChart from './components/PriceChart.jsx'
import SettingsPanel from './components/SettingsPanel.jsx'

export default function App() {
  const [settings, setSettings] = useState({
    setPrice: 2000,
    buyPrice: 1900,
    thresholdPercent: 10,
    pollingInterval: 5
  });
  const [currentPrice, setCurrentPrice] = useState(null);
  const [history, setHistory] = useState([]);
  const lastNotifiedRef = useRef(false);

  // load saved settings from electron-store via preload
  useEffect(() => {
    let mounted = true;
    window.api.getSettings().then(s => {
      if (!mounted) return
      if (s) setSettings(prev => ({ ...prev, ...s }));
    }).catch(err => console.error('getSettings error', err));
    return () => { mounted = false }
  }, []);

  // polling function
  useEffect(() => {
    let cancelled = false;
    async function fetchOnce() {
      try {
        // -- NOTE -- Replace this URL with your preferred gold API and API key.
        // Below is an example using Metals-API (you must signup and replace YOUR_API_KEY)
        // The response structure and access method may differ by provider.
        const API_KEY = '<REPLACE_WITH_YOUR_API_KEY>';
        if (!API_KEY || API_KEY === '<REPLACE_WITH_YOUR_API_KEY>') {
          // If no API key, do nothing (or you could mock data).
          // For demo you can use a fake/random price:
          const fake = 1800 + Math.random() * 200;
          handlePrice(fake);
          return;
        }
        const res = await axios.get(`https://metals-api.com/api/latest?access_key=${API_KEY}&base=USD&symbols=XAU`);
        const price = res.data && res.data.rates && res.data.rates.XAU ? Number(res.data.rates.XAU) : null;
        if (price) handlePrice(price);
      } catch (err) {
        // Do not spam console in production; keep for debugging
        console.error('fetch error', err);
      }
    }

    function handlePrice(price) {
      setCurrentPrice(price);
      setHistory(prev => {
        const next = [...prev.slice(-199), { time: new Date().toLocaleTimeString(), price }];
        return next;
      });

      // notification logic relative to setPrice
      const setP = Number(settings.setPrice) || 0;
      const threshold = Number(settings.thresholdPercent) || 10;
      if (setP > 0) {
        const diffPercent = Math.abs((price - setP) / setP) * 100;
        if (diffPercent >= threshold) {
          if (!lastNotifiedRef.current) {
            lastNotifiedRef.current = true;
            window.api.notify(`Gold moved ${diffPercent.toFixed(2)}% from your set price. Current: $${price.toFixed(2)}`);
            // also emit ipc event if you want: main could forward to other systems
          }
        } else {
          // reset notification latch when back within threshold
          lastNotifiedRef.current = false;
        }
      }
    }

    // first fetch immediately
    fetchOnce();

    // start interval
    const interval = setInterval(fetchOnce, Math.max(1000, (Number(settings.pollingInterval) || 5) * 1000));

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [settings.setPrice, settings.pollingInterval, settings.thresholdPercent]); // re-create if threshold/interval changes

  // handler for settings saved from SettingsPanel
  const handleSettingsSave = async (newSettings) => {
    try {
      const saved = await window.api.saveSettings(newSettings);
      setSettings(prev => ({ ...prev, ...saved }));
    } catch (err) {
      console.error('saveSettings error', err);
    }
  };

  return (
    <div className="app-root">
      <header className="header">
        <h1>Gold Price Tracker</h1>
        <div className="meta">Current: {currentPrice ? `$${Number(currentPrice).toFixed(2)}` : '—'}</div>
      </header>

      <main className="main">
        <section className="left">
          <PriceChart data={history} buyPrice={Number(settings.buyPrice)} setPrice={Number(settings.setPrice)} />
        </section>

        <aside className="right">
          <SettingsPanel settings={settings} onSave={handleSettingsSave} />
          <div className="card">
            <h4>Quick Info</h4>
            <p>Buy Price: <strong>{settings.buyPrice ? `$${Number(settings.buyPrice).toFixed(2)}` : '—'}</strong></p>
            <p>Alert Threshold: <strong>{settings.thresholdPercent}%</strong></p>
            <p>Polling: <strong>{settings.pollingInterval}s</strong></p>
          </div>
        </aside>
      </main>
    </div>
  );
}
