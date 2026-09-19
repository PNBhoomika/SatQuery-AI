import React, { useState, useRef, useEffect } from 'react';
import { Columns, SplitSquareVertical, Eye, Layers } from 'lucide-react';

interface BeforeAfterSliderProps {
  beforeImage: string;
  afterImage: string;
  changeMask?: string;
  changeHeatmap?: string;
  beforeDate?: string;
  afterDate?: string;
  confidence?: number;
  changeType?: string;
  affectedArea?: string;
  height?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeImage,
  afterImage,
  changeMask,
  changeHeatmap,
  beforeDate = '12 JUN 2024',
  afterDate = '18 JUN 2026',
  confidence = 0.87,
  changeType = 'New Construction / Urban Expansion',
  affectedArea = '18.4 hectares',
  height = '520px',
}) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [viewMode, setViewMode] = useState<'slider' | 'side-by-side' | 'mask-overlay'>('slider');
  const [maskOpacity, setMaskOpacity] = useState(70);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  const updatePosition = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    setSliderPosition((x / rect.width) * 100);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    updatePosition(e.clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!e.touches[0]) return;
    updatePosition(e.touches[0].clientX);
  };

  useEffect(() => {
    const onMouseUp = () => setIsDragging(false);
    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        updatePosition(e.clientX);
      }
    };
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onMouseMove);
    return () => {
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onMouseMove);
    };
  }, [isDragging]);

  return (
    <div className="w-full flex flex-col space-y-3 select-none">
      {/* ── Top Bar & Status Overlay ─────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-white/[0.08] bg-[#070a10]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-[11px] font-bold">
            CHANGE DETECTED
          </div>
          <div className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[11px] font-bold">
            {Math.round(confidence * 100)}% CONFIDENCE
          </div>
        </div>

        {/* View Mode Controls */}
        <div className="flex items-center gap-1.5 text-xs font-mono">
          {(['slider', 'side-by-side', 'mask-overlay'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setViewMode(mode)}
              className={`px-2.5 py-1 rounded uppercase tracking-wider text-[10px] transition-colors ${
                viewMode === mode
                  ? 'bg-white/10 text-white font-bold border border-white/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {mode.replace('-', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* ── Main View Container ──────────────────────────────────────── */}
      {viewMode === 'slider' && (
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onTouchMove={handleTouchMove}
          style={{ height }}
          className="relative w-full rounded-2xl overflow-hidden border border-white/[0.12] bg-[#04060a] cursor-ew-resize"
        >
          {/* After Image (Background / Full Width) */}
          <img
            src={afterImage}
            alt="After change"
            className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            onError={(e) => {
              // Graceful fallback display
              (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500"><rect fill="%230b101b" width="800" height="500"/><text fill="%2310b981" font-family="monospace" font-size="20" x="50%25" y="50%25" text-anchor="middle">AFTER IMAGERY // POST-EXPANSION (T2)</text></svg>';
            }}
          />

          {/* Before Image (Foreground Clipped) */}
          <div
            className="absolute inset-0 overflow-hidden pointer-events-none"
            style={{ width: `${sliderPosition}%` }}
          >
            <img
              src={beforeImage}
              alt="Before change"
              className="absolute inset-0 h-full object-cover max-w-none pointer-events-none"
              style={{
                width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100vw',
              }}
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500"><rect fill="%23070a10" width="800" height="500"/><text fill="%2394a3b8" font-family="monospace" font-size="20" x="50%25" y="50%25" text-anchor="middle">BEFORE IMAGERY // BASELINE (T1)</text></svg>';
              }}
            />
          </div>

          {/* Change Mask Overlay (optional translucent layer) */}
          {changeMask && (
            <img
              src={changeMask}
              alt="Change Mask"
              style={{ opacity: maskOpacity / 100 }}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none mix-blend-screen"
            />
          )}

          {/* Draggable Divider Line */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 pointer-events-none shadow-[0_0_12px_rgba(16,185,129,0.8)]"
            style={{ left: `${sliderPosition}%` }}
          >
            {/* Center Slider Handle */}
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full border border-emerald-400 bg-[#04060a]/90 backdrop-blur-md flex items-center justify-center shadow-2xl">
              <div className="flex items-center gap-0.5 text-emerald-300 font-mono text-[10px] font-bold">
                <span>&lsaquo;</span>
                <span>&rsaquo;</span>
              </div>
            </div>
          </div>

          {/* Small Date Label: BEFORE */}
          <div className="absolute top-4 left-4 z-10 px-3 py-2 rounded border border-white/15 bg-[#04060a]/85 backdrop-blur-md pointer-events-none">
            <span className="block text-[9px] font-mono text-slate-400 uppercase tracking-widest">BEFORE SCENE</span>
            <span className="text-xs font-mono font-bold text-white tracking-wide">{beforeDate}</span>
            <span className="block text-[9px] font-mono text-slate-400 mt-0.5">SENTINEL-2A MSI</span>
          </div>

          {/* Small Date Label: AFTER */}
          <div className="absolute top-4 right-4 z-10 px-3 py-2 rounded border border-white/15 bg-[#04060a]/85 backdrop-blur-md pointer-events-none text-right">
            <span className="block text-[9px] font-mono text-slate-400 uppercase tracking-widest">AFTER SCENE</span>
            <span className="text-xs font-mono font-bold text-emerald-400 tracking-wide">{afterDate}</span>
            <span className="block text-[9px] font-mono text-emerald-400/80 mt-0.5">EXPANSION VERIFIED</span>
          </div>

          {/* Bottom Left: Sensor & Coordinates Metadata */}
          <div className="absolute bottom-4 left-4 z-10 px-3 py-1.5 rounded border border-white/10 bg-[#04060a]/85 backdrop-blur-md pointer-events-none hidden sm:flex items-center gap-3 text-[10px] font-mono text-slate-300">
            <span className="text-cyan-400 font-bold">13.3408° N, 77.1009° E</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">GSD: 10M</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">EPSG: 32643 (UTM 43N)</span>
          </div>

          {/* Bottom Right: Change Region Telemetry */}
          <div className="absolute bottom-4 right-4 z-10 px-3 py-1.5 rounded border border-rose-500/40 bg-[#04060a]/90 backdrop-blur-md pointer-events-none flex items-center gap-2 text-[10px] font-mono">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <span className="text-slate-400">DETECTED:</span>
            <span className="text-rose-300 font-bold">{affectedArea}</span>
          </div>
        </div>
      )}

      {/* Mode 2: Side-by-Side Comparison */}
      {viewMode === 'side-by-side' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative rounded-xl overflow-hidden border border-white/10 h-[420px] bg-black">
            <img src={beforeImage} alt="Before" className="w-full h-full object-cover" />
            <div className="absolute top-3 left-3 px-2.5 py-1.5 rounded bg-[#04060a]/80 border border-white/10 font-mono text-xs text-white">
              BEFORE // {beforeDate}
            </div>
          </div>
          <div className="relative rounded-xl overflow-hidden border border-white/10 h-[420px] bg-black">
            <img src={afterImage} alt="After" className="w-full h-full object-cover" />
            <div className="absolute top-3 left-3 px-2.5 py-1.5 rounded bg-[#04060a]/80 border border-white/10 font-mono text-xs text-emerald-400">
              AFTER // {afterDate}
            </div>
          </div>
        </div>
      )}

      {/* Mode 3: Mask Overlay */}
      {viewMode === 'mask-overlay' && (
        <div className="space-y-3">
          <div className="relative rounded-xl overflow-hidden border border-white/10 h-[460px] bg-black">
            <img src={afterImage} alt="After" className="w-full h-full object-cover" />
            {changeMask && (
              <img
                src={changeMask}
                alt="Change Mask"
                style={{ opacity: maskOpacity / 100 }}
                className="absolute inset-0 w-full h-full object-cover mix-blend-screen"
              />
            )}
            <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded bg-[#04060a]/80 border border-white/10 text-xs font-mono text-white">
              CHANGE MASK OVERLAY (OPACITY: {maskOpacity}%)
            </div>
          </div>

          <div className="flex items-center gap-3 px-2 text-xs font-mono text-slate-400">
            <span>Mask Opacity:</span>
            <input
              type="range"
              min="0"
              max="100"
              value={maskOpacity}
              onChange={(e) => setMaskOpacity(Number(e.target.value))}
              className="w-48 accent-emerald-400 cursor-pointer"
            />
            <span>{maskOpacity}%</span>
          </div>
        </div>
      )}
    </div>
  );
};
