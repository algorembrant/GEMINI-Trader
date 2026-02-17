import { Signal } from 'lucide-react';

export default function AccountBar({ account, connected }) {
    if (!account || !account.balance) return null;

    return (
        <div className="account-bar">
            <div className="account-metrics">
                <div className="connection-indicator">
                    <div className={`connection-dot ${connected ? 'connection-dot-on' : 'connection-dot-off'}`} />
                    <span>{connected ? 'CONNECTED' : 'DISCONNECTED'}</span>
                </div>
                <div className="account-metric">
                    <span className="account-metric-label">Balance:</span>
                    <span className="account-metric-value">${account.balance.toFixed(2)}</span>
                </div>
                <div className="account-metric">
                    <span className="account-metric-label">Equity:</span>
                    <span className="account-metric-value">${account.equity.toFixed(2)}</span>
                </div>
                <div className="account-metric">
                    <span className="account-metric-label">Margin:</span>
                    <span className="color-secondary font-mono">${account.margin.toFixed(2)}</span>
                </div>
            </div>

            <div className={`badge ${account.trade_mode === 'demo' ? 'badge-blue' : 'badge-red'}`}>
                {account.trade_mode ? account.trade_mode.toUpperCase() : 'DEMO'}
            </div>
        </div>
    );
}
