import { useState, useEffect } from 'react';
import CandlestickChart from './components/CandlestickChart';
import ReasoningSidebar from './components/ReasoningSidebar';
import TradeControls from './components/TradeControls';
import PositionPanel from './components/PositionPanel';
import AccountBar from './components/AccountBar';
import { useWebSocket } from './lib/useWebSocket';
import { AlertTriangle } from 'lucide-react';
import './App.css';

function App() {
  const { connected, data, sendMessage } = useWebSocket('ws://localhost:8000/ws');

  const [candles, setCandles] = useState([]);
  const [tick, setTick] = useState(null);
  const [account, setAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [agentStatus, setAgentStatus] = useState('stopped');
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!data) return;

    if (data.type === 'status') {
      setAgentStatus(data.data.agent ? 'running' : 'stopped');
    } else if (data.type === 'candle_update') {
      setCandles(prev => {
        const newCandle = data.data;
        const last = prev[prev.length - 1];
        if (last && last.time === newCandle.time) {
          return [...prev.slice(0, -1), newCandle];
        }
        return [...prev, newCandle].slice(-500);
      });
    } else if (data.type === 'tick_update') {
      setTick(data.data);
    } else if (data.type === 'account') {
      setAccount(data.data);
    } else if (data.type === 'positions') {
      setPositions(data.data);
    } else if (data.type === 'agent_status') {
      setAgentStatus(data.data.status);
    } else if (data.type === 'reasoning') {
      setLogs(prev => [...prev, data.data].slice(-50));
    } else if (data.type === 'trade_event') {
      console.log('Trade Event:', data.data);
    }
  }, [data]);

  useEffect(() => {
    fetch('http://localhost:8000/api/candles').then(r => r.json()).then(setCandles).catch(console.error);
    fetch('http://localhost:8000/api/account').then(r => r.json()).then(setAccount).catch(console.error);
    fetch('http://localhost:8000/api/positions').then(r => r.json()).then(setPositions).catch(console.error);
  }, []);

  const handleToggleAgent = (running) => {
    fetch(`http://localhost:8000/api/agent/toggle?enable=${running}`, { method: 'POST' });
  };

  const handleManualTrade = (action, volume, sl, tp) => {
    fetch('http://localhost:8000/api/trade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, symbol: 'XAUUSDc', volume, sl, tp })
    });
  };

  return (
    <div className="app-layout">
      {/* Top Bar */}
      <div className="top-bar">
        <div className="top-bar-brand">
          <div className="top-bar-logo">G3</div>
          <span className="top-bar-title">GEMINI TRADER</span>
        </div>
        <div className="top-bar-content">
          <AccountBar account={account} connected={connected} />
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Left: Chart & Positions */}
        <div className="chart-column">
          {/* Chart */}
          <div className="chart-area">
            <CandlestickChart data={candles} tick={tick} />

            {/* Trade Controls Overlay */}
            <div className="trade-overlay">
              <TradeControls
                status={agentStatus}
                onToggleAgent={handleToggleAgent}
                onManualTrade={handleManualTrade}
              />
            </div>
          </div>

          {/* Positions */}
          <div className="positions-panel">
            <div className="positions-panel-header">
              Open Positions
            </div>
            <div className="positions-panel-body">
              <PositionPanel positions={positions} currentTick={tick} />
            </div>
          </div>
        </div>

        {/* Right: AI Reasoning Sidebar */}
        <div className="sidebar">
          <ReasoningSidebar logs={logs} status={agentStatus} />
        </div>
      </div>

      {/* Mobile Warning */}
      <div className="mobile-warning">
        <AlertTriangle size={40} color="var(--accent-gold)" />
        <h2>Desktop Only</h2>
        <p>This trading platform is designed for large screens.</p>
      </div>
    </div>
  );
}

export default App;
