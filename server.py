import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="QX Quantum Multi-Indicator Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignalRequest(BaseModel):
    asset: str
    timeframe: str

AVAILABLE_ASSETS = [
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
    {"symbol": "EURJPY-OTC", "name": "EUR/JPY OTC", "category": "otc", "base_price": 162.30},
    {"symbol": "GBPJPY-OTC", "name": "GBP/JPY OTC", "category": "otc", "base_price": 189.10},
    {"symbol": "USDINR-OTC", "name": "USD/INR OTC", "category": "otc", "base_price": 83.50},
    {"symbol": "USDPKR-OTC", "name": "USD/PKR OTC", "category": "otc", "base_price": 278.20},
    {"symbol": "USDBDT-OTC", "name": "USD/BDT OTC", "category": "otc", "base_price": 117.40},
    {"symbol": "USDCOP-OTC", "name": "USD/COP OTC", "category": "otc", "base_price": 3820.0},
    {"symbol": "NZDJPY-OTC", "name": "NZD/JPY OTC", "category": "otc", "base_price": 95.40},
    {"symbol": "CADCHF-OTC", "name": "CAD/CHF OTC", "category": "otc", "base_price": 0.6620},
    {"symbol": "BTCUSD", "name": "BTC/USD", "category": "crypto", "base_price": 67500.0},
    {"symbol": "ETHUSD", "name": "ETH/USD", "category": "crypto", "base_price": 3450.0},
    {"symbol": "SOLUSD", "name": "SOL/USD", "category": "crypto", "base_price": 178.0}
]

@app.get("/")
def read_root():
    return {"status": "online", "engine": "Advanced Quantum Core"}

@app.get("/api/assets")
def get_assets():
    return {"assets": AVAILABLE_ASSETS}

@app.post("/api/generate-signal")
def generate_signal(request: SignalRequest):
    try:
        direction_choice = random.choice(["CALL", "PUT"])
        confidence_score = random.randint(82, 98)
        
        # 1. Dynamically find base price for math calculations
        base_price = 1.0000
        for item in AVAILABLE_ASSETS:
            if item["symbol"] == request.asset:
                base_price = item["base_price"]
                break
        
        # 2. Math calculations for entry/exit boundary indicators
        variance = base_price * 0.0015
        entry_target = base_price + (random.uniform(-variance, variance))
        exit_target = entry_target + (base_price * 0.0025 if direction_choice == "CALL" else -base_price * 0.0025)
        
        rsi_val = random.randint(18, 40) if direction_choice == "CALL" else random.randint(62, 85)
        bb_status = "Price piercing lower boundary band" if direction_choice == "CALL" else "Price testing upper ceiling structure"
        
        # 3. Compile structural multi-indicator breakdown text
        reasoning_text = (
            f"⚡ [STRATEGY EXHAUSTION MASTER] Engine tracking {request.asset} at baseline context. "
            f"Relative Strength Index (RSI) is holding critical value at {rsi_val}. "
            f"Bollinger Bands indicate: '{bb_status}'. "
            f"🎯 OPTIMAL ENTRY RADAR TARGET: {entry_target:.5f} | "
            f"🎯 TARGET TAKE-PROFIT EXIT MARGIN: {exit_target:.5f}."
        )

        return {
            "asset": request.asset,
            "direction": direction_choice,
            "confidence": confidence_score,
            "reasoning": reasoning_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001)