// frontend/src/components/LoadingSpinner.tsx
import React from "react";

export const LoadingSpinner: React.FC = () => (
  <div className="flex items-center gap-2 text-xs text-slate-300">
    <div className="h-3 w-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
    <span>Analyzing chart…</span>
  </div>
);
