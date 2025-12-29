import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()
symbol = 'PLJ2026'

print(f"Fetching {symbol} with n_bars=2500...")
try:
    df = tv.get_hist(symbol=symbol, exchange='NYMEX', interval=Interval.in_1_minute, n_bars=2500)
    if df is not None:
        print(f"Total rows: {len(df)}")
        # Check price at 11:30
        target_time = '2025-12-29 11:30'
        near_rows = df.loc[df.index.strftime('%Y-%m-%d %H:%M') == target_time]
        if not near_rows.empty:
            print(f"Price at {target_time}: {near_rows.iloc[0]['close']}")
        else:
            print(f"No data exactly at {target_time}, checking nearby...")
            # print surrounding rows
            mask = (df.index.hour == 11) & (df.index.minute >= 25) & (df.index.minute <= 35) & (df.index.day == 29)
            print(df[mask])
            
        print("Last 5 rows:")
        print(df.tail(5))
        print(f"Last Price: {last_price}")
    else:
        print("Data is None")
except Exception as e:
    print(f"Error: {e}")
