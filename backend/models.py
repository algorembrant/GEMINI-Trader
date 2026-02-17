"""
Pydantic data models for the Gemini 3 Flash AI Trading Platform.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"
    HOLD = "HOLD"
    DO_NOTHING = "DO_NOTHING"


class CandleData(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class TickData(BaseModel):
    bid: float
    ask: float
    time: int
    symbol: str


class PositionInfo(BaseModel):
    ticket: int
    symbol: str
    type: str  # "buy" or "sell"
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    time: int


class AccountInfo(BaseModel):
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: Optional[float] = None
    profit: float
    server: str
    currency: str
    trade_mode: str  # "demo" or "live"


class AgentDecision(BaseModel):
    action: TradeAction
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    sl: Optional[float] = None
    tp: Optional[float] = None
    volume: Optional[float] = None


class TradeRequest(BaseModel):
    action: Literal["buy", "sell", "close"]
    symbol: str = "XAUUSDc"
    volume: float = 0.01
    sl: Optional[float] = None
    tp: Optional[float] = None
    ticket: Optional[int] = None  # for closing specific position


class WSMessage(BaseModel):
    type: str  # "candles", "tick", "reasoning", "trade_event", "positions", "account", "agent_status"
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
