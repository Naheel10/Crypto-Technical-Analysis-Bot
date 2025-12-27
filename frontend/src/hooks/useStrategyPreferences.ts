import { useEffect, useState } from "react";

const STORAGE_KEY = "crypto_ta_enabled_strategies";

export function useStrategyPreferences(allStrategyNames: string[]) {
  const [enabled, setEnabled] = useState<string[]>([]);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as string[];
        setEnabled(parsed.filter((name) => allStrategyNames.includes(name)));
        return;
      } catch {
        // ignore parse error
      }
    }
    setEnabled(allStrategyNames);
  }, [allStrategyNames.join(",")]);

  const toggleStrategy = (name: string) => {
    setEnabled((prev) => {
      const exists = prev.includes(name);
      const next = exists
        ? prev.filter((n) => n !== name)
        : [...prev, name];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const enableAll = () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(allStrategyNames));
    setEnabled(allStrategyNames);
  };

  const disableAll = () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
    setEnabled([]);
  };

  return {
    enabledStrategies: enabled,
    toggleStrategy,
    enableAll,
    disableAll,
  };
}
