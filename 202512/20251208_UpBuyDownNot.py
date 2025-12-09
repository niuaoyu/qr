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
df['incOrDec'] = df['price'].pct_change().round(2)

# Strategy: 
#   It rose yesterday (increase or decrease > 0), buy today (signal = 1)
#   It fell yesterday (increase or decrease <0), so I won’t buy it today (signal = 0)
df['buyOrNot'] = np.where(df['incOrDec'].shift(1)>0,1,0)

# Gains and Losses: 
# If I hold it today (signal=1), my profit = today’s increase or decrease
# If I take a short position today (signal=0), my profit = 0
df['strategyGains'] = (df['incOrDec'] * df['buyOrNot']).cumsum().round(2)
df['brainlessFixedInvestment'] = df['incOrDec'].cumsum().round(2)

print(df)
'''
0    1    100       NaN         0            NaN                       NaN
1    2    102      0.02         0           0.00                      0.02
2    3    101     -0.01         1          -0.01                      0.01
3    4    105      0.04         0          -0.01                      0.05
4    5    103     -0.02         1          -0.03                      0.03
5    6    108      0.05         0          -0.03                      0.08
6    7    107     -0.01         1          -0.04                      0.07
7    8    110      0.03         0          -0.04                      0.10
8    9    112      0.02         1          -0.02                      0.12
9   10    109     -0.03         1          -0.05                      0.09
'''


