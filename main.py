import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import re
import redis
birth_date =  date(1947, 4, 16)
today = date.today()
years = 0
days = 0
if birth_date.year < today.year:
    relative_age = relativedelta(today, birth_date)
    years = relative_age.years
    print(years)
    temp_date = date(birth_date.year + years, birth_date.month, birth_date.day)
    days = (today - temp_date).days
    print(days)

