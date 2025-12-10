'''
Double moving average strategy (golden cross death cross)
Strategy:
    You count the short-term moving average (3 days) and the long-term moving average (5 days)
        Short-term upside long-term → buy signal (golden cross: the trend is just rising)
        Short-term breakdown long-term → sell signal (death cross: the trend is coming to an end)
        Add a rule: if the loss exceeds 5%, force selling

    What is "top-on"
        1. Yesterday: Short-term moving average < Long-term moving average 
        2. Today: Short-term moving average > long-term moving average
        Both conditions are met at the same time = golden cross occurs

''' 

import numpy as np
import pandas as pd

price = [100, 100.6, 101.4, 101.8, 102.3, 102.9, 103.5, 104.0, 104.8, 105.5, 106.1, 106.7, 107.2, 107.9, 108.4, 109.2, 109.8, 
         110.3, 110.9, 111.6, 113.8, 111.9, 114.2, 112.4, 116.8, 115.1, 118.3, 116.7, 120.0, 118.2, 121.7, 120.0, 123.6, 121.9, 
         125.4, 123.6, 127.1, 125.3, 128.9, 127.0, 122.0, 117.0, 112.0, 107.0, 102.0, 97.0, 92.0, 87.0, 82.0, 90.0, 85.5, 94.5,
           90.0, 99.0, 94.5, 103.5, 99.0, 108.0, 103.5, 112.5, 108.0, 117.0, 112.5, 121.5, 117.0, 126.0, 121.5, 130.5, 126.0, 
           135.0, 130.5, 139.5, 135.0, 144.0, 139.5, 148.5, 144.0, 153.0]
day = [i for i in range(1,len(price)+1)]
df = pd.DataFrame({
    'day':day,
    'price':price
})

df['incOrNot'] = df['price'].pct_change().round(2)

df['AverageThreeDays'] = df['price'].rolling(window=3).mean().round(2)
df['AverageFiveDays'] = df['price'].rolling(window=5).mean().round(2)

golden_cross = (df['AverageThreeDays'] > df['AverageFiveDays'])*(
    df['AverageThreeDays'].shift(1) < df['AverageFiveDays'].shift(1)
)
lossFivePercentAfterGoldenCross = df['incOrNot']<=-0.05
death_cross = (df['AverageThreeDays'] < df['AverageFiveDays'])*(
    df['AverageThreeDays'].shift(1) > df['AverageFiveDays'].shift(1)
)

df['signalBuyOrNot'] = pd.Series(index=df.index, dtype=int)
df.loc[golden_cross,'signalBuyOrNot'] = 1
df.loc[lossFivePercentAfterGoldenCross,'signalBuyOrNot'] = 0
df.loc[death_cross,'signalBuyOrNot'] = 0
df['signalBuyOrNot'] = df['signalBuyOrNot'].fillna(method='pad',axis=0) # Maintaining the golden and dead crosses

# Add a rule: if the loss exceeds 5%, force selling


# The same day is counted as the same day, and the real market cannot be done, 
# why shift? Because the moving average can only be calculated at the close, it can only be bought at the opening of the next day.
# Only when the market closes today can we make tomorrow's judgment
df['strategyGains'] = (df['incOrNot'] *df['signalBuyOrNot'].shift(1)).cumsum().round(2)  
df['brainlessFixedInvestment'] = df['incOrNot'].cumsum().round(2)
    
print(df)





