"""
MT5 MCP Bridge — wraps the MetaTrader5 Python SDK into clean tool functions
for the AI agent to call. Supports both demo and live accounts.
Falls back to simulated data when MT5 is not available.
"""

import os
import time
import random
import math
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Try to import MetaTrader5; if unavailable, use simulation mode
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    if os.getenv("FORCE_MT5_DATA", "false").lower() == "true":
        raise ImportError("CRITICAL: MetaTrader5 package not found and FORCE_MT5_DATA=true")
    print("[MT5] MetaTrader5 package not available — running in SIMULATION mode")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class MT5Bridge:
    """Bridge to MetaTrader 5 via the official Python SDK."""

    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1 if MT5_AVAILABLE else 1,
        "M5": mt5.TIMEFRAME_M5 if MT5_AVAILABLE else 5,
        "M15": mt5.TIMEFRAME_M15 if MT5_AVAILABLE else 15,
        "M30": mt5.TIMEFRAME_M30 if MT5_AVAILABLE else 30,
        "H1": mt5.TIMEFRAME_H1 if MT5_AVAILABLE else 60,
        "H4": mt5.TIMEFRAME_H4 if MT5_AVAILABLE else 240,
        "D1": mt5.TIMEFRAME_D1 if MT5_AVAILABLE else 1440,
    }

    def __init__(self):
        self.connected = False
        self.simulation_mode = not MT5_AVAILABLE
        self.symbol = os.getenv("TRADING_SYMBOL", "XAUUSDm")
        self._sim_base_price = 2650.0
        self._sim_positions = []
        self._sim_ticket_counter = 1000

    def initialize(self) -> dict:
        """Connect to the MT5 terminal."""
        if self.simulation_mode:
            if os.getenv("FORCE_MT5_DATA", "false").lower() == "true":
                return {
                    "success": False,
                    "message": "CRITICAL: MT5 not available but FORCE_MT5_DATA is true. Exiting."
                }
            self.connected = True
            return {
                "success": True,
                "message": "Running in SIMULATION mode (MT5 not available)",
                "mode": "simulation"
            }

        mt5_path = os.getenv("MT5_PATH")
        login = int(os.getenv("MT5_LOGIN", "0"))
        password = os.getenv("MT5_PASSWORD", "")
        server = os.getenv("MT5_SERVER", "")

        init_kwargs = {}
        if mt5_path:
            init_kwargs["path"] = mt5_path

        if not mt5.initialize(**init_kwargs):
            err_code = mt5.last_error()
            if os.getenv("FORCE_MT5_DATA", "false").lower() == "true":
                return {"success": False, "message": f"CRITICAL: MT5 init failed: {err_code}"}
            return {"success": False, "message": f"MT5 init failed: {err_code}"}

        if login and password and server:
            authorized = mt5.login(login=login, password=password, server=server)
            if not authorized:
                return {"success": False, "message": f"MT5 login failed: {mt5.last_error()}"}

        self.connected = True
        account = mt5.account_info()
        mode = "demo" if account.trade_mode == 0 else "live"
        return {
            "success": True,
            "message": f"Connected to MT5 ({mode}) — Account #{account.login}",
            "mode": mode
        }

    def shutdown(self):
        """Disconnect from MT5."""
        if not self.simulation_mode and MT5_AVAILABLE:
            mt5.shutdown()
        self.connected = False

    def get_account_info(self) -> dict:
        """Get trading account information."""
        if self.simulation_mode:
            return {
                "login": 12345678,
                "balance": 10000.00,
                "equity": 10000.00 + sum(p.get("profit", 0) for p in self._sim_positions),
                "margin": sum(p.get("volume", 0) * 1000 for p in self._sim_positions),
                "free_margin": 10000.00 - sum(p.get("volume", 0) * 1000 for p in self._sim_positions),
                "margin_level": 0.0,
                "profit": sum(p.get("profit", 0) for p in self._sim_positions),
                "server": "SimulationServer",
                "currency": "USD",
                "trade_mode": os.getenv("ACCOUNT_MODE", "demo")
            }

        account = mt5.account_info()
        if account is None:
            return {"error": "Failed to get account info"}

        return {
            "login": account.login,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "margin_level": account.margin_level,
            "profit": account.profit,
            "server": account.server,
            "currency": account.currency,
            "trade_mode": "demo" if account.trade_mode == 0 else "live"
        }

    def get_rates(self, symbol: Optional[str] = None, timeframe: str = "M5", count: int = 200) -> list:
        """Fetch OHLCV candle data."""
        symbol = symbol or self.symbol

        if self.simulation_mode:
            return self._simulate_candles(count, timeframe)

        tf = self.TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_M5)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

        if rates is None or len(rates) == 0:
            return []

        candles = []
        for r in rates:
            candles.append({
                "time": int(r["time"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["tick_volume"]),
            })
        return candles

    def get_tick(self, symbol: Optional[str] = None) -> dict:
        """Get latest tick (bid/ask)."""
        symbol = symbol or self.symbol

        if self.simulation_mode:
            price = self._sim_base_price + random.uniform(-5, 5)
            spread = random.uniform(0.1, 0.5)
            return {
                "bid": round(price, 2),
                "ask": round(price + spread, 2),
                "time": int(time.time()),
                "symbol": symbol
            }

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"error": f"No tick data for {symbol}"}

        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "time": tick.time,
            "symbol": symbol
        }

    def get_positions(self, symbol: Optional[str] = None) -> list:
        """List open positions."""
        symbol = symbol or self.symbol

        if self.simulation_mode:
            tick = self.get_tick(symbol)
            for p in self._sim_positions:
                if p["type"] == "buy":
                    p["price_current"] = tick["bid"]
                    p["profit"] = round((tick["bid"] - p["price_open"]) * p["volume"] * 100, 2)
                else:
                    p["price_current"] = tick["ask"]
                    p["profit"] = round((p["price_open"] - tick["ask"]) * p["volume"] * 100, 2)
            return self._sim_positions

        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []

        result = []
        for p in positions:
            result.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "buy" if p.type == 0 else "sell",
                "volume": p.volume,
                "price_open": p.price_open,
                "price_current": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "time": p.time,
            })
        return result

    def place_order(self, action: str, symbol: Optional[str] = None,
                    volume: float = 0.01, sl: float = 0.0, tp: float = 0.0) -> dict:
        """Place a market order (buy or sell)."""
        symbol = symbol or self.symbol

        if self.simulation_mode:
            if os.getenv("FORCE_MT5_DATA", "false").lower() == "true":
                return {"success": False, "message": "Cannot place mock order in STRICT MT5 mode."}

            tick = self.get_tick(symbol)
            price = tick["ask"] if action.lower() == "buy" else tick["bid"]
            self._sim_ticket_counter += 1
            pos = {
                "ticket": self._sim_ticket_counter,
                "symbol": symbol,
                "type": action.lower(),
                "volume": volume,
                "price_open": price,
                "price_current": price,
                "sl": sl,
                "tp": tp,
                "profit": 0.0,
                "time": int(time.time()),
            }
            self._sim_positions.append(pos)
            return {"success": True, "ticket": pos["ticket"], "price": price, "action": action}

        # Real MT5 order
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"success": False, "message": f"Cannot get tick for {symbol}"}

        order_type = mt5.ORDER_TYPE_BUY if action.lower() == "buy" else mt5.ORDER_TYPE_SELL
        price = tick.ask if action.lower() == "buy" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 3000000,
            "comment": "Gemini3Flash-Agent",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl > 0:
            request["sl"] = sl
        if tp > 0:
            request["tp"] = tp

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = result.comment if result else "Unknown error"
            return {"success": False, "message": error_msg}

        return {
            "success": True,
            "ticket": result.order,
            "price": result.price,
            "action": action
        }

    def close_position(self, ticket: int) -> dict:
        """Close a specific position by ticket."""
        if self.simulation_mode:
            for i, p in enumerate(self._sim_positions):
                if p["ticket"] == ticket:
                    closed = self._sim_positions.pop(i)
                    return {"success": True, "ticket": ticket, "profit": closed["profit"]}
            return {"success": False, "message": f"Position {ticket} not found"}

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return {"success": False, "message": f"Position {ticket} not found"}

        pos = positions[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == 0 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 3000000,
            "comment": "Gemini3Flash-Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = result.comment if result else "Unknown error"
            return {"success": False, "message": error_msg}

        return {"success": True, "ticket": ticket, "profit": pos.profit}

    # ── Simulation helpers ──────────────────────────────────────────

    def _simulate_candles(self, count: int, timeframe: str = "M5") -> list:
        """Generate realistic-looking simulated gold candle data."""
        tf_minutes = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 60, "H4": 240, "D1": 1440
        }.get(timeframe, 5)

        candles = []
        now = int(time.time())
        price = self._sim_base_price

        for i in range(count):
            t = now - (count - i) * tf_minutes * 60
            change = random.gauss(0, 2.5)
            o = round(price, 2)
            c = round(price + change, 2)
            h = round(max(o, c) + abs(random.gauss(0, 1.5)), 2)
            low = round(min(o, c) - abs(random.gauss(0, 1.5)), 2)
            vol = random.randint(50, 500)

            candles.append({
                "time": t,
                "open": o,
                "high": h,
                "low": low,
                "close": c,
                "volume": vol,
            })
            price = c
            self._sim_base_price = c

        return candles
