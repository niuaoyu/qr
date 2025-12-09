'''
Double moving average strategy (golden cross death cross)
Strategy:
    You count the short-term moving average (3 days) and the long-term moving average (5 days)
        Short-term upside long-term → buy signal (golden cross: the trend is just rising)
        Short-term breakdown long-term → sell signal (death cross: the trend is coming to an end)

    What is "top-on"
        1. Yesterday: Short-term moving average < Long-term moving average 
        2. Today: Short-term moving average > long-term moving average
        Both conditions are met at the same time = golden cross occurs

''' 

import numpy as np
import pandas as pd

price = [100, 102, 99, 97, 101, 105, 103, 108, 106, 110, 115, 112, 118, 120, 117]
day = [i for i in range(1,len(price)+1)]
df = pd.DataFrame({
    'day':day,
    'price':price
})

df['incOrNot'] = df['price'].pct_change().round(2)

df['AverageThreeDays'] = df['price'].rolling(window=3).mean().round(2)
df['AverageFiveDays'] = df['price'].rolling(window=5).mean().round(2)

'''
Start holding after the golden cross (1)
Liquidation after a death cross (0)
Other times it remains the same as yesterday
'''

df['signalBuyOrNot'] = 0
for i in range(5,len(day)):
    if df['AverageThreeDays'].iloc[i] > df['AverageFiveDays'].iloc[i]:
        if df['AverageThreeDays'].iloc[i-1] < df['AverageFiveDays'].iloc[i-1]:
            df['signalBuyOrNot'].iloc[i] = 1
            continue
    if df['AverageThreeDays'].iloc[i] < df['AverageFiveDays'].iloc[i]:
        if df['AverageThreeDays'].iloc[i-1] > df['AverageFiveDays'].iloc[i-1]:
            df['signalBuyOrNot'].iloc[i] = 0
            continue
    df['signalBuyOrNot'].iloc[i] = df['signalBuyOrNot'].iloc[i-1]
# The same day is counted as the same day, and the real market cannot be done, 
# why shift? Because the moving average can only be calculated at the close, it can only be bought at the opening of the next day.
# Only when the market closes today can we make tomorrow's judgment
df['strategyGains'] = (df['incOrNot'] *df['signalBuyOrNot'].shift(1)).cumsum().round(2)  
df['brainlessFixedInvestment'] = df['incOrNot'].cumsum().round(2)
    
print(df)
# '''
#     day  price  incOrNot  AverageThreeDays  AverageFiveDays  signalBuyOrNot  strategyGains  brainlessFixedInvestment
# 0     1    100       NaN               NaN              NaN               0            NaN                       NaN
# 1     2    102      0.02               NaN              NaN               0           0.00                      0.02
# 2     3     99     -0.03            100.33              NaN               0          -0.00                     -0.01
# 3     4     97     -0.02             99.33              NaN               0          -0.00                     -0.03
# 4     5    101      0.04             99.00             99.8               0           0.00                      0.01
# 5     6    105      0.04            101.00            100.8               1           0.04                      0.05
# 6     7    103     -0.02            103.00            101.0               1          -0.02                      0.03
# 7     8    108      0.05            105.33            102.8               1           0.05                      0.08
# 8     9    106     -0.02            105.67            104.6               1          -0.02                      0.06
# 9    10    110      0.04            108.00            106.4               1           0.04                      0.10
# 10   11    115      0.05            110.33            108.4               1           0.05                      0.15
# 11   12    112     -0.03            112.33            110.2               1          -0.03                      0.12
# 12   13    118      0.05            115.00            112.2               1           0.05                      0.17
# 13   14    120      0.02            116.67            115.0               1           0.02                      0.19
# 14   15    117     -0.03            118.33            116.4               1          -0.03                      0.16
# '''

