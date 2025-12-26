
import yfinance as yf
from datetime import datetime, timedelta

def test_symbol(symbol):
    print(f"Testing {symbol}...")
    try:
        df = yf.download(symbol, period="1mo", progress=False)
        if not df.empty:
            print(f"  ✓ Success! {len(df)} records. Last: {df['Close'].iloc[-1]}")
            return True
        else:
            print("  ✗ Empty dataframe.")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

print("Checking Spot Symbols...")
candidates = ["XPT-USD", "XPTUSD=X", "PL=F", "XPD-USD", "XPDUSD=X", "PA=F"]

for s in candidates:
    test_symbol(s)
