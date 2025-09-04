import React, { useRef, useEffect } from 'react';

interface EnergyPlotProps {
  data: Array<{ iteration: number; energy: number }>;
  xLabel?: string;
  isDissociation?: boolean;
}

const EnergyPlot: React.FC<EnergyPlotProps> = ({ 
  data, 
  xLabel = "Iteration", 
  isDissociation = false 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!data || data.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 20, bottom: 50, left: 70 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Find data bounds
    const xValues = data.map(d => d.iteration);
    const yValues = data.map(d => d.energy);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);
    
    const xRange = xMax - xMin || 1;
    const yRange = yMax - yMin || 1;

    // Helper functions
    const xScale = (x: number) => padding.left + ((x - xMin) / xRange) * plotWidth;
    const yScale = (y: number) => padding.top + ((yMax - y) / yRange) * plotHeight;

    // Draw grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    
    // Vertical grid lines
    for (let i = 0; i <= 10; i++) {
      const x = padding.left + (i / 10) * plotWidth;
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, padding.top + plotHeight);
      ctx.stroke();
    }
    
    // Horizontal grid lines
    for (let i = 0; i <= 10; i++) {
      const y = padding.top + (i / 10) * plotHeight;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + plotWidth, y);
      ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 3;
    
    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + plotHeight);
    ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight);
    ctx.stroke();
    
    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + plotHeight);
    ctx.stroke();

    // Draw data line
    if (data.length > 1) {
      const gradient = ctx.createLinearGradient(0, 0, plotWidth, 0);
      gradient.addColorStop(0, '#2563eb');
      gradient.addColorStop(0.5, '#3b82f6');
      gradient.addColorStop(1, '#8b5cf6');
      
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      ctx.beginPath();
      data.forEach((point, i) => {
        const x = xScale(point.iteration);
        const y = yScale(point.energy);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw points
      ctx.fillStyle = '#1e3a8a';
      data.forEach(point => {
        const x = xScale(point.iteration);
        const y = yScale(point.energy);
        
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
        
        // Highlight last point
        if (point === data[data.length - 1]) {
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 3;
          ctx.stroke();
        }
      });
    }

    // Draw labels
    ctx.fillStyle = '#334155';
    ctx.font = 'bold 13px system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';

    // X-axis label
    ctx.fillText(xLabel, padding.left + plotWidth / 2, height - 10);

    // Y-axis label
    ctx.save();
    ctx.translate(15, padding.top + plotHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Energy (Hartree)', 0, 0);
    ctx.restore();

    // Draw tick labels
    ctx.font = '11px system-ui, -apple-system, sans-serif';
    
    // X-axis ticks
    for (let i = 0; i <= 5; i++) {
      const value = xMin + (i / 5) * xRange;
      const x = padding.left + (i / 5) * plotWidth;
      const displayValue = isDissociation ? (value / 100).toFixed(1) : Math.round(value);
      ctx.fillText(displayValue.toString(), x, padding.top + plotHeight + 20);
    }
    
    // Y-axis ticks
    for (let i = 0; i <= 5; i++) {
      const value = yMin + (i / 5) * yRange;
      const y = padding.top + plotHeight - (i / 5) * plotHeight;
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(4), padding.left - 10, y + 4);
    }

  }, [data, xLabel, isDissociation]);

  return (
    <div className="w-full h-80 bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg p-4">
      <canvas
        ref={canvasRef}
        className="w-full h-full rounded-md"
        style={{ display: 'block' }}
      />
    </div>
  );
};

export default EnergyPlot;