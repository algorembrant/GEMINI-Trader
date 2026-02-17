import { useEffect, useRef } from 'react';

export default function CandlestickChart({ data, tick }) {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    const candleWidth = 10;
    const candleSpacing = 2;
    const colors = {
        bg: '#080b14',
        grid: '#1e2329',
        text: '#8b949e',
        up: '#26a641',
        down: '#da3633',
        upBright: '#3fb950',
        downBright: '#f85149',
        crosshair: '#f0b429',
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;

        if (!canvas || !container || !Array.isArray(data) || data.length === 0) return;

        const ctx = canvas.getContext('2d');
        let animFrame;

        const draw = () => {
            const rect = container.getBoundingClientRect();
            const width = rect.width;
            const height = rect.height;

            if (width === 0 || height === 0) return;

            const dpr = window.devicePixelRatio || 1;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = colors.bg;
            ctx.fillRect(0, 0, width, height);

            const visibleCandlesCount = Math.floor(width / (candleWidth + candleSpacing));
            const startIndex = Math.max(0, data.length - visibleCandlesCount);
            const visibleData = data.slice(startIndex);

            if (visibleData.length === 0) return;

            let minPrice = Infinity;
            let maxPrice = -Infinity;
            visibleData.forEach(c => {
                if (c.low < minPrice) minPrice = c.low;
                if (c.high > maxPrice) maxPrice = c.high;
            });

            const priceRange = maxPrice - minPrice;
            if (priceRange === 0) {
                minPrice -= 1;
                maxPrice += 1;
            } else {
                minPrice -= priceRange * 0.1;
                maxPrice += priceRange * 0.1;
            }

            const chartPadR = 70;
            const chartW = width - chartPadR;

            const getY = (price) => height - ((price - minPrice) / (maxPrice - minPrice)) * height;
            const getX = (index) => index * (candleWidth + candleSpacing) + (candleWidth / 2);

            // Grid
            ctx.strokeStyle = colors.grid;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            for (let i = 1; i < 10; i++) {
                const y = (height / 10) * i;
                ctx.moveTo(0, y);
                ctx.lineTo(chartW, y);
            }
            ctx.stroke();

            // Price labels on right axis
            ctx.font = '10px "JetBrains Mono", monospace';
            ctx.fillStyle = colors.text;
            ctx.textAlign = 'left';
            for (let i = 1; i < 10; i++) {
                const y = (height / 10) * i;
                const price = maxPrice - ((maxPrice - minPrice) / 10) * i;
                ctx.fillText(price.toFixed(2), chartW + 8, y + 3);
            }

            // Candles
            visibleData.forEach((candle, i) => {
                const x = getX(i);
                if (x > chartW) return;

                const yOpen = getY(candle.open);
                const yClose = getY(candle.close);
                const yHigh = getY(candle.high);
                const yLow = getY(candle.low);

                const isUp = candle.close >= candle.open;
                const color = isUp ? colors.up : colors.down;

                // Wick
                ctx.strokeStyle = color;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(x, yHigh);
                ctx.lineTo(x, yLow);
                ctx.stroke();

                // Body
                ctx.fillStyle = color;
                const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
                ctx.fillRect(x - candleWidth / 2, Math.min(yOpen, yClose), candleWidth, bodyHeight);

                // Volume
                const volumes = visibleData.map(c => c.volume);
                const maxVol = Math.max(...volumes) || 1;
                const volHeight = (candle.volume / maxVol) * (height * 0.12);
                ctx.fillStyle = isUp ? 'rgba(38, 166, 65, 0.15)' : 'rgba(218, 54, 33, 0.15)';
                ctx.fillRect(x - candleWidth / 2, height - volHeight, candleWidth, volHeight);
            });

            // Current Price Line
            if (tick && tick.bid) {
                const yTick = getY(tick.bid);
                if (yTick >= 0 && yTick <= height) {
                    ctx.strokeStyle = colors.crosshair;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 4]);
                    ctx.beginPath();
                    ctx.moveTo(0, yTick);
                    ctx.lineTo(chartW, yTick);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    // Price label
                    ctx.fillStyle = colors.crosshair;
                    const labelW = 65;
                    ctx.fillRect(chartW, yTick - 10, labelW, 20);
                    ctx.fillStyle = '#000';
                    ctx.font = 'bold 10px "JetBrains Mono", monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(tick.bid.toFixed(2), chartW + labelW / 2, yTick + 4);
                    ctx.textAlign = 'left';
                }
            }
        };

        const resizeObserver = new ResizeObserver(() => {
            cancelAnimationFrame(animFrame);
            animFrame = requestAnimationFrame(draw);
        });
        resizeObserver.observe(container);

        draw();

        return () => {
            resizeObserver.disconnect();
            cancelAnimationFrame(animFrame);
        };
    }, [data, tick]);

    return (
        <div ref={containerRef} className="chart-container">
            <canvas ref={canvasRef} />
            {/* OHLC Overlay */}
            {Array.isArray(data) && data.length > 0 && (
                <div className="chart-ohlc-overlay">
                    <span>O: <span className="chart-ohlc-value">{data[data.length - 1].open.toFixed(2)}</span></span>
                    <span>H: <span className="chart-ohlc-value">{data[data.length - 1].high.toFixed(2)}</span></span>
                    <span>L: <span className="chart-ohlc-value">{data[data.length - 1].low.toFixed(2)}</span></span>
                    <span>C: <span className={`chart-ohlc-value font-bold ${data[data.length - 1].close >= data[data.length - 1].open ? 'color-green' : 'color-red'}`}>
                        {data[data.length - 1].close.toFixed(2)}
                    </span></span>
                </div>
            )}
        </div>
    );
}
