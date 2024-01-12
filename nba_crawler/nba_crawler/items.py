# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NbaCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class TeamItem(scrapy.Item):
    """球队基本信息
    """
    _table_name = 'tb_team'
    season = scrapy.Field() # 赛季
    team_name = scrapy.Field() # 全称
    team_short = scrapy.Field() # 简称
    logo = scrapy.Field()
    coach = scrapy.Field()
    coach_url = scrapy.Field() # url path
    executive = scrapy.Field() # 总经理
    executive_url = scrapy.Field() # url path
    arena = scrapy.Field() # 场馆
    attendance = scrapy.Field() # 观众人次
    

class TeamRosterItem(scrapy.Item):
    """球队球员名单(球员基本信息)
    """
    _table_name = 'tb_roster'
    number = scrapy.Field()
    player_url =scrapy.Field()
    player = scrapy.Field()
    positon = scrapy.Field()
    height = scrapy.Field()
    weight = scrapy.Field()
    birth_date = scrapy.Field()
    birth_country = scrapy.Field()
    exp = scrapy.Field()
    college = scrapy.Field()
    
class TeamInjuryItem(scrapy.Item):
    """球队伤病名单
    """
    _table_name = 'tb_injury'
    player = scrapy.Field() # 球员
    player_url = scrapy.Field() # 球员链接
    team_name = scrapy.Field() # 球队
    season = scrapy.Field() # 2023-24 赛季
    date = scrapy.Field() # 受伤日期
    description = scrapy.Field() # 详情
    
class TeamPerGame(scrapy.Item):
    """Roster球员-场均数据
    """
    _table_name = 'tb_team_per_game'
    player = scrapy.Field()
    player_url = scrapy.Field() #
    GS = scrapy.Field() # 首发场次
    G = scrapy.Field() # 场次
    MP = scrapy.Field() # 场均上场时间
    FG = scrapy.Field() # 命中数
    FGA = scrapy.Field() # 出手数
    FGPct = scrapy.Field() # 命中率
    ThreeP = scrapy.Field() # 3分
    ThreePA = scrapy.Field()
    ThreePPct = scrapy.Field()
    TwoP = scrapy.Field() # 2分
    TwoPA = scrapy.Field()
    TwoPPct = scrapy.Field()
    eFGPct = scrapy.Field() # 有效命中率
    FT = scrapy.Field() # 罚球
    FTA = scrapy.Field()
    FTPct = scrapy.Field()
    ORB = scrapy.Field()
    DRB = scrapy.Field()
    TRB = scrapy.Field()
    AST = scrapy.Field()
    STL = scrapy.Field()
    BLK = scrapy.Field() 
    TOV = scrapy.Field() # Turn over
    PF = scrapy.Field() # Personal Fouls
    PTS = scrapy.Field()