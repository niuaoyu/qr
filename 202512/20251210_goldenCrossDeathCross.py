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

# modified version
import numpy as np
import pandas as pd

price = [100, 102, 99, 97, 101, 105, 103, 108, 106, 110, 115, 112, 118, 120, 117]
day = [i for i in range(1,len(price)+1)]
df = pd.DataFrame({
    'day':day,
    'price':price
})

df['incOrNot'] = df['price'].pct_change()

df['AverageThreeDays'] = df['price'].rolling(window=3).mean()
df['AverageFiveDays'] = df['price'].rolling(window=5).mean()

golden_cross = (df['AverageThreeDays'] > df['AverageFiveDays'])*(
    df['AverageThreeDays'].shift(1) < df['AverageFiveDays'].shift(1)
)
death_cross = (df['AverageThreeDays'] < df['AverageFiveDays'])*(
    df['AverageThreeDays'].shift(1) > df['AverageFiveDays'].shift(1)
)

df['signalBuyOrNot'] = np.nan
df.loc[golden_cross,'signalBuyOrNot'] = 1
df.loc[death_cross,'signalBuyOrNot'] = 0
df['signalBuyOrNot'] = df['signalBuyOrNot'].ffill()

# The same day is counted as the same day, and the real market cannot be done, 
# why shift? Because the moving average can only be calculated at the close, it can only be bought at the opening of the next day.
# Only when the market closes today can we make tomorrow's judgment

'''
Suppose you are out of the market on a certain day (signalBuyOrNot is 0).
    The daily price change is 0.02 .
    Your calculation: (1 + 0.02) * 0 = 0.
    Consequence: Your funds for that day become 0.
Ultimate consequence: Because you are using cumulative multiplication, once a day is 0, 
multiplying all subsequent numbers by 0 will always result in 0. 
Your backtesting curve will plummet to the bottom.
'''
df['strategyGains'] = (1+(df['incOrNot'] *df['signalBuyOrNot'].shift(1))).cumprod()-1  
df['brainlessFixedInvestment'] = (1+df['incOrNot']).cumprod()-1
df= df.fillna(0)
print(df)



#--------------------------------------------------------------------------
# import numpy as np
# import pandas as pd

# price = [100, 102, 99, 97, 101, 105, 103, 108, 106, 110, 115, 112, 118, 120, 117]
# day = [i for i in range(1,len(price)+1)]
# df = pd.DataFrame({
#     'day':day,
#     'price':price
# })

# df['incOrNot'] = df['price'].pct_change().round(2)

# df['AverageThreeDays'] = df['price'].rolling(window=3).mean().round(2)
# df['AverageFiveDays'] = df['price'].rolling(window=5).mean().round(2)

# '''
# Start holding after the golden cross (1)
# Liquidation after a death cross (0)
# Other times it remains the same as yesterday
# '''

# df['signalBuyOrNot'] = 0
# for i in range(5,len(day)):
#     if df['AverageThreeDays'].iloc[i] > df['AverageFiveDays'].iloc[i]:
#         if df['AverageThreeDays'].iloc[i-1] < df['AverageFiveDays'].iloc[i-1]:
#             df['signalBuyOrNot'].iloc[i] = 1
#             continue
#     if df['AverageThreeDays'].iloc[i] < df['AverageFiveDays'].iloc[i]:
#         if df['AverageThreeDays'].iloc[i-1] > df['AverageFiveDays'].iloc[i-1]:
#             df['signalBuyOrNot'].iloc[i] = 0
#             continue
#     df['signalBuyOrNot'].iloc[i] = df['signalBuyOrNot'].iloc[i-1]
# # The same day is counted as the same day, and the real market cannot be done, 
# # why shift? Because the moving average can only be calculated at the close, it can only be bought at the opening of the next day.
# # Only when the market closes today can we make tomorrow's judgment
# df['strategyGains'] = ((1+df['incOrNot']) *df['signalBuyOrNot'].shift(1)).cumprod().round(2)-1  
# df['brainlessFixedInvestment'] = (1+df['incOrNot']).cumprod().round(2)-1
    
# print(df)


