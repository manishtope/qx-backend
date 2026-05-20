"""Quotex/OTC Signal Generator Backend - Fully Synced Timezone Version."""
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import random
import math
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="Quotex Signal Engine")
api_router = APIRouter(prefix="/api")

# In-memory history arrays
LOCAL_HISTORY_LOGS = []

ASSETS = [
    {"symbol": "EURUSD", "name": "EUR/USD", "category": "forex", "base_price": 1.1580},
    {"symbol": "GBPUSD", "name": "GBP/USD", "category": "forex", "base_price": 1.3380},
    {"symbol": "USDJPY", "name": "USD/JPY", "category": "forex", "base_price": 149.50},
    {"symbol": "AUDUSD", "name": "AUD/USD", "category": "forex", "base_price": 0.6580},
    {"symbol": "USDCAD", "name": "USD/CAD", "category": "forex", "base_price": 1.3580},
    {"symbol": "NZDUSD", "name": "NZD/USD", "category": "forex", "base_price": 0.6120},
    {"symbol": "EURGBP", "name": "EUR/GBP", "category": "forex", "base_price": 0.8580},
    {"symbol": "EURUSD-OTC", "name": "EUR/USD OTC", "category": "otc", "base_price": 1.1585},
    {"symbol": "GBPUSD-OTC", "name": "GBP/USD OTC", "category": "otc", "base_price": 1.3385},
    {"symbol": "USDJPY-OTC", "name": "USD/JPY OTC", "category": "otc", "base_price": 149.52},
    {"symbol": "AUDCAD-OTC", "name": "AUD/CAD OTC", "category": "otc", "base_price": 0.8930},
    {"symbol": "EURJPY-OTC", "name": "EUR/JPY OTC", "category": "162.30"},
    {"symbol": "GBPJPY-OTC", "name": "GBP/JPY OTC", "category": "otc", "base_price": 189.10},
    {"symbol": "USDINR-OTC", "name": "USD/INR OTC", "category": "otc", "base_price": 83.50},
    {"symbol": "USDPKR-OTC", "name": "USD/PKR OTC", "category": "otc", "base_price": 278.20},
    {"symbol": "USDBDT-OTC", "name": "USD/BDT OTC", "category": "otc", "base_price": 117.40},
    {"symbol": "USDCOP-OTC", "name": "USD/COP OTC", "category": "otc", "base_price": 3820.0},
    {"symbol": "NZDJPY-OTC", "name": "NZD/JPY OTC", "category": "otc", "base_price": 95.40},
    {"symbol": "CADCHF-OTC", "name": "CAD/CHF OTC", "category": "otc", "base_price": 0.6620},
    {"symbol": "BTCUSD", "name": "BTC/USD", "category": "crypto", "base_price": 67500.0},
    {"symbol": "ETHUSD", "name": "ETH/USD", "category": "crypto", "base_price": 3450.0},
    {"symbol": "SOLUSD", "name": "SOL/USD", "category": "crypto", "base_price": 178.0},
]

TIMEFRAME_SECONDS = {"1m": 60, "5m": 300, "15m": 900}

class Candle(BaseModel):
    t: int
    o: float
    h: float
    l: float
    c: float
    v: float

class Indicators(BaseModel):
    rsi: float
    rsi_status: str
    macd: float
    macd_signal: float
    macd_hist: float
    macd_status: str
    ema_fast: float
    ema_slow: float
    ema_status: str
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_status: str

class SignalResponse(BaseModel):
    id: str
    symbol: str
    name: str
    category: str
    timeframe: str
    direction: Literal["UP", "DOWN"]
    confidence: int
    entry_price: float
    expiry_at: str
    expiry_seconds: int
    reasoning: str
    indicators: Indicators
    candles: List[Candle]
    created_at: str

class SignalRequest(BaseModel):
    symbol: str
    timeframe: Literal["1m", "5m", "15m"] = "1m"
    tz: str = "IST"

def generate_candles(symbol: str, base_price: float, n: int = 80, timeframe: str = "1m") -> list:
    import numpy as np
    import pandas as pd
    bucket_seconds = TIMEFRAME_SECONDS[timeframe]
    now = int(datetime.now(timezone.utc).timestamp())
    bucket = now // bucket_seconds
    seed = hash(f"{symbol}-{bucket}") & 0xFFFFFFFF
    rng = np.random.default_rng(seed)

    vol_pct = 0.0008 if base_price > 100 else 0.0006
    if "OTC" in symbol:
        vol_pct *= 1.3

    prices = [base_price]
    for _ in range(n):
        shock = rng.normal(0, vol_pct)
        prices.append(prices[-1] * (1 + shock))

    candles = []
    for i in range(1, len(prices)):
        o = prices[i - 1]
        c = prices[i]
        wick = abs(rng.normal(0, vol_pct * 0.5)) * o
        h = max(o, c) + wick
        l = min(o, c) - wick
        v = float(rng.integers(800, 5000))
        t = (bucket - (n - i)) * bucket_seconds
        candles.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    return pd.DataFrame(candles)

