# This is a simplified version of  "Turtle Trading Rules." 
# The price hitting a new high indicates a powerful upward force; don't be afraid of heights, follow the trend. 

'''
Indicator Calculation:
    Past N-Day High (Donchian High): The highest price in the past 20 days (excluding today).
    Past N-Day Low (Donchian Low): The lowest price in the past 10 days (excluding today).
    Note: This is intentionally presented using different timeframes: 20-day for buying and 10-day for selling.

Trading Signal:
    Buy: Yesterday's closing price > Yesterday's calculated 20-day high.
    Sell/Short: Yesterday's closing price < Yesterday's calculated 10-day low.
    Hold: The intermediate state remains unchanged.
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

df['max20'] = df['prev_close'].shift(1).rolling(window=20).max() # .shift(1) -->  not today
df['min10'] = df['prev_close'].shift(1).rolling(window=10).min()

# 1 buy 0 sell 
entry_event  = (df['prev_close'] > (df['max20'])).fillna(False).astype(bool)
exit_event = (df['prev_close'] < (df['min10'])).fillna(False).astype(bool)
pos = pd.Series(np.nan,index=df.index)
pos[entry_event] = 1
pos[exit_event] = 0
df['position'] = pos.ffill().fillna(0).astype(int)
# print((df['position']==1).sum())
df['incOrNot'] = df['prev_close'].pct_change()

df['strategyGains'] = (1+(df['incOrNot'].shift(-1).fillna(0) *df['position'])).cumprod()-1  
df['brainlessFixedInvestment'] = (1+df['incOrNot']).cumprod()-1
print(df)