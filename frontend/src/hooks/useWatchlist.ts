import { useEffect, useState } from "react";

const STORAGE_KEY = "crypto_ta_watchlist";

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        setWatchlist(parsed);
      }
    } catch (err) {
      console.error("Failed to parse watchlist", err);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
  }, [watchlist]);

  const addSymbol = (symbol: string) => {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) return;
    setWatchlist((prev) =>
      prev.includes(normalized) ? prev : [...prev, normalized],
    );
  };

  const removeSymbol = (symbol: string) => {
    setWatchlist((prev) => prev.filter((s) => s !== symbol));
  };

  return { watchlist, addSymbol, removeSymbol, setWatchlist };
}
