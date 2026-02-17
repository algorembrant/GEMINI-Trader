import { useEffect, useRef, useState, useCallback } from 'react';

export default function CandlestickChart({ data, tick }) {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    // Viewport state: Offset from the RIGHT (0 means latest candle is at edge)
    // Scale: Pixels per candle (width + gap)
    const [viewport, setViewport] = useState({ offset: 0, scale: 10 });
    const [isDragging, setIsDragging] = useState(false);
    const lastMouseX = useRef(0);

    const colors = {
        bg: '#080b14',
        grid: '#1e2329',
        text: '#8b949e',
        up: '#26a641',
        down: '#da3633',
        crosshair: '#f0b429',
    };

    // Handle Resize
    useEffect(() => {
        const handleResize = () => draw();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Main Draw Function
    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (!canvas || !container || !data) return;

        const rect = container.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;

        // Handle Retina displays
        const dpr = window.devicePixelRatio || 1;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);

        // Clear background
        ctx.fillStyle = colors.bg;
        ctx.fillRect(0, 0, width, height);

        if (data.length === 0) return;

        const { offset, scale } = viewport;
        const candleWidth = scale * 0.7; // 70% body, 30% gap
        const rightMargin = 80; // Space for price scale
        const chartWidth = width - rightMargin;

        // Calculate visible range
        // Visible candles = chartWidth / scale
        const visibleCount = Math.ceil(chartWidth / scale);

        // Index of the rightmost candle to show
        // If offset is 0, we show data[len-1] at the right edge
        const rightIndex = data.length - 1 - Math.floor(offset / scale);
        const leftIndex = Math.max(0, rightIndex - visibleCount - 1);

        // Subset for rendering
        const visibleData = data.slice(leftIndex, rightIndex + 1);

        if (visibleData.length === 0) return;

        // Calculate Y-axis range (Min/Max Price)
        let minPrice = Infinity;
        let maxPrice = -Infinity;
        visibleData.forEach(c => {
            if (c.low < minPrice) minPrice = c.low;
            if (c.high > maxPrice) maxPrice = c.high;
        });

        // Add padding to price range
        const padding = (maxPrice - minPrice) * 0.1 || 1.0;
        minPrice -= padding;
        maxPrice += padding;
        const priceRange = maxPrice - minPrice;

        // Helper: Price to Y coordinate
        const getY = (price) => height - ((price - minPrice) / priceRange) * height;

        // Helper: Index to X coordinate
        // We render from right to left conceptually
        // X = chartWidth - ( (total_data_index - right_index_offset) * scale )
        // Simply: x position relative to the right edge of the chart area
        const getX = (index) => {
            const posFromRight = (data.length - 1 - index) * scale + (offset % scale);
            return chartWidth - posFromRight - (scale / 2);
        };

        // Draw Grid & Price Labels
        ctx.strokeStyle = colors.grid;
        ctx.lineWidth = 0.5;
        ctx.fillStyle = colors.text;
        ctx.font = '11px monospace';
        ctx.textAlign = 'left';

        // Vertical Price Grid
        const gridLines = 8;
        for (let i = 0; i <= gridLines; i++) {
            const y = (height / gridLines) * i;
            const price = maxPrice - (i / gridLines) * priceRange;

            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(chartWidth, y);
            ctx.stroke();

            ctx.fillText(price.toFixed(2), chartWidth + 5, y + 4);
        }

        // Horizontal Time Grid (simplified)
        // ... (could add time labels here)

        // Draw Candles
        visibleData.forEach((candle, i) => {
            const originalIndex = leftIndex + i;
            const x = getX(originalIndex);

            const yOpen = getY(candle.open);
            const yClose = getY(candle.close);
            const yHigh = getY(candle.high);
            const yLow = getY(candle.low);

            const isUp = candle.close >= candle.open;
            const color = isUp ? colors.up : colors.down;

            ctx.fillStyle = color;
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;

            // Wick
            ctx.beginPath();
            ctx.moveTo(x, yHigh);
            ctx.lineTo(x, yLow);
            ctx.stroke();

            // Body
            const bodyH = Math.max(Math.abs(yClose - yOpen), 1);
            ctx.fillRect(x - candleWidth / 2, Math.min(yOpen, yClose), candleWidth, bodyH);
        });

        // Draw Current Price Line (Bid)
        if (tick && tick.bid) {
            const yBid = getY(tick.bid);
            if (yBid >= 0 && yBid <= height) {
                ctx.strokeStyle = colors.crosshair;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(0, yBid);
                ctx.lineTo(chartWidth, yBid);
                ctx.stroke();
                ctx.setLineDash([]);

                // Label
                ctx.fillStyle = colors.crosshair;
                ctx.fillRect(chartWidth, yBid - 10, 60, 20);
                ctx.fillStyle = '#000';
                ctx.fillText(tick.bid.toFixed(2), chartWidth + 5, yBid + 4);
            }
        }
    }, [data, tick, viewport, colors]);

    // Redraw when dependencies change
    useEffect(() => {
        draw();
    }, [draw]);

    // Interaction Handlers
    const handleMouseDown = (e) => {
        setIsDragging(true);
        lastMouseX.current = e.clientX;
    };

    const handleMouseMove = (e) => {
        if (!isDragging) return;
        const deltaX = e.clientX - lastMouseX.current;
        lastMouseX.current = e.clientX;

        setViewport(prev => ({
            ...prev,
            offset: prev.offset - deltaX // Dragging right moves view left (history)
        }));
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    const handleWheel = (e) => {
        e.preventDefault();
        const zoomSensitivity = 0.001;
        setViewport(prev => {
            const newScale = Math.max(2, Math.min(50, prev.scale * (1 - e.deltaY * zoomSensitivity)));
            return { ...prev, scale: newScale };
        });
    };

    return (
        <div
            ref={containerRef}
            className="chart-container"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            style={{
                cursor: isDragging ? 'grabbing' : 'grab',
                touchAction: 'none',
                width: '100%',
                height: '100%',
                position: 'relative'
            }}
        >
            <canvas ref={canvasRef} style={{ display: 'block' }} />

            {/* Simple OHLC overlay */}
            {data && data.length > 0 && (
                <div style={{
                    position: 'absolute',
                    top: 10,
                    left: 10,
                    color: '#8b949e',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    pointerEvents: 'none'
                }}>
                    Last: O:{data[data.length - 1].open.toFixed(2)} H:{data[data.length - 1].high.toFixed(2)} L:{data[data.length - 1].low.toFixed(2)} C:{data[data.length - 1].close.toFixed(2)}
                </div>
            )}
        </div>
    );
}
