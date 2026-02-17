"""
FastAPI Server for Gemini 3 Flash AI Trading Platform.
Connects the MCP MT5 bridge, Gemini Agent, and Next.js frontend via WebSockets.
"""

import os
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import (
    CandleData, TickData, PositionInfo, AccountInfo, AgentDecision,
    TradeRequest, WSMessage
)
from mt5_mcp import MT5Bridge
from agent import TradingAgent
from ws_manager import ConnectionManager

load_dotenv()

# Initialize components
mt5_bridge = MT5Bridge()
agent = TradingAgent()
ws_manager = ConnectionManager()

# Global state
agent_running = False
background_task_handle = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: connect details on startup, cleanup on shutdown."""
    print("[Main] Starting up...")
    
    # 1. Connect to MT5
    result = mt5_bridge.initialize()
    if not result["success"]:
        print(f"[Main] SEVERE: {result['message']}")
        # In strict mode, we should ideally stop here
        if os.getenv("FORCE_MT5_DATA", "false").lower() == "true":
            raise RuntimeError(f"STRICT MODE: Failed to connect to MT5. {result['message']}")
    else:
        print(f"[Main] {result['message']}")

    # 2. Start background data loop (non-blocking)
    asyncio.create_task(market_data_loop())

    yield
    
    print("[Main] Shutting down...")
    mt5_bridge.shutdown()


app = FastAPI(title="Gemini 3 Flash Trader", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST API ────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Check system health and connection status."""
    return {
        "status": "online",
        "mt5_connected": mt5_bridge.connected,
        "agent_running": agent_running,
        "mode": "simulation" if mt5_bridge.simulation_mode else "live"
    }


@app.get("/api/account", response_model=AccountInfo)
async def get_account():
    """Get current account information."""
    info = mt5_bridge.get_account_info()
    if "error" in info:
        raise HTTPException(status_code=500, detail=info["error"])
    return info


@app.get("/api/positions", response_model=List[PositionInfo])
async def get_positions():
    """Get all open positions."""
    return mt5_bridge.get_positions()


@app.get("/api/candles", response_model=List[CandleData])
async def get_candles(timeframe: str = "M5", count: int = 200):
    """Get historical candle data."""
    return mt5_bridge.get_rates(timeframe=timeframe, count=count)


@app.post("/api/trade")
async def execute_trade(trade: TradeRequest):
    """Execute a manual trade."""
    if trade.action == "close":
        if not trade.ticket:
            raise HTTPException(status_code=400, detail="Ticket required for close")
        result = mt5_bridge.close_position(trade.ticket)
    else:
        result = mt5_bridge.place_order(
            action=trade.action,
            symbol=trade.symbol,
            volume=trade.volume,
            sl=trade.sl or 0.0,
            tp=trade.tp or 0.0
        )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    # Broadcast trade event
    await ws_manager.broadcast("trade_event", result)
    return result


@app.post("/api/agent/toggle")
async def toggle_agent(enable: bool):
    """Start or stop the autonomous trading agent."""
    global agent_running
    agent_running = enable
    status = "running" if agent_running else "stopped"
    print(f"[Main] Agent {status}")
    await ws_manager.broadcast("agent_status", {"status": status})
    return {"status": status}


# ── WebSocket ───────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial state
        await ws_manager.send_personal(websocket, "status", {
            "mt5": mt5_bridge.connected,
            "agent": agent_running
        })
        
        while True:
            # Keep connection alive + handle incoming messages (e.g. ping)
            data = await websocket.receive_text()
            # Parse if needed, currently we just listen
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ── Background Loops ────────────────────────────────────────

async def market_data_loop():
    """
    Main loop:
    1. Stream prices (candles/ticks) to frontend
    2. Invoke Agent if enabled
    """
    print("[Main] Market data loop started")
    last_candle_time = 0
    
    while True:
        try:
            # 1. Fetch & Broadcast Market Data
            current_tick = mt5_bridge.get_tick()
            candles = mt5_bridge.get_rates(count=2)  # Just need latest for updates
            
            if candles:
                latest_candle = candles[-1]
                await ws_manager.broadcast("candle_update", latest_candle)
            
            if current_tick:
                await ws_manager.broadcast("tick_update", current_tick)

            # 2. Agent Logic (if running)
            if agent_running:
                # Run agent roughly every new candle or every N seconds
                # For this demo, we'll run it every 10s to see activity
                if int(datetime.now().timestamp()) % 10 == 0:
                    await run_agent_cycle(current_tick)

            # 3. Broadcast Account/Positions periodically
            if int(datetime.now().timestamp()) % 2 == 0:
                positions = mt5_bridge.get_positions()
                account = mt5_bridge.get_account_info()
                await ws_manager.broadcast("positions", positions)
                await ws_manager.broadcast("account", account)

            await asyncio.sleep(1)  # 1Hz update rate

        except Exception as e:
            print(f"[Loop Error] {e}")
            await asyncio.sleep(5)


async def run_agent_cycle(tick: dict):
    """One cycle of the AI agent: Analyze -> Reason -> Act."""
    print("[Agent] Analyzing market...")
    
    # Gather context
    candles = mt5_bridge.get_rates(count=50) # Give agent more history
    positions = mt5_bridge.get_positions()
    account = mt5_bridge.get_account_info()
    
    # 1. Ask Gemini
    decision = await agent.analyze(candles, tick, account, positions)
    
    # 2. Broadcast Reasoning
    await ws_manager.broadcast("reasoning", {
        "action": decision["action"],
        "reasoning": decision["reasoning"],
        "confidence": decision["confidence"],
        "timestamp": datetime.now().isoformat()
    })
    
    # 3. Execute Decision
    if decision["action"] in ["BUY", "SELL"]:
        # Check confidence threshold
        if decision["confidence"] >= 0.7:
            print(f"[Agent] Executing {decision['action']} ({decision['confidence']})")
            result = mt5_bridge.place_order(
                action=decision["action"],
                volume=decision.get("volume", 0.01),
                sl=decision.get("sl", 0.0),
                tp=decision.get("tp", 0.0)
            )
            await ws_manager.broadcast("trade_event", result)
    elif decision["action"] == "CLOSE":
        # Close all relevant positions
        for p in positions:
            res = mt5_bridge.close_position(p["ticket"])
            await ws_manager.broadcast("trade_event", res)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
