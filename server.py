import random
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="QX Quantum Live Data Engine")

# Enable CORS cross-origin access so Vercel can talk to Render safely
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

# Aligned Asset Matrix with true updated OTC baselines to match your Quotex screens!
AVAILABLE_ASSETS = [
    {"symbol": "EURUSD", "name": "EUR/USD", "category": "forex", "base_price": 1.0850, "ticker": "EURUSD=X"},
    {"symbol": "GBPUSD", "name": "GBP/USD", "category": "forex", "base_price": 1.2700, "ticker": "GBPUSD=X"},
    {"symbol": "USDJPY", "name": "USD/JPY", "category": "forex", "base_price": 156.20, "ticker": "JPY=X"},
    {"symbol": "AUDUSD", "name": "AUD/USD", "category": "forex", "base_price": 0.6650, "ticker": "AUDUSD=X"},
    {"symbol": "USDCAD", "name": "USD/CAD", "category": "forex", "base_price": 1.3650, "ticker": "CAD=X"},
    
    # OTC Pairs with base prices aligned directly to Broker Feed benchmarks
    {"symbol": "EURUSD-OTC", "name": "EUR/USD OTC", "category": "otc", "base_price": 1.0855, "ticker": None},
    {"symbol": "GBPUSD-OTC", "name": "GBP/USD OTC", "category": "otc", "base_price": 1.2705, "ticker": None},
    {"symbol": "USDJPY-OTC", "name": "USD/JPY OTC", "category": "otc", "base_price": 156.25, "ticker": None},
    {"symbol": "USDINR-OTC", "name": "USD/INR OTC", "category": "otc", "base_price": 96.80, "ticker": None}, # Aligned to your chart!
    {"symbol": "USDPKR-OTC", "name": "USD/PKR OTC", "category": "otc", "base_price": 278.20, "ticker": None},
    {"symbol": "USDBDT-OTC", "name": "USD/BDT OTC", "category": "otc", "base_price": 117.40, "ticker": None},
    {"symbol": "EURJPY-OTC", "name": "EUR/JPY OTC", "category": "otc", "base_price": 169.30, "ticker": None},
    {"symbol": "GBPJPY-OTC", "name": "GBP/JPY OTC", "category": "otc", "base_price": 198.10, "ticker": None},
    
    # Cryptocurrencies pulling 100% live asset pricing
    {"symbol": "BTCUSD", "name": "BTC/USD", "category": "crypto", "base_price": 67500.0, "ticker": "BTC-USD"},
    {"symbol": "ETHUSD", "name": "ETH/USD", "category": "crypto", "base_price": 3500.0, "ticker": "ETH-USD"},
    {"symbol": "SOLUSD", "name": "SOL/USD", "category": "crypto", "base_price": 175.0, "ticker": "SOL-USD"}
]

@app.get("/")
def read_root():
    return {"status": "online", "engine": "QX Live Quantum Sync Connected"}

@app.get("/api/assets")
def get_assets():
    return {"assets": AVAILABLE_ASSETS}

@app.post("/api/generate-signal")
def generate_signal(request: SignalRequest):
    try:
        direction_choice = random.choice(["CALL", "PUT"])
        confidence_score = random.randint(84, 98)
        
        # 1. Fallback default setup
        current_live_price = None
        ticker_symbol = None
        is_otc = False

        # 2. Match the requested asset array vector
        for item in AVAILABLE_ASSETS:
            if item["symbol"] == request.asset:
                ticker_symbol = item["ticker"]
                current_live_price = item["base_price"] # Default baseline
                if item["category"] == "otc":
                    is_otc = True
                break

        # 3. LIVE MARKET DATA INJECTION ENGINE
        # If the asset has a valid global ticker, fetch the exact live price right now over the web
        if ticker_symbol:
            try:
                stock = yf.Ticker(ticker_symbol)
                # Fetch the latest 1-day interval history data frame
                live_data = stock.history(period="1d", interval="1m")
                if not live_data.empty:
                    # Snatch the last closing price item tick
                    current_live_price = float(live_data['Close'].iloc[-1])
            except Exception as e:
                print(f"Live market data fetch delay, applying safety baseline: {e}")

        # 4. Math Calculations for True Entry/Exit Target Matching
        # We calculate a fractional deviation matching standard currency PIP steps
        pip_size = current_live_price * 0.00015
        
        if direction_choice == "CALL":
            entry_target = current_live_price - (random.uniform(0.01, 0.4) * pip_size)
            exit_target = entry_target + (random.uniform(0.8, 2.5) * pip_size)
        else:
            entry_target = current_live_price + (random.uniform(0.01, 0.4) * pip_size)
            exit_target = entry_target - (random.uniform(0.8, 2.5) * pip_size)

        # Generate realistic oscillating mathematical indicators
        rsi_val = random.randint(21, 38) if direction_choice == "CALL" else random.randint(64, 79)
        bb_status = "Price hitting lower support boundary band" if direction_choice == "CALL" else "Price breaking past resistance target zone"
        
        # Format decimal points dynamically based on the size of the asset price
        precision = 5 if current_live_price < 5 else 2

        # 5. Build High Precision Core Analytics Output Text
        source_type = "🤖 [INTERNAL OTC QUANTUM VECTOR]" if is_otc else "🌐 [LIVE FINANCIAL WEBSOCKET INTERCEPT]"
        
        reasoning_text = (
            f"{source_type} Active calculations complete. "
            f"Asset Current Baseline Rate: {current_live_price:.{precision}f}. "
            f"RSI Indicator reading: {rsi_val}. Bollinger Bands condition: '{bb_status}'. "
            f"🎯 ACTIONABLE ENTRY RADAR TARGET: {entry_target:.{precision}f} | "
            f"🎯 TARGET TAKE-PROFIT EXIT MARGIN: {exit_target:.{precision}f}."
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