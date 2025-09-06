// Path: frontend/src/components/EnergyPlot.tsx

import React, { useRef, useEffect } from 'react';

interface EnergyPlotProps {
  data: Array<{ iteration: number; energy: number }>;
  xLabel?: string;
  isDissociation?: boolean;
}

const EnergyPlot: React.FC<EnergyPlotProps> = ({ data, xLabel = "Iteration", isDissociation = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const { width, height } = rect;

    const padding = { top: 20, right: 20, bottom: 50, left: 70 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    const xValues = data.map(d => d.iteration);
    const yValues = data.map(d => d.energy);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yBuffer = Math.abs(Math.max(...yValues) - Math.min(...yValues)) * 0.1;
    const yMin = Math.min(...yValues) - yBuffer;
    const yMax = Math.max(...yValues) + yBuffer;
    
    const xRange = xMax - xMin || 1;
    const yRange = yMax - yMin || 1;

    const xScale = (x: number) => padding.left + ((x - xMin) / xRange) * plotWidth;
    const yScale = (y: number) => padding.top + ((yMax - y) / yRange) * plotHeight;

    // Draw axes
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Draw data line
    if (data.length > 1) {
      ctx.strokeStyle = '#4f46e5';
      ctx.lineWidth = 2;
      ctx.beginPath();
      data.forEach((point, i) => {
        const x = xScale(point.iteration);
        const y = yScale(point.energy);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    // Draw data points
    ctx.fillStyle = '#4f46e5';
    data.forEach(point => {
        const x = xScale(point.iteration);
        const y = yScale(point.energy);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
    });

    // Draw labels and ticks
    ctx.fillStyle = '#334155';
    ctx.font = '12px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(xLabel, padding.left + plotWidth / 2, height - 15);

    ctx.textAlign = 'right';
    const numYTicks = 5;
    for (let i = 0; i <= numYTicks; i++) {
        const value = yMin + (i / numYTicks) * yRange;
        const y = yScale(value);
        ctx.fillText(value.toFixed(4), padding.left - 10, y + 4);
    }
    
    ctx.textAlign = 'center';
    const numXTicks = 5;
    for (let i = 0; i <= numXTicks; i++) {
        const value = xMin + (i / numXTicks) * xRange;
        const x = xScale(value);
        ctx.fillText(isDissociation ? (value / 100).toFixed(1) : Math.round(value), x, height - padding.bottom + 20);
    }

  }, [data, xLabel, isDissociation]);

  return (
    <div className="w-full p-2 rounded-lg h-80">
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }}/>
    </div>
  );
};

export default EnergyPlot;