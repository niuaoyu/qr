# Strategy: Buy if it went up yesterday, don’t buy if it fell yesterday

import numpy as np
import pandas as pd

fakeData = [100, 102, 101, 105, 103, 108, 107, 110, 112, 109]
day = [i for i in range(1,len(fakeData)+1)]
df = pd.DataFrame({
    "day":day,
    "price":fakeData
})

# Increase or decrease = (Today's price - Yesterday's price) / Yesterday's price
df['incOrDec'] = df['price'].pct_change()

# Strategy: 
#   It rose yesterday (increase or decrease > 0), buy today (signal = 1)
#   It fell yesterday (increase or decrease <0), so I won’t buy it today (signal = 0)
df['buyOrNot'] = np.where(df['incOrDec'].shift(1)>0,1,0)

# Gains and Losses: 
# If I hold it today (signal=1), my profit = today’s increase or decrease
# If I take a short position today (signal=0), my profit = 0

df['strategyGains'] = df['incOrDec'] * df['buyOrNot']
df['brainlessFixedInvestment'] = df['incOrDec'].cumsum()

print(df)
'''
   day  price  incOrDec  buyOrNot  strategyGains  brainlessFixedInvestment
0    1    100       NaN         0            NaN                       NaN
1    2    102  0.020000         0       0.000000                  0.020000
2    3    101 -0.009804         1      -0.009804                  0.010196
3    4    105  0.039604         0       0.000000                  0.049800
4    5    103 -0.019048         1      -0.019048                  0.030752
5    6    108  0.048544         0       0.000000                  0.079296
6    7    107 -0.009259         1      -0.009259                  0.070037
7    8    110  0.028037         0       0.000000                  0.098074
8    9    112  0.018182         1       0.018182                  0.116256
9   10    109 -0.026786         1      -0.026786                  0.089470
'''


