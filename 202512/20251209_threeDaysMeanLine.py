'''
Strategy:You are a slightly less stupid stockholder
You calculate the average price of the last 3 days
    If yesterday's price > SMA → today buy (trend up)
    if yesterday's price < SMA → today do not buy (trend down)
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

df['threeDaysMean'] = df['price'].rolling(window=3).mean()

# understand why the first is wrong?
# df['signalBuyOrNot'] = np.where(df['threeDaysMean'].shift(1)<df['price'],1,0)
df['signalBuyOrNot'] = np.where((df['threeDaysMean']<df['price']).shift(1),1,0)

df['threeDaysMeanGains'] = (1+df['incOrNot'] *df['signalBuyOrNot']).cumprod()-1
df['brainlessFixedInvestment'] = (1+df['incOrNot']).cumprod()-1
print(df)