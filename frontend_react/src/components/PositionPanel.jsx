import { XCircle } from 'lucide-react';

export default function PositionPanel({ positions }) {
    if (!positions || positions.length === 0) {
        return (
            <div className="pos-table-empty">
                No open positions
            </div>
        );
    }

    return (
        <div className="pos-table">
            <div className="pos-header">
                <div>Ticket</div>
                <div>Type</div>
                <div>Vol</div>
                <div>Open</div>
                <div>Current</div>
                <div style={{ textAlign: 'right' }}>P&L</div>
                <div style={{ textAlign: 'right' }}>Action</div>
            </div>

            {positions.map(pos => {
                const isProfit = pos.profit >= 0;
                return (
                    <div key={pos.ticket} className="pos-row">
                        <div className="pos-cell color-muted">#{pos.ticket}</div>
                        <div className={`pos-cell font-bold ${pos.type === 'buy' ? 'color-green' : 'color-red'}`}>
                            {pos.type.toUpperCase()}
                        </div>
                        <div className="pos-cell color-secondary">{pos.volume}</div>
                        <div className="pos-cell">{pos.price_open.toFixed(2)}</div>
                        <div className="pos-cell color-secondary">{pos.price_current.toFixed(2)}</div>
                        <div className={`pos-cell-right font-bold ${isProfit ? 'color-green' : 'color-red'}`}>
                            {pos.profit > 0 ? '+' : ''}{pos.profit.toFixed(2)}
                        </div>
                        <div className="pos-close-btn">
                            <button
                                title="Close Position"
                                onClick={() => {
                                    fetch('http://localhost:8000/api/trade', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ action: 'close', ticket: pos.ticket })
                                    });
                                }}
                            >
                                <XCircle size={14} />
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
