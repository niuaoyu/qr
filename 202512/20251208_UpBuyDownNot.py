# Strategy: Buy if it went up yesterday, don’t buy if it fell yesterday

'''
In the beginning stages of Vectorized Backtesting, we usually default to the "Full warehouse study" model.
Let's say you have $1 in capital.
    buyOrNot = 1: This means that you bought all of this $1 (or all of your current assets) into stocks. Your assets fluctuate with the stock.
    buyOrNot = 0: means you sold all your stocks and held your cash position. Your equity fluctuates to 0.
So you don't need to obsess about "did you buy 100 or 200 shares". What you are looking at is the change in "Net Value".
'''

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


# df['strategyGains'] = (df['incOrDec'] * df['buyOrNot'])
'''
Rates of return cannot be directly added together (cumsum)! This is a classic trap of simple interest thinking.
Example: You have 100 yuan.
    On the first day, the return increases by 50%, becoming 150 yuan.
    On the second day, the return decreases by 50%, resulting in 150 * 0.5 = 75 yuan.
    The actual result: You lost 25 yuan.(100*(1+0.5)*(1-0.5) = 75)
    Your calculation: +0.50 + (-0.50) = 0. Your calculation shows you neither gained nor lost.
Corrected logic: Compound interest. The formula is (1 + daily rate of return) * (yesterday's net value). 
'''
df['strategyNetValue'] = (1+df['incOrDec'] * df['buyOrNot'].fillna(0)).cumprod() - 1
df['brainlessFixedInvestment'] = (1+df['incOrDec']).cumprod() - 1

print(df)


