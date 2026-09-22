import React, { useEffect, useRef } from 'react';

export const OrbitalTelemetryCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Mouse parallax tracking
    let mouseX = width / 2;
    let mouseY = height / 2;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Orbit parameters
    const orbits = [
      { radiusX: width * 0.45, radiusY: height * 0.28, angle: 0, speed: 0.0007, tilt: -0.22, color: 'rgba(16, 185, 129, 0.45)', dotColor: '#10b981', label: 'SENTINEL-2A // SSO 786KM' },
      { radiusX: width * 0.55, radiusY: height * 0.35, angle: Math.PI * 0.6, speed: 0.0005, tilt: 0.15, color: 'rgba(6, 182, 212, 0.35)', dotColor: '#06b6d4', label: 'SENTINEL-1 SAR // C-BAND' },
      { radiusX: width * 0.62, radiusY: height * 0.42, angle: Math.PI * 1.3, speed: 0.0004, tilt: -0.08, color: 'rgba(245, 158, 11, 0.25)', dotColor: '#f59e0b', label: 'LANDSAT-9 // L2' },
    ];

    // Starfield points
    const stars: { x: number; y: number; size: number; alpha: number; pulseSpeed: number }[] = [];
    for (let i = 0; i < 90; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        size: Math.random() * 1.2 + 0.3,
        alpha: Math.random() * 0.5 + 0.2,
        pulseSpeed: Math.random() * 0.02 + 0.005,
      });
    }

    let time = 0;

    const render = () => {
      time += 1;
      // Smooth mouse lerp
      mouseX += (targetMouseX - mouseX) * 0.03;
      mouseY += (targetMouseY - mouseY) * 0.03;
      const offsetX = ((mouseX - width / 2) / width) * 20;
      const offsetY = ((mouseY - height / 2) / height) * 15;

      ctx.clearRect(0, 0, width, height);

      // Draw subtle stars with gentle twinkle
      for (const star of stars) {
        const twinkle = Math.sin(time * star.pulseSpeed) * 0.25 + 0.75;
        ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha * twinkle * 0.6})`;
        ctx.beginPath();
        ctx.arc(star.x + offsetX * 0.2, star.y + offsetY * 0.2, star.size, 0, Math.PI * 2);
        ctx.fill();
      }

      // Center of Earth curvature
      const centerX = width * 0.5 + offsetX;
      const centerY = height * 0.55 + offsetY;

      // Draw orbital trajectories
      for (const orbit of orbits) {
        orbit.angle += orbit.speed;

        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(orbit.tilt);

        // Orbit ellipse path
        ctx.beginPath();
        ctx.ellipse(0, 0, orbit.radiusX, orbit.radiusY, 0, 0, Math.PI * 2);
        ctx.strokeStyle = orbit.color;
        ctx.lineWidth = 0.75;
        ctx.setLineDash([3, 12]);
        ctx.stroke();

        // Active satellite marker along path
        const satX = Math.cos(orbit.angle) * orbit.radiusX;
        const satY = Math.sin(orbit.angle) * orbit.radiusY;

        // Glow ring
        ctx.beginPath();
        ctx.arc(satX, satY, 4, 0, Math.PI * 2);
        ctx.fillStyle = orbit.dotColor;
        ctx.shadowColor = orbit.dotColor;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Telemetry tag label
        ctx.font = '9px "JetBrains Mono", monospace';
        ctx.fillStyle = 'rgba(226, 232, 240, 0.75)';
        ctx.fillText(orbit.label, satX + 8, satY - 4);

        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-10 w-full h-full"
    />
  );
};
