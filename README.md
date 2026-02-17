## Gemini 3 Flash AI Trading Platform - Walkthrough

This guide explains how to run and use the autonomous AI trading platform powered by Gemini 3 Flash.

## Prerequisites
- Python 3.10+ (with .venv activated)
- Node.js 18+
- MetaTrader 5 Terminal (installed and running)

## 1. Configuration

Ensure your .env file in backend/ has the correct credentials:

```ini
MT5_LOGIN=YOUR_ID
MT5_PASSWORD=YOUR_PASSWORD
MT5_SERVER=YOUR_SERVER
GEMINI_API_KEY=YOUR_KEY
ACCOUNT_MODE=demo
```

## 2. Starting the Platform

**Backend (Python API + Agent)**

Open a terminal in `backend/` and run:

```bash
# Activate venv if needed
.venv\Scripts\activate

#locate
cd backend

#launch backend
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0


```

use backend because thats the directory name

> You should see: Uvicorn running on http://0.0.0.0:8000


**Frontend (User Interface)**

Open a new terminal in frontend/ and run:

```bash
#locate
cd frontend_react

#launch frontend
npm run dev
```

> You should see: Ready in ... at http://localhost:3000

## 3. Using the Platform
Open the App: Navigate to http://localhost:3000.
Connection Status: Check the top header. You should see "CONNECTED" (green).
If "DISCONNECTED", ensure the backend is running and MT5 is open.
Start the Agent:
Click the START button in the "Gemini Agent" panel.
The AI reasoning sidebar will start streaming "thoughts" from Gemini 3 Flash.
The agent will analyze the custom chart ticks and candles.
Manual Trading:
Use the BUY / SELL buttons to place trades manually.
Set Volume, SL, and TP before trading.
Open positions appear in the bottom panel.
## 4. Verification & Troubleshooting
Backend Health Check: Visit http://localhost:8000/api/health. It should return {"status": "online", "mt5_connected": true, ...}.
MT5 Connection: If the bridge fails to connect, ensure "Algo Trading" is enabled in MT5 and the credentials are correct. The backlog will show Connected to MT5.
Gemini API: If the agent is silent or errors, check your GEMINI_API_KEY.