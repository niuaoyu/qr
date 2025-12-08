'''
Strategy:You are a slightly less stupid stockholder
You calculate the average price of the last 3 days
    If today's price > SMA → BUY (trend up)
    if today's price < SMA → do not buy (trend down)
A little smarter than the last strategy: don't look at single days up or down, look at the trend.
'''
import numpy as np
import pandas as pd

price = [100, 102, 99, 97, 101, 105, 103, 108, 106, 110, 115, 112]
day = [i for i in range(1,len(price)+1)]

df = pd.DataFrame({
    'day':day,
    'price':price
})
df['incOrNot'] = df['price'].pct_change()

df['threeDaysMean'] = df['price'].rolling(window=3).mean().round(2)
df['signalBuyOrNot'] = np.where(df['threeDaysMean'].shift(1)<df['price'],1,0)

df['threeDaysMeanGains'] = (df['incOrNot'] *df['signalBuyOrNot']).round(2)
df['brainlessFixedInvestment'] = df['incOrNot'].cumsum().round(2)
print(df)
'''
    day  price  incOrNot  threeDaysMean  signalBuyOrNot  threeDaysMeanGains  brainlessFixedInvestment
0     1    100       NaN            NaN               0                 NaN                       NaN
1     2    102  0.020000            NaN               0                0.00                      0.02
2     3     99 -0.029412         100.33               0               -0.00                     -0.01
3     4     97 -0.020202          99.33               0               -0.00                     -0.03
4     5    101  0.041237          99.00               1                0.04                      0.01
5     6    105  0.039604         101.00               1                0.04                      0.05
6     7    103 -0.019048         103.00               1               -0.02                      0.03
7     8    108  0.048544         105.33               1                0.05                      0.08
8     9    106 -0.018519         105.67               1               -0.02                      0.06
9    10    110  0.037736         108.00               1                0.04                      0.10
10   11    115  0.045455         110.33               1                0.05                      0.15
11   12    112 -0.026087         112.33               1               -0.03                      0.12
'''