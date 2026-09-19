import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { useIntelligence } from '../../context/IntelligenceContext';

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { launchDemoScenario, isDemoActive } = useIntelligence();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    if (location.pathname !== '/') {
      navigate(`/#${sectionId}`);
      setTimeout(() => {
        const el = document.getElementById(sectionId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      const el = document.getElementById(sectionId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const isConsole = location.pathname.startsWith('/dashboard');

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled || isConsole
          ? 'bg-[#04060a]/90 backdrop-blur-md border-b border-white/[0.07] py-3.5'
          : 'bg-gradient-to-b from-[#04060a]/80 via-[#04060a]/40 to-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Brand Identity */}
        <Link to="/" className="flex items-center gap-3.5 group">
          <div className="w-8 h-8 rounded border border-white/15 bg-white/[0.02] flex items-center justify-center group-hover:border-emerald-500/50 transition-colors">
            <div className="w-2 h-2 rounded-full bg-emerald-400 group-hover:scale-125 transition-transform" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-heading font-extrabold tracking-tight text-base text-white">ORBITINTEL</span>
              <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border border-white/10 text-slate-400">SIH 2026</span>
            </div>
            <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase -mt-0.5">SATQUERY-AI</span>
          </div>
        </Link>

        {/* Primary Navigation */}
        <nav className="hidden md:flex items-center gap-8 text-[11px] font-mono uppercase tracking-widest text-slate-400">
          <button
            onClick={() => scrollToSection('platform')}
            className="hover:text-white transition-colors cursor-pointer"
          >
            PLATFORM
          </button>
          <Link
            to="/search"
            className={`hover:text-white transition-colors ${
              location.pathname === '/search' ? 'text-white font-semibold' : ''
            }`}
          >
            SEARCH
          </Link>
          <Link
            to="/alerts"
            className={`hover:text-white transition-colors ${
              location.pathname === '/alerts' ? 'text-white font-semibold' : ''
            }`}
          >
            ALERTS
          </Link>
          <Link
            to="/analysis/analysis_tumakuru_01"
            className={`hover:text-white transition-colors ${
              location.pathname.startsWith('/analysis') ? 'text-white font-semibold' : ''
            }`}
          >
            ANALYSIS
          </Link>
        </nav>

        {/* Actions & Console Launch */}
        <div className="flex items-center gap-4">
          {/* Subtle Demo Toggle */}
          <button
            onClick={() => {
              launchDemoScenario();
              navigate('/dashboard');
            }}
            className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] font-mono uppercase tracking-wider border transition-all ${
              isDemoActive
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                : 'border-white/10 text-slate-400 hover:text-slate-200 hover:border-white/20'
            }`}
            title="Load Tumakuru Corridor demonstration"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>DEMO SCENARIO</span>
          </button>

          {/* Launch Console CTA */}
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded border border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 hover:text-emerald-200 font-mono text-[11px] uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(16,185,129,0.15)]"
          >
            <span>LAUNCH ANALYST CONSOLE</span>
            <span className="text-emerald-400">&rarr;</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
