# Mean Reversion: Betting that if it falls too much, it will rise, and if it rises too much, it will fall (catching a falling knife).
'''
Indicator Calculation:
    Middle Band: Average closing price over the past 20 days.
    Standard Deviation: Standard deviation of closing prices over the past 20 days.
    Upper Band: Middle Band + 2 standard deviations.
    Lower Band: Middle Band - 2 standard deviations.

Trading Signals:
    Buy (Entry): When yesterday's closing price < yesterday's lower band. (The price has fallen too much; buy the dip.)
    Sell/Exit (Exit): When yesterday's closing price > yesterday's upper band. (The price has risen too much; exit.)
    Hold: If in the middle range, maintain the previous position.
'''

import numpy as np
import pandas as pd
csv_path = r'C:\Users\nay\Desktop\qr\qr\data\000300.XSHG_250101_251213_days.csv'
df = pd.read_csv(csv_path).loc[:,['date','prev_close']] 
'''
           date  prev_close
0    2025-01-02   3934.9109
1    2025-01-03   3820.3952
2    2025-01-06   3775.1648
3    2025-01-07   3768.9697
4    2025-01-08   3796.1055
..          ...         ...
225  2025-12-08   4584.5368
226  2025-12-09   4621.7545
227  2025-12-10   4598.2232
228  2025-12-11   4591.8273
229  2025-12-12   4552.1848

[230 rows x 2 columns]
'''

df['mean20'] = df['prev_close'].rolling(window=20).mean()
df['std20'] = df['prev_close'].rolling(window=20).std()
df['upper'] = df['mean20'] + 2 * df['std20']
df['lower'] = df['mean20'] - 2 * df['std20']
# 1 buy 0 sell 
entry_event  = (df['prev_close'] < (df['lower'])).fillna(False).astype(bool)
exit_event = (df['prev_close'] > (df['upper'])).fillna(False).astype(bool)
pos = pd.Series(np.nan,index=df.index)
pos[entry_event] = 1
pos[exit_event] = 0
df['position'] = pos.ffill().fillna(0).astype(int)

df['incOrNot'] = df['prev_close'].pct_change()

# position: yesterday buy or sell signal;incOrNot:today's earn or loss's percentage 
df['strategyGains'] = (1+(df['incOrNot'].shift(-1).fillna(0) * df['position'])).cumprod()-1  
df['brainlessFixedInvestment'] = (1+df['incOrNot']).cumprod()-1
print(df)