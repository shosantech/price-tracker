// src/components/SettingsPanel.jsx
import React, { useState, useEffect } from 'react'

export default function SettingsPanel({ settings = {}, onSave }) {
  const [form, setForm] = useState({
    setPrice: settings.setPrice || 0,
    buyPrice: settings.buyPrice || 0,
    thresholdPercent: settings.thresholdPercent || 10,
    pollingInterval: settings.pollingInterval || 5
  });

  useEffect(() => {
    setForm({
      setPrice: settings.setPrice || 0,
      buyPrice: settings.buyPrice || 0,
      thresholdPercent: settings.thresholdPercent || 10,
      pollingInterval: settings.pollingInterval || 5
    });
  }, [settings]);

  const handleChange = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const save = () => {
    // convert numeric fields
    const payload = {
      setPrice: Number(form.setPrice) || 0,
      buyPrice: Number(form.buyPrice) || 0,
      thresholdPercent: Number(form.thresholdPercent) || 10,
      pollingInterval: Number(form.pollingInterval) || 5
    };
    if (onSave) onSave(payload);
  };

  return (
    <div className="settings">
      <h3>Settings</h3>

      <label>Set Price (USD)</label>
      <input type="number" value={form.setPrice} onChange={(e) => handleChange('setPrice', e.target.value)} />

      <label>Buy Price (USD)</label>
      <input type="number" value={form.buyPrice} onChange={(e) => handleChange('buyPrice', e.target.value)} />

      <label>Threshold % (notify when ± this %)</label>
      <input type="number" value={form.thresholdPercent} onChange={(e) => handleChange('thresholdPercent', e.target.value)} />

      <label>Polling Interval (seconds)</label>
      <input type="number" value={form.pollingInterval} onChange={(e) => handleChange('pollingInterval', e.target.value)} />

      <div style={{ marginTop: 10 }}>
        <button onClick={save}>Save</button>
      </div>
    </div>
  )
}
