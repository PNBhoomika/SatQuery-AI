import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import { Layers, MapPin, ZoomIn, ZoomOut, Crosshair, Sparkles, Compass, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useIntelligence } from '../../context/IntelligenceContext';
import { SearchResult, Alert, Cluster } from '../../types/api';

export const MapView: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const clustersLayerRef = useRef<L.LayerGroup | null>(null);
  const polygonsLayerRef = useRef<L.LayerGroup | null>(null);
  const baseTileLayerRef = useRef<L.TileLayer | null>(null);

  const [baseMap, setBaseMap] = useState<'satellite' | 'dark'>('satellite');
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number }>({ lat: 13.3408, lng: 77.1009 });
  const [currentZoom, setCurrentZoom] = useState<number>(12);
  const navigate = useNavigate();

  const {
    searchResults,
    selectedResult,
    setSelectedResult,
    alerts,
    selectedAlert,
    setSelectedAlert,
    clusters,
    selectedCluster,
    setSelectedCluster,
    mapCenter,
    mapZoom,
  } = useIntelligence();

  // Base Map Tile URLs - Cartographic and high-resolution Earth Observation basemaps
  const TILE_URLS = {
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  };

  const ATTRIBUTIONS = {
    satellite: '&copy; Esri &mdash; Earthstar Geographics, Sentinel-2 / USGS',
    dark: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
  };

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: mapCenter,
      zoom: mapZoom,
      zoomControl: false,
      attributionControl: false,
    });

    const tileLayer = L.tileLayer(TILE_URLS[baseMap], {
      maxZoom: 18,
      attribution: ATTRIBUTIONS[baseMap],
    }).addTo(map);

    baseTileLayerRef.current = tileLayer;

    // Create marker layers
    const clustersGroup = L.layerGroup().addTo(map);
    const polygonsGroup = L.layerGroup().addTo(map);
    const markersGroup = L.layerGroup().addTo(map);

    clustersLayerRef.current = clustersGroup;
    polygonsLayerRef.current = polygonsGroup;
    markersLayerRef.current = markersGroup;
    mapInstanceRef.current = map;

    // Track cursor coordinates
    map.on('mousemove', (e: L.LeafletMouseEvent) => {
      setCursorCoords({ lat: e.latlng.lat, lng: e.latlng.lng });
    });

    map.on('zoomend', () => {
      setCurrentZoom(map.getZoom());
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Base Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !baseTileLayerRef.current) return;
    baseTileLayerRef.current.setUrl(TILE_URLS[baseMap]);
  }, [baseMap]);

  // Center/Zoom map when context coordinates change
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setView(mapCenter, mapZoom, { animate: true });
  }, [mapCenter, mapZoom]);

  // Render Markers, Change Polygons and HDBSCAN Clusters
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current || !clustersLayerRef.current || !polygonsLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    clustersLayerRef.current.clearLayers();
    polygonsLayerRef.current.clearLayers();

    // 1. Render Change Detection Polygon (Bi-Temporal Ground-Truth Area in Tumakuru)
    const changeCoords: [number, number][] = [
      [13.3490, 77.0940],
      [13.3520, 77.1070],
      [13.3420, 77.1130],
      [13.3360, 77.1020],
      [13.3390, 77.0930],
    ];

    const changePolygon = L.polygon(changeCoords, {
      color: '#f43f5e',
      weight: 1.5,
      dashArray: '5, 5',
      fillColor: '#f43f5e',
      fillOpacity: 0.16,
    });

    changePolygon.bindTooltip(
      `<div style="font-family: monospace; font-size: 10px; color: #f43f5e; padding: 2px 4px; background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(244, 63, 94, 0.4); border-radius: 4px;">
        <span style="font-weight: 700;">CHANGE EVENT // ALT-2026-024</span><br/>
        Area: 18.4 HA &bull; Conf: 87% &bull; Type: Urban Expansion
      </div>`,
      { sticky: true }
    );

    changePolygon.on('click', () => {
      navigate('/analysis/analysis_tumakuru_01');
    });

    polygonsLayerRef.current.addLayer(changePolygon);

    // 2. Render HDBSCAN Cluster Bounding Regions
    clusters.forEach((cluster) => {
      if (cluster.bounds) {
        const isClusterSelected = selectedCluster?.cluster_id === cluster.cluster_id;
        const rect = L.rectangle(cluster.bounds, {
          color: isClusterSelected ? '#10b981' : '#06b6d4',
          weight: isClusterSelected ? 2 : 1.2,
          dashArray: '4, 4',
          fillColor: isClusterSelected ? '#10b981' : '#06b6d4',
          fillOpacity: isClusterSelected ? 0.18 : 0.06,
        });

        rect.on('click', () => {
          setSelectedCluster(cluster);
          mapInstanceRef.current?.fitBounds(cluster.bounds, { padding: [30, 30] });
        });

        rect.bindTooltip(
          `<div style="font-family: monospace; font-size: 10px; background: rgba(15, 23, 42, 0.9); color: #e2e8f0; padding: 3px 6px; border: 1px solid rgba(6, 182, 212, 0.4); border-radius: 4px;">
            <strong style="color: #38bdf8;">${cluster.cluster_name}</strong><br/>
            ${cluster.member_count} detections &bull; ${(cluster.confidence * 100).toFixed(0)}% conf
          </div>`,
          { sticky: true }
        );

        clustersLayerRef.current?.addLayer(rect);
      }
    });

    // 3. Render Search Results Markers
    searchResults.forEach((res, idx) => {
      const isSelected = selectedResult?.id === res.id;
      const markerColor = isSelected ? '#10b981' : '#06b6d4';

      const customIcon = L.divIcon({
        className: 'custom-sat-marker',
        html: `
          <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; inset: 0; border-radius: 9999px; background: ${
              isSelected ? 'rgba(16, 185, 129, 0.4)' : 'rgba(6, 182, 212, 0.25)'
            }; animation: ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="position: relative; width: 18px; height: 18px; border-radius: 9999px; background: ${markerColor}; border: 2px solid #ffffff; box-shadow: 0 0 14px ${
          isSelected ? 'rgba(16, 185, 129, 0.9)' : 'rgba(6, 182, 212, 0.8)'
        }; display: flex; align-items: center; justify-content: center; color: #000; font-family: monospace; font-size: 9px; font-weight: 700;">
              ${idx + 1}
            </div>
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });

      const marker = L.marker([res.latitude, res.longitude], { icon: customIcon });

      const popupContent = document.createElement('div');
      popupContent.innerHTML = `
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 210px; background: #070a10; color: #f8fafc; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 4px;">
            <span style="font-family: monospace; font-size: 9px; color: #06b6d4; font-weight: 700; text-transform: uppercase;">
              TARGET #${String(idx + 1).padStart(2, '0')} // ${res.sensor || 'SENTINEL-2'}
            </span>
            <span style="font-family: monospace; font-size: 9px; background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 1px 5px; border-radius: 2px; font-weight: 700;">
              ${res.relevanceScore}% MATCH
            </span>
          </div>
          <h4 style="font-size: 11px; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">
            ${res.title}
          </h4>
          <div style="font-family: monospace; font-size: 9px; color: #94a3b8; margin-bottom: 8px; display: flex; flex-direction: column; gap: 2px;">
            <div><span>Coord:</span> <strong style="color: #cbd5e1;">${res.latitude.toFixed(4)}°N, ${res.longitude.toFixed(4)}°E</strong></div>
            <div><span>Confidence:</span> <strong style="color: #10b981;">${(res.confidence * 100).toFixed(0)}%</strong></div>
          </div>
          <button id="btn-popup-analyze-${res.id}" style="width: 100%; background: #10b981; color: #022c22; font-family: monospace; font-size: 9px; font-weight: 800; padding: 6px 8px; border-radius: 4px; border: none; cursor: pointer; text-transform: uppercase; letter-spacing: 0.05em;">
            OPEN DEEP ANALYSIS &rarr;
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on('click', () => {
        setSelectedResult(res);
        setTimeout(() => {
          const btn = document.getElementById(`btn-popup-analyze-${res.id}`);
          if (btn) {
            btn.onclick = () => navigate('/analysis/analysis_tumakuru_01');
          }
        }, 50);
      });

      markersLayerRef.current?.addLayer(marker);
    });

    // 4. Render Active Alerts (Amber/Red Priority Markers)
    alerts.forEach((alt) => {
      const isPending = alt.status === 'PENDING REVIEW';
      const isConfirmed = alt.status === 'CONFIRMED';
      const alertColor = isConfirmed ? '#10b981' : isPending ? '#f43f5e' : '#64748b';

      const alertIcon = L.divIcon({
        className: 'custom-alert-marker',
        html: `
          <div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;">
            ${isPending ? '<div style="position: absolute; inset: 0; border-radius: 9999px; background: rgba(244, 63, 94, 0.4); animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>' : ''}
            <div style="position: relative; width: 14px; height: 14px; border-radius: 2px; background: ${alertColor}; transform: rotate(45deg); border: 1.5px solid #ffffff; box-shadow: 0 0 10px ${alertColor};"></div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const alertMarker = L.marker([alt.latitude, alt.longitude], { icon: alertIcon });

      alertMarker.bindTooltip(
        `<div style="font-family: monospace; font-size: 9px; background: rgba(15, 23, 42, 0.95); color: #f8fafc; padding: 3px 6px; border: 1px solid ${alertColor}; border-radius: 3px;">
          <span style="color: ${alertColor}; font-weight: 700;">ALERT ${alt.id}</span> &bull; ${alt.type}<br/>
          Conf: ${(alt.confidence * 100).toFixed(0)}% &bull; ${alt.status}
        </div>`,
        { sticky: true }
      );

      alertMarker.on('click', () => {
        setSelectedAlert(alt);
        navigate('/analysis/analysis_tumakuru_01');
      });

      markersLayerRef.current?.addLayer(alertMarker);
    });
  }, [searchResults, selectedResult, clusters, selectedCluster, alerts]);

  const resetView = () => {
    mapInstanceRef.current?.setView([13.3408, 77.1009], 12);
  };

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.08] shadow-2xl bg-[#090b10]">
      {/* Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Top Left: North Indicator & Telemetry Header */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-2">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-white/10 bg-[#070a10]/85 backdrop-blur-md shadow-xl text-white">
          <div className="flex flex-col items-center justify-center w-6 h-6 rounded border border-white/20 bg-white/[0.04]">
            <span className="text-[8px] font-mono font-black text-rose-400 leading-none">▲</span>
            <span className="text-[8px] font-mono font-bold text-slate-300 leading-none">N</span>
          </div>
          <div className="flex flex-col text-[9px] font-mono leading-tight">
            <span className="text-slate-400 font-semibold tracking-wider">AOI CENTROID</span>
            <span className="text-emerald-400 font-bold">13.3408° N, 77.1009° E</span>
          </div>
        </div>
      </div>

      {/* Top Right: Floating Basemap Switcher & View Controls */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-2">
        <div className="flex rounded-lg border border-white/10 bg-[#070a10]/85 backdrop-blur-md p-0.5 shadow-xl">
          <button
            type="button"
            onClick={() => setBaseMap('satellite')}
            className={`px-2 py-1 rounded text-[10px] font-mono font-medium transition-all ${
              baseMap === 'satellite'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sentinel / Esri
          </button>
          <button
            type="button"
            onClick={() => setBaseMap('dark')}
            className={`px-2 py-1 rounded text-[10px] font-mono font-medium transition-all ${
              baseMap === 'dark'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Carto Dark
          </button>
        </div>

        {/* Zoom & Center Tools */}
        <div className="flex flex-col rounded-lg border border-white/10 bg-[#070a10]/85 backdrop-blur-md p-0.5 shadow-xl self-end">
          <button
            type="button"
            onClick={() => mapInstanceRef.current?.zoomIn()}
            className="p-1.5 rounded hover:bg-white/[0.08] text-slate-300 hover:text-emerald-400 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => mapInstanceRef.current?.zoomOut()}
            className="p-1.5 rounded hover:bg-white/[0.08] text-slate-300 hover:text-emerald-400 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={resetView}
            className="p-1.5 rounded hover:bg-white/[0.08] text-slate-300 hover:text-emerald-400 transition-colors border-t border-white/[0.06]"
            title="Reset to AOI Centroid"
          >
            <Crosshair className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Bottom Center: Live Coordinates & Telemetry HUD */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-[1000] hidden sm:flex items-center gap-3 px-3 py-1 rounded-full border border-white/10 bg-[#070a10]/90 backdrop-blur-md text-[9px] font-mono text-slate-300 shadow-2xl">
        <span className="text-slate-400">CURSOR:</span>
        <span className="text-white font-bold">{cursorCoords.lat.toFixed(4)}° N, {cursorCoords.lng.toFixed(4)}° E</span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400">ZOOM:</span>
        <span className="text-emerald-400 font-bold">{currentZoom}</span>
        <span className="text-slate-600">|</span>
        <span className="text-cyan-400 font-bold">10M RESOLUTION</span>
      </div>

      {/* Bottom Left: Semantic Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] flex flex-wrap items-center gap-2.5 px-3 py-1.5 rounded-lg border border-white/10 bg-[#070a10]/90 backdrop-blur-md text-[10px] font-mono text-slate-300 shadow-xl">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="text-slate-300">Verified</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
          <span className="text-slate-300">Sensor Target</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-sm bg-rose-500 transform rotate-45"></span>
          <span className="text-slate-300">Change Event</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-2 rounded border border-rose-500/60 bg-rose-500/20"></span>
          <span className="text-slate-300">Δ 18.4 HA Polygon</span>
        </div>
      </div>
    </div>
  );
};

