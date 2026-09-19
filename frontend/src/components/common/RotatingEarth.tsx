/**
 * RotatingEarth.tsx  —  Member 5 / Frontend
 *
 * Premium Canvas-2D rotating Earth visual.
 * Mounted ONCE in App.tsx as a fixed background layer.
 * pointer-events: none so it never intercepts clicks.
 *
 * Approach: Canvas 2D (no Three.js / WebGL) — lightweight, no extra deps.
 * Earth is drawn procedurally: sphere projection, continent masks, atmosphere,
 * lat/lng grid, subtle orbital arc, and a tiny scanning satellite dot.
 *
 * Rotation: ~1 revolution per 45 s (configurable via ROTATION_SPEED).
 * Animation state is preserved across route changes because the component
 * lives above <Routes> in App.tsx and never unmounts.
 */

import React, { useEffect, useRef, useCallback } from 'react';

// ─── Configuration ───────────────────────────────────────────────────────────

// One full rotation every 46 seconds (cinematic, slow and majestic)
const ROTATION_PERIOD_SECONDS = 46;

// Continent polygon coordinates [lon, lat] in degrees.
// Enhanced and curated landmass definitions including polar regions and subcontinents.
const CONTINENT_POLYGONS: [number, number][][] = [
  // Eurasia & Europe
  [
    [-10, 36], [-5, 43], [0, 48], [12, 54], [20, 58], [28, 70], [45, 68],
    [65, 69], [85, 73], [105, 75], [130, 72], [150, 68], [170, 65],
    [172, 60], [160, 52], [142, 48], [135, 36], [122, 30], [118, 22],
    [108, 18], [102, 10], [98, 16], [90, 22], [80, 26], [70, 24],
    [55, 25], [45, 38], [35, 36], [28, 41], [18, 40], [5, 43], [-6, 36],
  ],
  // Africa
  [
    [-17, 15], [-12, 28], [-5, 36], [10, 37], [25, 32], [35, 30],
    [43, 12], [51, 12], [42, -5], [38, -18], [32, -28], [26, -34],
    [18, -34], [12, -22], [8, -5], [2, 5], [-10, 6], [-17, 15],
  ],
  // North America
  [
    [-168, 65], [-155, 60], [-135, 54], [-124, 48], [-120, 34], [-110, 24],
    [-98, 18], [-87, 14], [-80, 9], [-76, 20], [-80, 30], [-74, 40],
    [-64, 45], [-55, 50], [-60, 62], [-80, 66], [-100, 72], [-130, 72],
    [-150, 68], [-168, 65],
  ],
  // South America
  [
    [-80, 9], [-74, 11], [-62, 10], [-50, -2], [-35, -6], [-36, -14],
    [-42, -23], [-50, -32], [-58, -42], [-66, -55], [-74, -48], [-72, -32],
    [-76, -18], [-80, -4], [-80, 9],
  ],
  // Australia
  [
    [114, -22], [118, -16], [128, -14], [138, -12], [146, -16], [152, -24],
    [153, -32], [146, -38], [136, -35], [124, -34], [115, -30], [114, -22],
  ],
  // Greenland
  [
    [-50, 60], [-35, 65], [-20, 72], [-22, 82], [-40, 83], [-56, 78],
    [-54, 68], [-50, 60],
  ],
  // Indian Subcontinent
  [
    [68, 24], [72, 21], [78, 12], [81, 8], [80, 14], [86, 21], [89, 22],
    [78, 28], [68, 24],
  ],
  // Japan Arch
  [
    [130, 32], [136, 35], [141, 42], [143, 44], [140, 38], [133, 33], [130, 32],
  ],
  // Scandinavia & Baltic
  [
    [5, 58], [12, 57], [18, 62], [28, 70], [22, 71], [14, 68], [8, 62], [5, 58],
  ],
  // British Isles
  [
    [-5, 50], [1, 51], [0, 56], [-4, 58], [-6, 54], [-5, 50],
  ],
  // Antarctica ice margin (southern shelf)
  [
    [-180, -74], [-130, -72], [-80, -68], [-40, -72], [0, -70],
    [45, -68], [90, -66], [135, -67], [175, -72], [180, -74],
    [180, -89], [-180, -89],
  ],
  // Arctic pack ice (northern shelf)
  [
    [-180, 80], [-120, 82], [-60, 84], [0, 83], [60, 82], [120, 81], [180, 80],
    [180, 89], [-180, 89],
  ],
];

