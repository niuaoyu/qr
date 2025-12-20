import rqdatac, pandas, datetime

rqdatac.init('15256832925','a1234567890')

rqdatac.get_price('000001.XSHE', start_date=20150101, end_date="2015-02-01")

rqdatac.get_price('000002.XSHE', start_date=pandas.Timestamp("20150101"), end_date=datetime.datetime(2015,2,1))