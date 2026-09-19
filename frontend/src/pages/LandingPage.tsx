import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search,
  Layers,
  Activity,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Database,
  Radio,
  Satellite,
  Compass,
  SlidersHorizontal,
  ChevronRight,
  Maximize2,
  MapPin,
  Eye,
} from 'lucide-react';
import { BeforeAfterSlider } from '../components/comparison/BeforeAfterSlider';
import { OrbitalTelemetryCanvas } from '../components/common/OrbitalTelemetryCanvas';
import { useIntelligence } from '../context/IntelligenceContext';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { launchDemoScenario, submitFeedback } = useIntelligence();

  // Query Typing Animation for Section 01
  const [typedQuery, setTypedQuery] = useState('');
  const fullQuery = 'Find large construction areas near rivers';

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setTypedQuery(fullQuery.slice(0, index));
      index++;
      if (index > fullQuery.length) {
        clearInterval(interval);
      }
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Section 02 Active Sensor Layer
  const [activeSensor, setActiveSensor] = useState<'sentinel1' | 'sentinel2' | 'landsat' | 'bhuvan'>('sentinel2');

  // Section 03 feedback state
  const [demoStatus, setDemoStatus] = useState<'PENDING REVIEW' | 'CONFIRMED' | 'REJECTED'>('PENDING REVIEW');

  const handleConfirm = async () => {
    setDemoStatus('CONFIRMED');
    await submitFeedback({
      alert_id: 'ALT-2026-024',
      action: 'CONFIRM',
      analyst_notes: 'Verified via landing showcase.',
    });
  };

  const handleReject = async () => {
    setDemoStatus('REJECTED');
    await submitFeedback({
      alert_id: 'ALT-2026-024',
      action: 'REJECT',
      rationale: 'Seasonal variation',
      analyst_notes: 'Rejected via landing showcase.',
    });
  };

  return (
    <div className="min-h-screen page-bg-hero text-[#f8fafc] overflow-x-hidden selection:bg-emerald-500/20 selection:text-emerald-300">

      {/* =========================================================================
          HERO SECTION — LOOKING AT EARTH FROM SPACE
      ========================================================================= */}
      <section className="relative min-h-[96vh] flex items-center justify-center pt-24 pb-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Layer 1: Huge Cinematic Earth Satellite Photography Background */}
        <div className="absolute inset-0 z-0">
          <img
            src="/assets/hero_earth.jpg"
            alt="Earth from Space"
            className="w-full h-full object-cover object-center scale-105 transition-transform duration-[10000ms] ease-out pointer-events-none"
          />
          {/* Atmospheric Layering & Deep Vignette for Readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#04060a] via-[#04060a]/60 to-[#04060a]/40" />
          <div className="absolute inset-0 bg-radial-vignette pointer-events-none" />
        </div>

        {/* Layer 2: Moving Orbital Trajectories & Starfield Canvas */}
        <OrbitalTelemetryCanvas />

        {/* Layer 3: Faint Coordinate Geometry */}
        <div className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center opacity-25">
          <div className="w-[850px] h-[850px] rounded-full border border-dashed border-emerald-400/20" />
          <div className="absolute w-[1200px] h-[1200px] rounded-full border border-white/[0.04]" />
          {/* Coordinate Crosshairs */}
          <div className="absolute top-12 left-10 font-mono text-[10px] text-slate-500 tracking-widest uppercase">
            LAT 13°20'26.8"N // LON 77°06'03.2"E // ALT 786 KM
          </div>
          <div className="absolute top-12 right-10 font-mono text-[10px] text-slate-500 tracking-widest uppercase">
            ORBIT PASS: S2A_OPER_MSI_L2A_20260814
          </div>
        </div>

        {/* Hero Editorial Typography Container */}
        <div className="relative z-20 max-w-6xl mx-auto w-full flex flex-col justify-between pt-8 pb-4">
          {/* Small Top Telemetry Label */}
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/15 bg-black/50 backdrop-blur-md text-[10px] font-mono uppercase tracking-widest text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ORBITINTEL // EARTH OBSERVATION INTELLIGENCE</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
              SIH 2026 // PS 26227
            </span>
          </div>

          {/* Asymmetric Editorial Campaign Headline */}
          <div className="space-y-4 max-w-4xl">
            <h1 className="font-heading font-extrabold tracking-tightest leading-[0.94] text-4xl sm:text-7xl md:text-8xl text-white">
              SEE WHAT<br />
              <span className="text-emerald-400">CHANGED.</span>
            </h1>

            <h1 className="font-heading font-extrabold tracking-tightest leading-[0.94] text-4xl sm:text-7xl md:text-8xl text-white">
              SEARCH WHAT<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-slate-200 via-slate-400 to-slate-500">
                MATTERS.
              </span>
            </h1>
          </div>

          {/* Supporting Statement & CTAs */}
          <div className="mt-8 pt-6 border-t border-white/[0.1] flex flex-col md:flex-row md:items-end justify-between gap-6">
            <p className="max-w-md text-sm sm:text-base text-slate-300 font-sans leading-relaxed">
              Turn multi-sensor Earth observation imagery into searchable, spatio-temporal intelligence.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <a
                href="#story-section-01"
                className="px-6 py-3 rounded border border-white/25 bg-black/40 backdrop-blur-md hover:bg-white/10 hover:border-white/50 text-white font-mono text-xs uppercase tracking-widest transition-all"
              >
                EXPLORE THE PLATFORM &rarr;
              </a>

              <Link
                to="/dashboard"
                className="px-6 py-3 rounded border border-emerald-400 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-widest transition-all shadow-[0_0_30px_rgba(16,185,129,0.35)]"
              >
                LAUNCH ANALYST CONSOLE &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 01 // SEARCH EARTH BY MEANING
      ========================================================================= */}
      <section id="story-section-01" className="relative py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/[0.08]">
        <div className="space-y-12">
          {/* Header */}
          <div className="max-w-3xl">
            <span className="text-[11px] font-mono text-emerald-400 uppercase tracking-widest block mb-2">
              SECTION 01 // MULTIMODAL SEMANTIC RETRIEVAL
            </span>
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight">
              SEARCH EARTH BY MEANING.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 font-sans mt-3 leading-relaxed">
              Natural language text prompts are projected into joint vision-language embedding space (RemoteCLIP 512-dim),
              matching high-resolution satellite tiles by semantic content rather than rigid geographic keywords.
            </p>
          </div>

          {/* Interactive Semantic Transformation Composition */}
          <div className="relative rounded-2xl overflow-hidden border border-white/[0.12] bg-[#070a10] shadow-2xl">
            {/* Background Satellite Scene: River Delta & Infrastructure */}
            <div className="relative h-[480px] sm:h-[540px] w-full overflow-hidden">
              <img
                src="/assets/multispectral_scene.jpg"
                alt="Multispectral River and Construction Delta"
                className="w-full h-full object-cover object-center scale-100 hover:scale-105 transition-transform duration-1000"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#04060a] via-black/40 to-transparent" />

              {/* Geographic Marker Overlays on Image */}
              <div className="absolute top-1/3 left-1/2 -translate-x-1/2 flex flex-col items-center group cursor-pointer">
                <div className="relative flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full border border-emerald-400 bg-emerald-400/20 animate-ping absolute" />
                  <div className="w-3.5 h-3.5 rounded-full bg-emerald-400 border border-black shadow-lg" />
                </div>
                <div className="mt-2 px-3 py-1 rounded bg-black/90 border border-emerald-500/50 text-[10px] font-mono text-emerald-300 backdrop-blur-md">
                  TARGET SITE // CONSTRUCTION & RIVER CORRIDOR (94.8% MATCH)
                </div>
              </div>

              {/* Top Search Overlay */}
              <div className="absolute top-6 left-6 right-6 max-w-2xl">
                <div className="p-4 rounded-xl border border-white/20 bg-black/80 backdrop-blur-md shadow-2xl">
                  <span className="text-[9px] font-mono uppercase text-slate-400 block mb-1">
                    ANALYST PROMPT INPUT:
                  </span>
                  <div className="flex items-center gap-2 text-base sm:text-xl font-mono text-white">
                    <span className="text-emerald-400">&gt;</span>
                    <span>"{typedQuery}"</span>
                    <span className="w-2 h-4 bg-emerald-400 animate-pulse" />
                  </div>
                </div>
              </div>

              {/* Bottom Pipeline Transformation */}
              <div className="absolute bottom-6 left-6 right-6">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl border border-white/15 bg-black/85 backdrop-blur-md font-mono text-xs">
                  <div>
                    <span className="text-[9px] uppercase text-slate-400 block">STEP 01</span>
                    <span className="text-white font-bold">QUERY VECTOR</span>
                    <p className="text-[10px] text-slate-400 mt-0.5">512-dim Normalized Vector</p>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase text-slate-400 block">STEP 02</span>
                    <span className="text-emerald-400 font-bold">SEMANTIC UNDERSTANDING</span>
                    <p className="text-[10px] text-slate-400 mt-0.5">Cosine Similarity &gt; 0.94</p>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase text-slate-400 block">STEP 03</span>
                    <span className="text-cyan-400 font-bold">SPATIAL LOCALIZATION</span>
                    <p className="text-[10px] text-slate-400 mt-0.5">13.3408° N, 77.1009° E</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 02 // ONE EARTH. MANY SENSORS.
      ========================================================================= */}
      <section className="relative py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/[0.08]">
        <div className="space-y-12">
          <div className="max-w-3xl">
            <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest block mb-2">
              SECTION 02 // SENSOR SYNTHESIS
            </span>
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight">
              ONE EARTH.<br />MANY SENSORS.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 font-sans mt-3 leading-relaxed">
              No single sensor tells the whole story. OrbitIntel synchronizes multispectral optics with all-weather radar
              and multi-decade archives to construct an unblinking timeline of surface evolution.
            </p>
          </div>

          {/* Sensor Selector & Scientific Showcase */}
          <div className="space-y-6">
            {/* Interactive Layer Pills */}
            <div className="flex flex-wrap items-center gap-3">
              {[
                { key: 'sentinel1', label: 'SENTINEL-1 SAR', desc: 'All-Weather C-Band Radar' },
                { key: 'sentinel2', label: 'SENTINEL-2 MSI', desc: '10m Multispectral Optical' },
                { key: 'landsat', label: 'LANDSAT 8/9', desc: '50-Year Longitudinal Archive' },
                { key: 'bhuvan', label: 'ISRO BHUVAN', desc: 'National Geoportal Cadastral' },
              ].map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setActiveSensor(s.key as any)}
                  className={`px-4 py-2 rounded text-xs font-mono uppercase tracking-wider transition-all border ${
                    activeSensor === s.key
                      ? 'border-cyan-400 bg-cyan-500/15 text-cyan-300 font-bold'
                      : 'border-white/10 text-slate-400 hover:text-white hover:border-white/25'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Display Canvas for Active Sensor */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center rounded-2xl border border-white/[0.1] bg-[#070a10] p-6 lg:p-8">
              <div className="lg:col-span-7 rounded-xl overflow-hidden border border-white/[0.1] h-[380px] bg-black">
                {activeSensor === 'sentinel1' ? (
                  <img
                    src="/assets/sar_radar_view.jpg"
                    alt="Sentinel-1 SAR Radar View"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src="/assets/multispectral_scene.jpg"
                    alt="Multispectral Optical View"
                    className="w-full h-full object-cover"
                  />
                )}
              </div>

              <div className="lg:col-span-5 space-y-5">
                {activeSensor === 'sentinel1' && (
                  <>
                    <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                      SENSOR PROFILE // ESA C-BAND SAR
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-heading font-extrabold text-white">
                      SENTINEL-1 SYNTHETIC APERTURE RADAR
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 font-sans leading-relaxed">
                      Penetrates heavy monsoons, tropical cloud covers, and nighttime conditions. Dark specular returns reveal
                      floodwaters; bright radar backscatter exposes newly erected metal structures and industrial machinery.
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.08] text-xs font-mono">
                      <div>
                        <span className="text-slate-500 block">BAND:</span>
                        <span className="text-white font-semibold">C-Band (5.405 GHz)</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">POLARIZATION:</span>
                        <span className="text-white font-semibold">VV + VH Dual</span>
                      </div>
                    </div>
                  </>
                )}

                {activeSensor === 'sentinel2' && (
                  <>
                    <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest">
                      SENSOR PROFILE // ESA MULTISPECTRAL
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-heading font-extrabold text-white">
                      SENTINEL-2 MULTISPECTRAL INSTRUMENT
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 font-sans leading-relaxed">
                      13 discrete spectral channels spanning Visible, Near-Infrared (NIR), and Short-Wave Infrared (SWIR).
                      Delivers 10-meter ground sample distance for computing NDVI, NDWI, and built-up index anomalies.
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.08] text-xs font-mono">
                      <div>
                        <span className="text-slate-500 block">RESOLUTION:</span>
                        <span className="text-white font-semibold">10m GSD (B2, B3, B4, B8)</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">REVISIT:</span>
                        <span className="text-white font-semibold">5 Days Constellation</span>
                      </div>
                    </div>
                  </>
                )}

                {activeSensor === 'landsat' && (
                  <>
                    <div className="text-[10px] font-mono text-amber-400 uppercase tracking-widest">
                      SENSOR PROFILE // USGS/NASA OLI-2 & TIRS-2
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-heading font-extrabold text-white">
                      LANDSAT 8 & 9 ARCHIVE
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 font-sans leading-relaxed">
                      Provides longitudinal ground truth dating back across 50 years of observation. Critical for validating
                      baseline land use before modern urbanization, solar farm installations, or deforestation began.
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.08] text-xs font-mono">
                      <div>
                        <span className="text-slate-500 block">ARCHIVE:</span>
                        <span className="text-white font-semibold">1972 &rarr; Present</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">CALIBRATION:</span>
                        <span className="text-white font-semibold">Collection 2 Level-2</span>
                      </div>
                    </div>
                  </>
                )}

                {activeSensor === 'bhuvan' && (
                  <>
                    <div className="text-[10px] font-mono text-violet-400 uppercase tracking-widest">
                      SENSOR PROFILE // ISRO NATIONAL GEOPORTAL
                    </div>
                    <h3 className="text-2xl sm:text-3xl font-heading font-extrabold text-white">
                      ISRO BHUVAN OPEN DATA
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 font-sans leading-relaxed">
                      Indian Space Research Organisation national coverage offering cadastral-level parcel records,
                      LULC 1:50K cartographic classifications, and regional administrative boundary shapefiles.
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/[0.08] text-xs font-mono">
                      <div>
                        <span className="text-slate-500 block">TERRITORY:</span>
                        <span className="text-white font-semibold">Indian Subcontinent</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">LAYERS:</span>
                        <span className="text-white font-semibold">Cadastral & LULC</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 03 // SEE WHAT CHANGED (BEFORE / AFTER COMPARISON)
      ========================================================================= */}
      <section className="relative py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/[0.08]">
        <div className="space-y-12">
          <div className="max-w-3xl">
            <span className="text-[11px] font-mono text-amber-400 uppercase tracking-widest block mb-2">
              SECTION 03 // BI-TEMPORAL CHANGE DETECTION
            </span>
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight">
              SEE WHAT CHANGED.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 font-sans mt-3 leading-relaxed">
              Automated multi-temporal scene subtraction paired with false-alarm suppression filters. The slider below
              demonstrates 18.4 hectares of solar and industrial expansion in Karnataka detected with 87% confidence.
            </p>
          </div>

          {/* Full-Width Cinematic Before/After Viewport */}
          <div className="rounded-2xl border border-white/[0.12] bg-[#070a10] p-6 lg:p-8 backdrop-blur-md shadow-2xl space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block">TARGET AOI</span>
                <h3 className="text-lg sm:text-xl font-heading font-bold text-white">
                  Tumakuru Industrial & Solar Corridor, Karnataka
                </h3>
                <span className="text-xs font-mono text-slate-400">13.3408° N, 77.1009° E</span>
              </div>

              <div className="flex items-center gap-3">
                <div className="px-3 py-1.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300 font-mono text-xs font-bold">
                  87% CONFIDENCE
                </div>
                <div className="px-3 py-1.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 font-mono text-xs font-bold">
                  TEMPORAL CHANGE DETECTED
                </div>
              </div>
            </div>

            {/* Before / After Slider Component */}
            <BeforeAfterSlider
              beforeImage="/data/demo/imagery/tumakuru_t1.png"
              afterImage="/data/demo/imagery/tumakuru_t2.png"
              beforeDate="12 JUN 2024"
              afterDate="18 JUN 2026"
              confidence={0.87}
              changeType="Industrial Shed Construction & Photovoltaic Array Expansion"
              affectedArea="18.4 hectares"
              height="520px"
            />

            {/* Quick Action Verification Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-white/[0.08]">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400 uppercase">Analyst Verification:</span>
                <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${
                  demoStatus === 'CONFIRMED' ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' :
                  demoStatus === 'REJECTED' ? 'bg-rose-500/15 border-rose-500/40 text-rose-300' :
                  'bg-white/5 border-white/10 text-slate-300'
                }`}>
                  {demoStatus}
                </span>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleConfirm}
                  className="px-4 py-2 rounded border border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 font-mono text-xs uppercase transition-all"
                >
                  Confirm Event
                </button>
                <button
                  type="button"
                  onClick={handleReject}
                  className="px-4 py-2 rounded border border-rose-500/50 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-mono text-xs uppercase transition-all"
                >
                  Reject (False Alarm)
                </button>
                <Link
                  to="/analysis/analysis_tumakuru_01"
                  className="px-4 py-2 rounded border border-white/20 hover:bg-white/10 text-white font-mono text-xs uppercase transition-all"
                >
                  Full Analysis Page &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 04 // FROM IMAGE TO INTELLIGENCE PIPELINE
      ========================================================================= */}
      <section className="relative py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/[0.08]">
        <div className="space-y-12">
          <div className="max-w-3xl">
            <span className="text-[11px] font-mono text-emerald-400 uppercase tracking-widest block mb-2">
              SECTION 04 // OPERATIONAL WORKFLOW
            </span>
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight">
              FROM IMAGE TO INTELLIGENCE.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 font-sans mt-3 leading-relaxed">
              Every stage of the OrbitIntel pipeline is modular and auditable, transforming raw multispectral downlinks
              into verified geospatial truth.
            </p>
          </div>

          {/* Visual Step Pipeline (No boring cards, styled as connected telemetry nodes) */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 pt-4">
            {[
              { num: '01', title: 'EARTH', desc: 'Raw Sentinel / Landsat Downlink', tag: 'INGESTION' },
              { num: '02', title: 'SEARCH', desc: 'Natural Language / Image Query', tag: 'EMBEDDINGS' },
              { num: '03', title: 'RETRIEVE', desc: 'Qdrant Vector Index &lt; 150ms', tag: 'SIMILARITY' },
              { num: '04', title: 'COMPARE', desc: 'Bi-Temporal Co-Registration', tag: 'ALIGNMENT' },
              { num: '05', title: 'DETECT', desc: 'Deep Feature Difference Mask', tag: 'SEGMENTATION' },
              { num: '06', title: 'VERIFY', desc: 'Analyst Confirm / Reject Loop', tag: 'HUMAN OVERSIGHT' },
            ].map((st, i) => (
              <div key={st.num} className="p-4 rounded-xl border border-white/[0.08] bg-[#070a10]/80 space-y-2 relative group hover:border-emerald-500/40 transition-all">
                <span className="text-[10px] font-mono text-emerald-400 block">{st.num} // {st.tag}</span>
                <h4 className="text-lg font-heading font-extrabold text-white">{st.title}</h4>
                <p className="text-[11px] text-slate-400 font-sans leading-snug">{st.desc}</p>
                {i < 5 && (
                  <span className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-slate-600 font-mono text-xs">
                    &rarr;
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 05 // PLANETARY TO TACTICAL ZOOM TRANSITION
      ========================================================================= */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/[0.08]">
        <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-b from-emerald-500/[0.07] via-[#070a10] to-[#04060a] p-8 sm:p-16 text-center space-y-8">
          {/* Zoom Sequence Visual Telemetry */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/15 bg-white/[0.02] text-[10px] font-mono text-slate-300 uppercase">
            <span>PLANETARY DESCENT SEQUENCE</span>
          </div>

          <div className="max-w-3xl mx-auto space-y-3">
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight leading-tight">
              FROM SPACE TO SITE INTELLIGENCE.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 font-sans leading-relaxed">
              Transition seamlessly from global low-Earth orbit perspective into localized high-resolution monitoring.
              Open the interactive analyst console to inspect current alerts, search satellite scenes, and verify spatial changes.
            </p>
          </div>

          {/* Zoom Steps Indicator */}
          <div className="max-w-2xl mx-auto py-2 flex items-center justify-between text-[11px] font-mono text-slate-400 border-y border-white/[0.06]">
            <span>1. ORBIT (786 KM)</span>
            <span>&rarr;</span>
            <span>2. INDIA REGION</span>
            <span>&rarr;</span>
            <span>3. KARNATAKA</span>
            <span>&rarr;</span>
            <span className="text-emerald-400 font-bold">4. TUMAKURU (10M GSD)</span>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link
              to="/dashboard"
              className="w-full sm:w-auto px-10 py-4 rounded border border-emerald-400 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-heading font-extrabold text-xs uppercase tracking-wider transition-all shadow-[0_0_35px_rgba(16,185,129,0.35)]"
            >
              ENTER ANALYST WORKSTATION &rarr;
            </Link>

            <Link
              to="/alerts"
              className="w-full sm:w-auto px-8 py-4 rounded border border-white/20 hover:bg-white/10 text-white font-mono text-xs uppercase tracking-wider transition-all"
            >
              VIEW ACTIVE MISSION ALERTS
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