// Major city night lights [lon, lat, intensity (0.5-1.0)]
const NIGHT_CITIES: [number, number, number][] = [
  // Asia
  [77.2, 28.6, 1.0],   // New Delhi
  [72.8, 19.1, 1.0],   // Mumbai
  [77.6, 13.0, 0.9],   // Bengaluru
  [80.3, 13.1, 0.85],  // Chennai
  [88.4, 22.6, 0.85],  // Kolkata
  [121.5, 31.2, 1.0],  // Shanghai
  [116.4, 39.9, 1.0],  // Beijing
  [139.7, 35.7, 1.0],  // Tokyo
  [126.9, 37.5, 0.95], // Seoul
  [100.5, 13.7, 0.85], // Bangkok
  [103.8, 1.3, 0.9],   // Singapore
  // Europe
  [2.3, 48.8, 1.0],    // Paris
  [-0.1, 51.5, 1.0],   // London
  [13.4, 52.5, 0.9],   // Berlin
  [37.6, 55.7, 0.95],  // Moscow
  [12.5, 41.9, 0.85],  // Rome
  [-3.7, 40.4, 0.85],  // Madrid
  // Americas
  [-74.0, 40.7, 1.0],  // New York
  [-87.6, 41.8, 0.9],  // Chicago
  [-118.2, 34.0, 1.0], // Los Angeles
  [-122.4, 37.8, 0.9], // San Francisco
  [-99.1, 19.4, 0.9],  // Mexico City
  [-46.6, -23.5, 0.9], // São Paulo
  [-43.2, -22.9, 0.85],// Rio de Janeiro
  [-58.4, -34.6, 0.8], // Buenos Aires
  // Africa & Middle East
  [31.2, 30.0, 0.9],   // Cairo
  [55.3, 25.2, 0.95],  // Dubai
  [3.4, 6.5, 0.75],    // Lagos
  [18.4, -33.9, 0.8],  // Cape Town
  // Oceania
  [151.2, -33.8, 0.9], // Sydney
  [144.9, -37.8, 0.85],// Melbourne
];

// Atmospheric cloud bands (lon, lat, rx, ry, rotation rad, opacity factor)
const CLOUD_SYSTEMS: [number, number, number, number, number, number][] = [
  // Intertropical Convergence Zone (equatorial band)
  [20, 4, 32, 12, 0.1, 0.38],
  [-40, 2, 38, 11, -0.08, 0.35],
  [-110, 6, 42, 13, 0.05, 0.36],
  [140, 2, 45, 14, -0.06, 0.40],
  [80, 5, 36, 12, 0.04, 0.38],
  // Mid-latitude storm vortexes (Northern Hemisphere)
  [-35, 48, 28, 16, -0.4, 0.42],  // North Atlantic cyclone
  [-145, 46, 32, 18, -0.35, 0.40], // North Pacific cyclone
  [160, 52, 26, 15, -0.3, 0.37],
  [45, 54, 24, 14, 0.2, 0.35],
  // Southern Ocean storm bands (furious fifties)
  [-80, -52, 45, 14, 0.25, 0.42],
  [10, -50, 42, 13, 0.2, 0.40],
  [95, -53, 46, 14, 0.22, 0.44],
  [170, -48, 38, 12, 0.18, 0.38],
  // Tropical cyclonic swirls
  [128, 18, 16, 16, 0.8, 0.48], // Typhoon formation
  [-70, 22, 15, 15, 0.7, 0.45], // Caribbean hurricane swirl
  [85, 15, 14, 14, 0.6, 0.44],  // Bay of Bengal depression
];

