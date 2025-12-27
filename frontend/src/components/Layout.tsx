// frontend/src/components/Layout.tsx
import React from "react";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-emerald-500 flex items-center justify-center text-xs font-bold">
              TA
            </div>
            <div>
              <h1 className="text-lg font-semibold">
                Beginner Crypto TA Bot
              </h1>
              <p className="text-xs text-slate-400">
                LLM-powered explainable trade signals for absolute beginners.
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            Educational only • Not financial advice
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 py-6">{children}</div>
      </main>

      <footer className="border-t border-slate-800 text-xs text-slate-500 py-3 text-center">
        Built with FastAPI, ccxt, pandas, React, and Tailwind.
      </footer>
    </div>
  );
};
