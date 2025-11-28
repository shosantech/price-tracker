import React, { useEffect, useState, useRef } from 'react';
import PriceChart from './components/PriceChart.jsx';
import SettingsPanel from './components/SettingsPanel.jsx';

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

  // load saved settings
  useEffect(() => {
    let mounted = true;
    window.api.getSettings().then(s => {
      if (!mounted) return;
      if (s) setSettings(prev => ({ ...prev, ...s }));
    }).catch(console.error);
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchOnce() {
      try {
        const result = await window.api.getPrice();
        if (!result) return;
        handlePrice(result.mid);
      } catch (err) { console.error(err); }
    }

    function handlePrice(price) {
      setCurrentPrice(price);
      setHistory(prev => [...prev.slice(-199), { time: new Date().toLocaleTimeString(), price }]);

      const setP = Number(settings.setPrice) || 0;
      const threshold = Number(settings.thresholdPercent) || 10;
      if (setP > 0) {
        const diffPercent = Math.abs((price - setP) / setP) * 100;
        if (diffPercent >= threshold && !lastNotifiedRef.current) {
          lastNotifiedRef.current = true;
          window.api.notify(`Price moved ${diffPercent.toFixed(2)}% from your set price. Current: $${price.toFixed(2)}`);
        } else if (diffPercent < threshold) lastNotifiedRef.current = false;
      }
    }

    fetchOnce();
    const interval = setInterval(fetchOnce, Math.max(1000, (Number(settings.pollingInterval) || 5) * 1000));
    return () => { cancelled = true; clearInterval(interval); };
  }, [settings.setPrice, settings.pollingInterval, settings.thresholdPercent]);

  const handleSettingsSave = async (newSettings) => {
    try {
      const saved = await window.api.saveSettings(newSettings);
      setSettings(prev => ({ ...prev, ...saved }));
    } catch (err) { console.error(err); }
  };

  return (
    <div className="app-root">
      <header className="header">
        <h1>Price Tracker</h1>
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
