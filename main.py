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


with open('D:\\Projects\\PersonProject\\NBASpirder\\nba_crawler\\logs\\nba_crawler\\TeamSpider\\08f5f783c73711ee84416c5d3a062bef.log', 'r') as f:
    s = f.read()
    mt = re.search(r'(?s:.*)ProcessStatus\:response\:(\d+), request\:(\d+)', s)
    if mt:
        print(eval(mt.groups()[0]+ '/' + mt.groups()[1]) * 100)
    