// ─── Projection & Coordinates ────────────────────────────────────────────────

interface EarthDrawParams {
  cx: number;
  cy: number;
  r: number;
  rotAngle: number;
  tiltX: number;
  tiltY: number;
}

function geoToCanvas(
  lon: number,
  lat: number,
  params: EarthDrawParams,
  lonOffset = 0,
): { x: number; y: number; z: number; visible: boolean } {
  const { cx, cy, r, rotAngle, tiltX, tiltY } = params;

  const lonRad = ((lon + lonOffset) * Math.PI) / 180 + rotAngle;
  const latRad = (lat * Math.PI) / 180;

  // Spherical -> Cartesian
  let X = Math.cos(latRad) * Math.cos(lonRad);
  let Y = Math.sin(latRad);
  let Z = Math.cos(latRad) * Math.sin(lonRad);

  // Parallax tilt around Y axis
  const cosX = Math.cos(tiltX);
  const sinX = Math.sin(tiltX);
  const X1 = X * cosX - Z * sinX;
  const Z1 = X * sinX + Z * cosX;
  X = X1;
  Z = Z1;

  // Parallax tilt around X axis
  const cosY = Math.cos(tiltY);
  const sinY = Math.sin(tiltY);
  const Y1 = Y * cosY - Z * sinY;
  const Z2 = Y * sinY + Z * cosY;
  Y = Y1;

  // Depth threshold: point is on visible front hemisphere
  const visible = Z2 > -0.04;

  return {
    x: cx + X * r,
    y: cy - Y * r,
    z: Z2,
    visible,
  };
}

// ─── Component ───────────────────────────────────────────────────────────────

interface RotatingEarthProps {
  scale?: number;
  opacity?: number;
  className?: string;
}

