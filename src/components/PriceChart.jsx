// src/components/PriceChart.jsx
import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts'

export default function PriceChart({ data = [], buyPrice, setPrice }) {
  // recharts expects numeric values; ensure data is shaped correctly
  const formatted = data.map(d => ({ time: d.time, price: Number(d.price) }));

  return (
    <div style={{ width: '100%', height: 360 }}>
      <ResponsiveContainer>
        <LineChart data={formatted} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" minTickGap={20} />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
          <Line type="monotone" dataKey="price" stroke="#0b74de" dot={false} strokeWidth={2} />
          {setPrice > 0 && <ReferenceLine y={setPrice} stroke="#28a745" label="Set Price" strokeDasharray="3 3" />}
          {buyPrice > 0 && <ReferenceLine y={buyPrice} stroke="#6f42c1" label="Buy Price" strokeDasharray="3 3" />}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
