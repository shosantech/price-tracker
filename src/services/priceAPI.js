// src/services/priceAPI.js
const API_URL = import.meta.env.VITE_PRICE_API_URL;

export async function fetchPrice() {
  try {
    if (!API_URL) throw new Error("Missing VITE_PRICE_API_URL in .env");

    const resp = await fetch(API_URL);
    if (!resp.ok) throw new Error("Network response not ok: " + resp.status);

    const data = await resp.json();
    if (!Array.isArray(data) || data.length === 0) throw new Error("Invalid data structure");

    // pick the AT platform entry
    const at = data.find(item => item.topo?.platform === "AT");
    if (!at) throw new Error("AT platform entry not found");

    const prices = at.spreadProfilePrices;
    if (!Array.isArray(prices) || prices.length === 0) throw new Error("No spreadProfilePrices data");

    // pick 'standard' spreadProfile
    const standard = prices.find(p => p.spreadProfile === "standard");
    if (!standard) throw new Error("standard spreadProfile not found in AT");

    const { bid, ask } = standard;
    const mid = (bid + ask) / 2;

    return { bid, ask, mid, spreadProfile: "standard", timestamp: at.ts };

  } catch (err) {
    console.error("fetchPrice error:", err);
    return null;
  }
}