export const RotatingEarth: React.FC<RotatingEarthProps> = ({
  scale = 1.0,
  opacity = 1.0,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const rotationRef = useRef<number>(0.8);      // Start angle shows vivid oceans & continents immediately
  const lastTimeRef = useRef<number>(0);
  const mouseRef = useRef({ x: 0.5, y: 0.5 });
  const targetMouseRef = useRef({ x: 0.5, y: 0.5 });

  const draw = useCallback((
    ctx: CanvasRenderingContext2D,
    W: number,
    H: number,
  ) => {
    ctx.clearRect(0, 0, W, H);

    // Responsive positioning:
    // Desktop: Large, majestic, right-of-center behind hero text
    // Mobile/Tablet: Centered, scaled nicely with zero horizontal overflow
    const isMobile = W < 768;
    const isTablet = W >= 768 && W < 1100;

    const baseRadius = isMobile
      ? Math.min(W, H) * 0.36 * scale
      : isTablet
      ? Math.min(W, H) * 0.38 * scale
      : Math.min(W, H) * 0.40 * scale;

    const cx = isMobile ? W * 0.50 : isTablet ? W * 0.68 : W * 0.72;
    const cy = isMobile ? H * 0.44 : H * 0.48;

    // Mouse parallax (subtle orbit tilt)
    const mx = mouseRef.current.x;
    const my = mouseRef.current.y;
    const tiltX = (mx - 0.5) * 0.12;
    const tiltY = (my - 0.5) * 0.08;

    const params: EarthDrawParams = {
      cx,
      cy,
      r: baseRadius,
      rotAngle: rotationRef.current,
      tiltX,
      tiltY,
    };

    // ── 1. Broad Outer Space Ambient Scatter ─────────────────────────────────
    // Soft planetary deep-space glow that blends smoothly into dark cosmic space
    const outerSpaceGlow = ctx.createRadialGradient(
      cx, cy, baseRadius * 0.85,
      cx, cy, baseRadius * 1.75,
    );
    outerSpaceGlow.addColorStop(0, 'rgba(14, 116, 185, 0.16)');
    outerSpaceGlow.addColorStop(0.35, 'rgba(6, 182, 212, 0.08)');
    outerSpaceGlow.addColorStop(0.70, 'rgba(3, 105, 161, 0.03)');
    outerSpaceGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius * 1.75, 0, Math.PI * 2);
    ctx.fillStyle = outerSpaceGlow;
    ctx.fill();

    // ── 2. Atmospheric Exosphere Rim (Outside the sphere edge) ──────────────
    // Realistic luminous blue / cyan rim glow seen from orbit
    const atmoRim = ctx.createRadialGradient(
      cx - baseRadius * 0.12, cy - baseRadius * 0.16, baseRadius * 0.94,
      cx, cy, baseRadius * 1.20,
    );
    atmoRim.addColorStop(0, 'rgba(56, 189, 248, 0.0)');
    atmoRim.addColorStop(0.12, 'rgba(56, 189, 248, 0.42)'); // Brilliant cyan corona
    atmoRim.addColorStop(0.40, 'rgba(14, 165, 233, 0.24)'); // Radiant sky blue
    atmoRim.addColorStop(0.70, 'rgba(37, 99, 235, 0.09)');  // Deep sapphire Rayleigh scatter
    atmoRim.addColorStop(1.0, 'rgba(0, 0, 0, 0)');
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius * 1.20, 0, Math.PI * 2);
    ctx.fillStyle = atmoRim;
    ctx.fill();

    // ── 3. Sphere Base: Deep Blue Living Ocean ──────────────────────────────
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius, 0, Math.PI * 2);
    ctx.clip(); // All terrestrial elements clipped to planetary disc

    // Ocean gradient — vivid, rich, deep celestial blue (not dark murky gray)
    const oceanGrad = ctx.createRadialGradient(
      cx - baseRadius * 0.28, cy - baseRadius * 0.32, baseRadius * 0.04,
      cx, cy, baseRadius,
    );
    oceanGrad.addColorStop(0, '#1c5b96');   // Bright sunlit oceanic surface
    oceanGrad.addColorStop(0.28, '#10447a'); // Rich royal blue ocean
    oceanGrad.addColorStop(0.58, '#0a2c56'); // Deep cobalt abyssal water
    oceanGrad.addColorStop(0.85, '#051936'); // Twilight ocean
    oceanGrad.addColorStop(1.0, '#020b18');  // Night ocean
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);

    // ── 4. Precision Latitude / Longitude Telemetry Grid ─────────────────────
    ctx.globalAlpha = 0.12;
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 0.6;

    // Latitude parallels every 30°
    for (let lat = -60; lat <= 60; lat += 30) {
      ctx.beginPath();
      let first = true;
      for (let lon = -180; lon <= 180; lon += 4) {
        const pt = geoToCanvas(lon, lat, params);
        if (!pt.visible) { first = true; continue; }
        if (first) { ctx.moveTo(pt.x, pt.y); first = false; }
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
    }

    // Longitude meridians every 30°
    for (let lon = 0; lon < 360; lon += 30) {
      ctx.beginPath();
      let first = true;
      for (let lat = -80; lat <= 80; lat += 4) {
        const pt = geoToCanvas(lon, lat, params);
        if (!pt.visible) { first = true; continue; }
        if (first) { ctx.moveTo(pt.x, pt.y); first = false; }
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1.0;

    // ── 5. Continents: Natural Earth Tones & Continental Shelves ────────────
    CONTINENT_POLYGONS.forEach((polygon) => {
      // Check if polygon points to polar ice caps
      const isPolarIce = polygon.some(([_, lat]) => Math.abs(lat) >= 70);

      ctx.beginPath();
      let started = false;
      let lastVisible = false;

      polygon.forEach(([lon, lat]) => {
        const pt = geoToCanvas(lon, lat, params);
        if (pt.visible) {
          if (!started || !lastVisible) {
            ctx.moveTo(pt.x, pt.y);
            started = true;
          } else {
            ctx.lineTo(pt.x, pt.y);
          }
          lastVisible = true;
        } else {
          lastVisible = false;
        }
      });

      if (started) {
        ctx.closePath();

        if (isPolarIce) {
          // Polar glacier ice — pristine white with soft arctic blue tint
          const iceGrad = ctx.createRadialGradient(
            cx - baseRadius * 0.2, cy - baseRadius * 0.2, 0,
            cx, cy, baseRadius,
          );
          iceGrad.addColorStop(0, 'rgba(240, 249, 255, 0.90)');
          iceGrad.addColorStop(0.8, 'rgba(214, 238, 250, 0.78)');
          iceGrad.addColorStop(1, 'rgba(165, 214, 240, 0.65)');
          ctx.fillStyle = iceGrad;
          ctx.fill();
        } else {
          // Realistic continent fill — natural lush green & earth-vegetation tones
          const contGrad = ctx.createRadialGradient(
            cx - baseRadius * 0.25, cy - baseRadius * 0.3, 0,
            cx, cy, baseRadius,
          );
          contGrad.addColorStop(0, '#3f683d');   // Sunlit canopy & grasslands
          contGrad.addColorStop(0.35, '#2f522e'); // Deep temperate forests
          contGrad.addColorStop(0.70, '#223e23'); // Highland terrain
          contGrad.addColorStop(1.0, '#152917');  // Edge shadow terrain
          ctx.fillStyle = contGrad;
          ctx.fill();

          // Coastal continental shelf halo (cyan shallow water boundary)
          ctx.globalAlpha = 0.35;
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 1.0;
          ctx.stroke();

          // Inner terrain accent stroke
          ctx.globalAlpha = 0.55;
          ctx.strokeStyle = '#4e7b4a';
          ctx.lineWidth = 0.5;
          ctx.stroke();
          ctx.globalAlpha = 1.0;
        }
      }
    });

    // ── 6. Swirling Cloud Systems (Atmospheric Weather Patterns) ────────────
    // Clouds rotate at slightly offset rate to create living dynamic atmosphere
    const cloudAngleOffset = 0.05 * Math.sin(rotationRef.current * 2);

    CLOUD_SYSTEMS.forEach(([cLon, cLat, rx, ry, rot, opacityFactor]) => {
      const pt = geoToCanvas(cLon, cLat, params, cloudAngleOffset);
      if (!pt.visible || pt.z < 0.02) return;

      ctx.save();
      ctx.translate(pt.x, pt.y);
      ctx.rotate(rot);

      // Scale cloud patch proportionally to distance from limb
      const perspectiveScale = Math.max(0.3, Math.min(1.0, pt.z + 0.15));
      const rX = (rx / 100) * baseRadius * perspectiveScale;
      const rY = (ry / 100) * baseRadius * perspectiveScale;

      const cloudGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, Math.max(rX, rY));
      const baseAlpha = opacityFactor * Math.min(1.0, pt.z * 1.5);
      cloudGrad.addColorStop(0, `rgba(255, 255, 255, ${baseAlpha.toFixed(2)})`);
      cloudGrad.addColorStop(0.45, `rgba(240, 248, 255, ${(baseAlpha * 0.75).toFixed(2)})`);
      cloudGrad.addColorStop(0.85, `rgba(215, 235, 250, ${(baseAlpha * 0.30).toFixed(2)})`);
      cloudGrad.addColorStop(1, 'rgba(180, 220, 245, 0)');

      ctx.beginPath();
      ctx.ellipse(0, 0, rX, rY, 0, 0, Math.PI * 2);
      ctx.fillStyle = cloudGrad;
      ctx.fill();
      ctx.restore();
    });

    // ── 7. Night-Side City Lights (Warm Amber Civilization Clusters) ─────────
    NIGHT_CITIES.forEach(([cLon, cLat, intensity]) => {
      const pt = geoToCanvas(cLon, cLat, params);
      if (!pt.visible) return;

      // Calculate position relative to solar day/night terminator
      const lonRad = (cLon * Math.PI) / 180 + rotationRef.current;
      const latRad = (cLat * Math.PI) / 180;
      const sunFacing = Math.cos(latRad) * Math.sin(lonRad);

      // Only display lights on the dark night side
      if (sunFacing < 0.10) {
        const nightFactor = Math.min(1.0, (0.10 - sunFacing) * 4.0);
        const lightAlpha = intensity * nightFactor * Math.max(0.2, pt.z);

        // Core light
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 1.3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(254, 240, 138, ${lightAlpha.toFixed(2)})`;
        ctx.fill();

        // Warm ambient glow
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3.2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 158, 11, ${(lightAlpha * 0.35).toFixed(2)})`;
        ctx.fill();
      }
    });

    // ── 8. Planetary Day/Night Terminator (Cinematic Lighting) ───────────────
    // Natural sunlight illuminated from top-right-front, casting soft terminator shadow
    const shadowGrad = ctx.createRadialGradient(
      cx + baseRadius * 0.42, cy - baseRadius * 0.32, baseRadius * 0.1,
      cx, cy, baseRadius,
    );
    shadowGrad.addColorStop(0, 'rgba(0, 0, 0, 0)');
    shadowGrad.addColorStop(0.48, 'rgba(0, 0, 0, 0)');
    shadowGrad.addColorStop(0.72, 'rgba(4, 12, 28, 0.40)'); // Twilight atmospheric zone
    shadowGrad.addColorStop(0.88, 'rgba(2, 6, 18, 0.78)');
    shadowGrad.addColorStop(1.0, 'rgba(1, 3, 10, 0.94)');   // Deep night
    ctx.fillStyle = shadowGrad;
    ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);

    // Soft warm sunset/sunrise twilight band along the terminator line
    const twilightBand = ctx.createRadialGradient(
      cx + baseRadius * 0.42, cy - baseRadius * 0.32, baseRadius * 0.65,
      cx, cy, baseRadius * 0.95,
    );
    twilightBand.addColorStop(0, 'rgba(249, 115, 22, 0)');
    twilightBand.addColorStop(0.5, 'rgba(249, 115, 22, 0.07)'); // Subtle orange glow on twilight
    twilightBand.addColorStop(0.8, 'rgba(56, 189, 248, 0.05)');
    twilightBand.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = twilightBand;
    ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);

    // ── 9. Specular Ocean Sun Glint (Sunlight reflection from orbit) ─────────
    const glintGrad = ctx.createRadialGradient(
      cx + baseRadius * 0.35, cy - baseRadius * 0.32, 0,
      cx + baseRadius * 0.35, cy - baseRadius * 0.32, baseRadius * 0.45,
    );
    glintGrad.addColorStop(0, 'rgba(255, 255, 255, 0.22)');
    glintGrad.addColorStop(0.35, 'rgba(186, 230, 253, 0.08)');
    glintGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = glintGrad;
    ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);

    // ── 10. Inner Atmospheric Rayleigh Limb Glow (Fresnel rim) ───────────────
    // Critical for photorealistic Earth from space look: bright cyan edge inside sphere
    const innerLimbGrad = ctx.createRadialGradient(
      cx, cy, baseRadius * 0.72,
      cx, cy, baseRadius,
    );
    innerLimbGrad.addColorStop(0, 'rgba(56, 189, 248, 0)');
    innerLimbGrad.addColorStop(0.65, 'rgba(56, 189, 248, 0.12)');
    innerLimbGrad.addColorStop(0.88, 'rgba(125, 211, 252, 0.35)');
    innerLimbGrad.addColorStop(1.0, 'rgba(186, 230, 253, 0.55)');
    ctx.fillStyle = innerLimbGrad;
    ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);

    ctx.restore(); // End sphere clip

    // ── 11. Atmospheric Edge Razor Rim (Super crisp boundary halo) ───────────
    const edgeHalo = ctx.createRadialGradient(
      cx, cy, baseRadius * 0.97,
      cx, cy, baseRadius * 1.05,
    );
    edgeHalo.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
    edgeHalo.addColorStop(0.45, 'rgba(14, 165, 233, 0.28)');
    edgeHalo.addColorStop(1.0, 'rgba(0, 0, 0, 0)');
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius * 1.05, 0, Math.PI * 2);
    ctx.fillStyle = edgeHalo;
    ctx.fill();

    // ── 12. Orbital Telemetry Arc & Observation Satellite ───────────────────
    const arcSpeedAngle = rotationRef.current * 0.5;
    const arcRadius = baseRadius * 1.25;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(arcSpeedAngle);

    // Satellite orbital trajectory
    ctx.beginPath();
    ctx.ellipse(0, 0, arcRadius, arcRadius * 0.36, 0, -Math.PI * 0.20, Math.PI * 0.85);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
    ctx.lineWidth = 1.0;
    ctx.setLineDash([4, 8]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Observation Satellite icon & laser telemetry ping
    const satPhase = (rotationRef.current * 0.7) % (Math.PI * 2);
    const satX = arcRadius * Math.cos(satPhase * 0.6);
    const satY = arcRadius * 0.36 * Math.sin(satPhase * 0.6);

    // Satellite body
    ctx.beginPath();
    ctx.arc(satX, satY, 2.8, 0, Math.PI * 2);
    ctx.fillStyle = '#38bdf8';
    ctx.shadowColor = '#0284c7';
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Subtle sensor pulse rings
    const pulseRadius = 5 + (Date.now() % 2000) / 100;
    const pulseAlpha = Math.max(0, 1 - pulseRadius / 25);
    ctx.beginPath();
    ctx.arc(satX, satY, pulseRadius, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(56, 189, 248, ${(pulseAlpha * 0.4).toFixed(2)})`;
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.restore();

    // ── 13. Earth Observation Sweep Radar Scanner Arc ───────────────────────
    const scanAngle = (Date.now() / 4200) % (Math.PI * 2);
    const scanR = baseRadius * 1.14;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(scanAngle);
    const scanGrad = ctx.createLinearGradient(-scanR, 0, scanR, 0);
    scanGrad.addColorStop(0, 'rgba(6, 182, 212, 0)');
    scanGrad.addColorStop(0.5, 'rgba(56, 189, 248, 0.18)');
    scanGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
    ctx.beginPath();
    ctx.arc(0, 0, scanR, -0.18, 0.18);
    ctx.strokeStyle = scanGrad;
    ctx.lineWidth = 2.2;
    ctx.stroke();
    ctx.restore();
  }, [scale]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;

    const handleResize = () => {
      if (!canvas) return;
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Mouse tracking for subtle parallax
    const handleMouseMove = (e: MouseEvent) => {
      targetMouseRef.current = {
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      };
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Frame-rate independent continuous animation loop.
    // Starts immediately on mount — zero delay, no scroll required.
    const radPerSecond = (2 * Math.PI) / ROTATION_PERIOD_SECONDS;

    const animate = (timestamp: number) => {
      if (!lastTimeRef.current) {
        lastTimeRef.current = timestamp;
      }
      const deltaSeconds = Math.min((timestamp - lastTimeRef.current) / 1000, 0.1);
      lastTimeRef.current = timestamp;

      // Mouse lerp
      mouseRef.current.x += (targetMouseRef.current.x - mouseRef.current.x) * 0.03;
      mouseRef.current.y += (targetMouseRef.current.y - mouseRef.current.y) * 0.03;

      // Continuous frame-rate independent rotation
      rotationRef.current += radPerSecond * deltaSeconds;
      if (rotationRef.current > Math.PI * 2) {
        rotationRef.current -= Math.PI * 2;
      }

      draw(ctx, W, H);
      animRef.current = requestAnimationFrame(animate);
    };

    // Immediately trigger first frame and loop
    animRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Mount once in App.tsx, never unmounts, preserves continuous rotation

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`fixed inset-0 pointer-events-none select-none ${className}`}
      style={{
        zIndex: 0,
        opacity,
        display: 'block',
      }}
    />
  );
};

export default RotatingEarth;

