"""
Gemini 3 Flash Trading Agent — the 'Antigravity Trader'.
Analyzes XAUUSDc market data and makes autonomous trading decisions.
"""

import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Try importing Google GenAI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[Agent] google-genai not available — running with MOCK agent")


SYSTEM_PROMPT = """You are **Antigravity Trader**, an elite AI trading agent specializing in XAUUSDc (Gold vs USD) trading on MetaTrader 5.

## Your Role
You analyze real-time market data and make precise trading decisions. You run autonomously, making buy/sell/hold decisions based on price action, candlestick patterns, and market structure.

## Your Trading Rules
1. **Risk Management First**: Never risk more than 2% of account balance per trade.
2. **Always set SL/TP**: Stop Loss and Take Profit are mandatory. Minimum SL: 50 pips from entry. TP should be at least 1.5x the SL distance (risk-reward ratio).
3. **One position at a time**: Don't open a new position if one is already open. You can CLOSE an existing position or HOLD.
4. **Market Structure**: Look for support/resistance, trend direction, and key price levels in the candle data.
5. **Confidence threshold**: Only trade with confidence >= 0.7. Below that, HOLD or DO_NOTHING.

## Input Data
You will receive:
- **Recent candles**: OHLCV data (most recent candles for the timeframe)
- **Current tick**: Latest bid/ask prices
- **Account info**: Balance, equity, margin, profit
- **Open positions**: Currently held positions (if any)

## Output Format
You MUST respond with ONLY valid JSON (no markdown, no extra text):
{
    "action": "BUY" | "SELL" | "CLOSE" | "HOLD" | "DO_NOTHING",
    "reasoning": "Your detailed analysis explaining WHY you made this decision. Include what patterns you see, key levels, and your risk assessment.",
    "confidence": 0.0 to 1.0,
    "sl": null or price level for stop loss,
    "tp": null or price level for take profit,
    "volume": null or lot size (e.g. 0.01)
}

## Action Definitions
- **BUY**: Open a long position (you expect price to go UP)
- **SELL**: Open a short position (you expect price to go DOWN)
- **CLOSE**: Close the current open position
- **HOLD**: Keep the current position open, no changes
- **DO_NOTHING**: No position open and no good setup — wait
"""


class TradingAgent:
    """Gemini 3 Flash Agent for autonomous XAUUSDc trading."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        self.client = None
        self.decision_history: list[dict] = []

        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            print(f"[Agent] Gemini client initialized with model: {self.model_name}")
        else:
            print("[Agent] No Gemini API key — using mock decisions")

    async def analyze(self, candles: list, tick: dict, account: dict,
                      positions: list) -> dict:
        """
        Analyze market data and return a trading decision.
        Returns: { action, reasoning, confidence, sl, tp, volume }
        """
        if not self.client:
            # In strict usage, we simply return DO_NOTHING if no AI is available
            return {
                "action": "DO_NOTHING",
                "reasoning": "Gemini API client not initialized (check keys)",
                "confidence": 0.0,
                "sl": None, "tp": None, "volume": None
            }

        # Build the market context prompt
        recent_candles = candles[-20:] if len(candles) > 20 else candles
        candle_text = self._format_candles(recent_candles)

        prompt = f"""## Current Market State — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Latest Tick
Bid: {tick.get('bid', 'N/A')} | Ask: {tick.get('ask', 'N/A')}

### Recent Candles (OHLCV, most recent last)
{candle_text}

### Account Status
Balance: ${account.get('balance', 0):.2f}
Equity: ${account.get('equity', 0):.2f}
Free Margin: ${account.get('free_margin', 0):.2f}
Current P&L: ${account.get('profit', 0):.2f}

### Open Positions
{self._format_positions(positions)}

### Recent Decision History
{self._format_history()}

Analyze the market and make your trading decision now."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )

            response_text = response.text.strip()
            # Clean up potential markdown wrapping
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            decision = json.loads(response_text)

            # Validate required fields
            decision.setdefault("action", "DO_NOTHING")
            decision.setdefault("reasoning", "No reasoning provided")
            decision.setdefault("confidence", 0.5)
            decision.setdefault("sl", None)
            decision.setdefault("tp", None)
            decision.setdefault("volume", float(os.getenv("DEFAULT_VOLUME", "0.01")))

            # Save to history
            self.decision_history.append({
                "time": datetime.now().isoformat(),
                "action": decision["action"],
                "confidence": decision["confidence"],
            })
            if len(self.decision_history) > 50:
                self.decision_history = self.decision_history[-50:]

            return decision

        except json.JSONDecodeError as e:
            return {
                "action": "DO_NOTHING",
                "reasoning": f"Failed to parse agent response: {str(e)}. Raw: {response_text[:200]}",
                "confidence": 0.0,
                "sl": None, "tp": None, "volume": None
            }
        except Exception as e:
            return {
                "action": "DO_NOTHING",
                "reasoning": f"Agent error: {str(e)}",
                "confidence": 0.0,
                "sl": None, "tp": None, "volume": None
            }

    # Mock decision method removed for production/strict mode safety

    def _format_candles(self, candles: list) -> str:
        """Format candle data as a readable table."""
        lines = ["Time | Open | High | Low | Close | Volume"]
        for c in candles:
            t = datetime.fromtimestamp(c["time"]).strftime("%H:%M")
            lines.append(f"{t} | {c['open']:.2f} | {c['high']:.2f} | {c['low']:.2f} | {c['close']:.2f} | {c['volume']}")
        return "\n".join(lines)

    def _format_positions(self, positions: list) -> str:
        if not positions:
            return "No open positions."
        lines = []
        for p in positions:
            lines.append(
                f"Ticket #{p['ticket']}: {p['type'].upper()} {p['volume']} lots @ {p['price_open']:.2f} "
                f"→ Current: {p['price_current']:.2f} | P&L: ${p['profit']:.2f} | SL: {p['sl']} | TP: {p['tp']}"
            )
        return "\n".join(lines)

    def _format_history(self) -> str:
        if not self.decision_history:
            return "No previous decisions."
        recent = self.decision_history[-5:]
        lines = []
        for d in recent:
            lines.append(f"{d['time']}: {d['action']} (conf: {d['confidence']:.1%})")
        return "\n".join(lines)
