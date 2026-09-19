import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { IntelligenceProvider } from './context/IntelligenceContext';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { AlertsPage } from './pages/AlertsPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { RotatingEarth } from './components/common/RotatingEarth';

export const App: React.FC = () => {
  return (
    <IntelligenceProvider>
      <Router>
        <div className="relative flex flex-col min-h-screen bg-[#07090e] text-[#f8fafc]">
          {/*
           * RotatingEarth — persistent fixed background layer.
           * Mounted ONCE here so it never remounts on route changes or scroll.
           * pointer-events: none (inside component) — never intercepts clicks.
           * z-index: 0 — sits behind all page content.
           * Different opacity per-page is not needed: the Earth sits behind
           * each page's own background, which provides the per-page opacity control.
           */}
          <RotatingEarth />

          {/* All page content and navigation floats above Earth at z-10+ */}
          <div className="relative z-10 flex flex-col min-h-screen">
            <Navbar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/analysis/:id" element={<AnalysisPage />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </div>
      </Router>
    </IntelligenceProvider>
  );
};

export default App;