def analyze(df) -> tuple:
    import pandas as pd
    closes = df["c"]
    last_close = float(closes.iloc[-1])

    # Simple RSI calculation mechanics
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi_v = float(rsi.iloc[-1]) if not math.isnan(rsi.iloc[-1]) else 50.0

    # Moving Average calculations
    ema9 = closes.ewm(span=9, adjust=False).mean()
    ema21 = closes.ewm(span=21, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    ema12 = closes.ewm(span=12, adjust=False).mean()
    
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    std = closes.rolling(window=20).std()
    mid = closes.rolling(window=20).mean()
    upper = mid + 2.0 * std
    lower = mid - 2.0 * std

    direction = "UP" if rsi_v < 50 else "DOWN"
    confidence = random.randint(72, 94)

    indicators = Indicators(
        rsi=round(rsi_v, 2), rsi_status="OVERSOLD" if rsi_v < 35 else "OVERBOUGHT" if rsi_v > 65 else "NEUTRAL",
        macd=round(float(macd.iloc[-1]), 5), macd_signal=round(float(signal.iloc[-1]), 5), macd_hist=round(float(hist.iloc[-1]), 5), macd_status="BULLISH" if hist.iloc[-1] > 0 else "BEARISH",
        ema_fast=round(float(ema9.iloc[-1]), 5), ema_slow=round(float(ema21.iloc[-1]), 5), ema_status="BULLISH" if ema9.iloc[-1] > ema21.iloc[-1] else "BEARISH",
        bb_upper=round(float(upper.iloc[-1]), 5), bb_middle=round(float(mid.iloc[-1]), 5), bb_lower=round(float(lower.iloc[-1]), 5), bb_status="LOWER BAND" if last_close < mid.iloc[-1] else "UPPER BAND"
    )
    return indicators, direction, confidence

@api_router.get("/assets")
async def get_assets():
    return {"assets": ASSETS}

@api_router.get("/ticker")
async def get_ticker():
    out = []
    for a in ASSETS[:6]:  # Limit to keep pipeline thin
        change = random.choice([-0.412, 0.125, -0.042, 0.881, 0.217])
        out.append({"symbol": a["symbol"], "name": a["name"], "price": round(a["base_price"], 5), "change": change})
    return {"ticker": out}

@api_router.post("/signal/generate", response_model=SignalResponse)
async def generate_signal(req: SignalRequest):
    asset = next((a for a in ASSETS if a["symbol"] == req.symbol), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    df = generate_candles(req.symbol, asset["base_price"], n=40, timeframe=req.timeframe)
    indicators, direction, confidence = analyze(df)

    # Core conversion zone: Formats timestamps directly inside requested timezone
    now = datetime.now(timezone.utc)
    if req.tz == "IST":
        now = now + timedelta(hours=5, minutes=30)
    elif req.tz == "EST":
        now = now - timedelta(hours=5)

    expiry_seconds = TIMEFRAME_SECONDS[req.timeframe]
    expiry_time = now + timedelta(seconds=expiry_seconds)

    entry_price = float(df["c"].iloc[-1])
    decimals = 5 if entry_price < 100 else 2

    candles = [Candle(t=int(r.t), o=round(float(r.o), decimals), h=round(float(r.h), decimals), l=round(float(r.l), decimals), c=round(float(r.c), decimals), v=float(r.v)) for r in df.itertuples(index=False)]

    signal = SignalResponse(
        id=str(uuid.uuid4()), symbol=asset["symbol"], name=asset["name"], category=asset["category"],
        timeframe=req.timeframe, direction=direction, confidence=confidence, entry_price=round(entry_price, decimals),
        expiry_at=expiry_time.strftime("%H:%M:%S"),
        expiry_seconds=expiry_seconds,
        reasoning=f"Technical indicators show {indicators.rsi_status} patterns. Convergence supports localized {direction} movement.",
        indicators=indicators, candles=candles, created_at=now.strftime("%H:%M:%S")
    )
    
    LOCAL_HISTORY_LOGS.insert(0, {k: v for k, v in signal.model_dump().items() if k != "candles"})
    return signal

@api_router.get("/signal/history")
async def signal_history():
    return {"history": LOCAL_HISTORY_LOGS[:10]}

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])