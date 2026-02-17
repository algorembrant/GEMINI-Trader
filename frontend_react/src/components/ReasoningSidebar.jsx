import { useRef, useEffect } from 'react';
import { Cpu, Activity } from 'lucide-react';

export default function ReasoningSidebar({ logs, status }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <>
            {/* Header */}
            <div className="sidebar-header">
                <div className="sidebar-header-left">
                    <Cpu size={16} className={status === 'running' ? 'color-green anim-pulse' : 'color-muted'} />
                    <span className="sidebar-header-title">GEMINI 3 FLASH</span>
                </div>
                <div className={`badge ${status === 'running' ? 'badge-green' : 'badge-red'}`}>
                    {status.toUpperCase()}
                </div>
            </div>

            {/* Log Stream */}
            <div className="sidebar-body">
                {(!logs || logs.length === 0) && (
                    <div className="sidebar-empty">
                        <Activity size={28} strokeWidth={1} />
                        <span>Waiting for agent thoughts...</span>
                    </div>
                )}

                {logs && [...logs].reverse().map((log, i) => (
                    <div key={i} className="log-entry fade-in">
                        <div className="log-entry-header">
                            <span className={`badge ${log.action === 'BUY' ? 'badge-green' :
                                    log.action === 'SELL' ? 'badge-red' :
                                        log.action === 'CLOSE' ? 'badge-blue' :
                                            'badge-neutral'
                                }`}>
                                {log.action}
                            </span>
                            <div className="confidence-info">
                                <div className="confidence-bar-track">
                                    <div
                                        className={`confidence-bar-fill ${log.confidence > 0.7 ? 'confidence-bar-high' : 'confidence-bar-low'}`}
                                        style={{ width: `${log.confidence * 100}%` }}
                                    />
                                </div>
                                <span>{(log.confidence * 100).toFixed(0)}%</span>
                            </div>
                        </div>

                        <p className="log-entry-body">{log.reasoning}</p>

                        <div className="log-entry-footer">
                            <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                            <span>GEMINI-2.0-FLASH</span>
                        </div>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            {/* Footer */}
            <div className="sidebar-footer">
                <span className="live-dot" />
                <span>Live connection established</span>
            </div>
        </>
    );
}
