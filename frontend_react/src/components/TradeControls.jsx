import { useState } from 'react';
import { Play, Pause, Activity } from 'lucide-react';

export default function TradeControls({ status, onToggleAgent, onManualTrade }) {
    const [vol, setVol] = useState(0.01);
    const [sl, setSl] = useState(0);
    const [tp, setTp] = useState(0);

    const isRunning = status === 'running';

    return (
        <div className="trade-controls-gap">
            {/* Agent Toggle */}
            <div className="agent-toggle">
                <div className="agent-toggle-left">
                    <div className={`agent-icon ${isRunning ? 'agent-icon-on anim-pulse' : 'agent-icon-off'}`}>
                        <Activity size={16} />
                    </div>
                    <div>
                        <div className="agent-info-title">Gemini Agent</div>
                        <div className="agent-info-status">{isRunning ? 'Analyzing Market...' : 'Stopped'}</div>
                    </div>
                </div>
                <button
                    className={`btn ${isRunning ? 'btn-stop' : 'btn-start'}`}
                    onClick={() => onToggleAgent(!isRunning)}
                >
                    {isRunning ? <><Pause size={12} /> STOP</> : <><Play size={12} /> START</>}
                </button>
            </div>

            {/* Inputs */}
            <div className="inputs-row">
                <div className="input-group">
                    <label className="input-label">Volume</label>
                    <input
                        type="number" step="0.01"
                        value={vol} onChange={e => setVol(parseFloat(e.target.value))}
                        className="input-field"
                    />
                </div>
                <div className="input-group">
                    <label className="input-label">SL</label>
                    <input
                        type="number" step="0.1"
                        value={sl} onChange={e => setSl(parseFloat(e.target.value))}
                        className="input-field"
                        placeholder="Opt"
                    />
                </div>
                <div className="input-group">
                    <label className="input-label">TP</label>
                    <input
                        type="number" step="0.1"
                        value={tp} onChange={e => setTp(parseFloat(e.target.value))}
                        className="input-field"
                        placeholder="Opt"
                    />
                </div>
            </div>

            {/* Buy / Sell */}
            <div className="trade-buttons-row">
                <button className="btn-buy" onClick={() => onManualTrade('BUY', vol, sl, tp)}>
                    BUY
                </button>
                <button className="btn-sell" onClick={() => onManualTrade('SELL', vol, sl, tp)}>
                    SELL
                </button>
            </div>
        </div>
    );
}
