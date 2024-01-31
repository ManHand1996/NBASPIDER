from scrapy.loader import ItemLoader
from dateutil.parser import parse, ParserError
from itemloaders.processors import Identity, TakeFirst, Compose
from datetime import datetime
from pandas import NA
# Q: quater, H: half
QUATER = ['H1','H2','Q1','Q2', 'Q3', 'Q4', 'OT1', 'OT2', 
          'OT3','OT4','OT5','OT6', 'OT7', 'OT8']

def quater_input(val: str):
    if val.upper() in QUATER:
        return val.upper()
    else:
        return str(NA)

def datetime_output(val):
    try:
        # print('date_input', val)
        return parse(val).strftime('%Y-%m-%d %H:%M:%S')
    except ParserError:
        return str(NA)

def date_output(val):
    try:
        # print('date_input', val)
        return parse(val).strftime('%Y-%m-%d')
    except ParserError:
        return str(NA)

def number_input(val):
    symbol = val[0]
    try:
        new_val = float(val[1:])
        if symbol in '-+':
            return -new_val if symbol == '-' else new_val
        else:
            return float(val[1:])
    except ValueError:
        return 0

def country_ISOCODE(val):
    try:
        vals = val.split(' ')
        vals[-1] = vals[-1].upper()
        return ' '.join(vals)
    except (IndexError, AttributeError):
        return val

class NBAItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
    default_input_processor = TakeFirst()
    
    
    
class GameItemLoader(NBAItemLoader):
    """比赛详细GameDetailQuaterItem 与 GameBasicItem比赛基本信息
    """
    default_output_processor = TakeFirst()
    default_input_processor = TakeFirst()
    
    date_in = TakeFirst()
    date_out = Compose(TakeFirst(), datetime_output)
    quater_out = Compose(TakeFirst(), quater_input)
    PM_out = Compose(TakeFirst(), number_input)


class PlayerItemLoader(NBAItemLoader):
    default_output_processor = TakeFirst()
    default_input_processor = TakeFirst()
    
    birth_date_out = Compose(TakeFirst(), date_output)
    born_loc_out = Compose(TakeFirst(), country_ISOCODE)