import scrapy
from scrapy.item import ItemMeta, Item
"""
篮球术语词汇表
https://www.basketball-reference.com/about/glossary.html
"""


class GameDetailItemMeta(ItemMeta):
    """Meta Class dynamicly create fields
    """
    def __new__(mcs, class_name, bases, attrs):
        _cls = super().__new__(mcs, class_name, bases, attrs)
        if class_name == 'GameDetailItem':
            # 进阶数据(Pct:估计)：
            _cls.fields['TS'] = scrapy.Field() # 真实命中率
            _cls.fields['eFGPct'] = scrapy.Field() # 有效命中率
            _cls.fields['ThreePAr'] = scrapy.Field() # 每次出手时，3分出手率
            _cls.fields['FTr'] = scrapy.Field() # 每次出手, 获得罚球率
            _cls.fields['ORBPct'] = scrapy.Field() # 在场时，获得进攻篮板率
            _cls.fields['DRBPct'] = scrapy.Field() # 在场时，获得进攻篮板率
            _cls.fields['TRBPct']= scrapy.Field() # 在场时，总篮板率
            _cls.fields['ASTPct'] = scrapy.Field() # 助功率
            _cls.fields['STLPct'] = scrapy.Field() # 抢断率
            _cls.fields['BLKPct'] = scrapy.Field() # 盖帽率
            _cls.fields['TOVPct'] = scrapy.Field() # 每百回合失误数
            _cls.fields['USGPct'] = scrapy.Field() # 球员使用率
            _cls.fields['ORtg'] = scrapy.Field() # 每百回合(球员/球队)得分
            _cls.fields['DRtg'] = scrapy.Field() # 每百回合(球员/球队)失分
            _cls.fields['BPM'] =  scrapy.Field() # 每百回合正负值(基于联盟平均水平)
        return _cls


class NBAItem(Item):
    _table_name = '' # sql table name
    _keys = [] # sql table keys for update or delete

class CommonItem(Item):
    """通用项: 区分每赛季各球员
    """
    season = scrapy.Field() # 赛季
    team = scrapy.Field() # 球队
    player = scrapy.Field()
    player_url = scrapy.Field() #

class PlayerCommonItem(Item):
    age = scrapy.Field()
    league = scrapy.Field()
    positions = scrapy.Field()
    is_playoff = scrapy.Field()


class BasicItem(NBAItem, CommonItem):
    """球员/球队基础数据
    """
    
    GS = scrapy.Field() # 首发场次
    G = scrapy.Field() # 场次
    
    FG = scrapy.Field() # 命中数
    FGA = scrapy.Field() # 出手数
    FGPct = scrapy.Field() # 命中率
    ThreeP = scrapy.Field() # 3分命中数
    ThreePA = scrapy.Field() # 3分出手数
    ThreePPct = scrapy.Field() # 3分命中率
    TwoP = scrapy.Field() # 2分命中
    TwoPA = scrapy.Field()
    TwoPPct = scrapy.Field()
    FT = scrapy.Field() # 罚球命中
    FTA = scrapy.Field() # 罚球出手
    FTPct = scrapy.Field() # 罚球命中率
    ORB = scrapy.Field() # 进攻篮板
    DRB = scrapy.Field() # 防守篮板
    TRB = scrapy.Field() # 总篮板
    AST = scrapy.Field() # 助攻
    STL = scrapy.Field() # 抢断
    BLK = scrapy.Field() # 盖帽
    TOV = scrapy.Field() # Turn over
    PF = scrapy.Field() # Personal Fouls
    PTS = scrapy.Field() # 得分




class PerGameItem(BasicItem):
    """场均数据(基础数据)
    """
    
    MP = scrapy.Field() # 场均上场时间
    eFGPct = scrapy.Field() # 有效命中率

  
class AdvanceItem(NBAItem, CommonItem):
    """球员/球队进阶数据
    """
   
    
    G = scrapy.Field() # 场次
    Total_MP = scrapy.Field() # 总上场时间 minutes play
    PER = scrapy.Field() # 效率评级(联盟平均值15)
    TS = scrapy.Field() # 真实命中率
    ThreePAr = scrapy.Field() # 每次出手时，3分出手率
    FTr = scrapy.Field() # 每次出手, 获得罚球率
    ORBPct = scrapy.Field() # 在场时，获得进攻篮板率
    DRBPct = scrapy.Field() # 在场时，获得进攻篮板率
    TRBPct= scrapy.Field() # 在场时，总篮板率
    ASTPct = scrapy.Field() # 助功率
    STLPct = scrapy.Field() # 抢断率
    BLKPct = scrapy.Field() # 盖帽率
    TOVPct = scrapy.Field() # 每百回合失误数
    USGPct = scrapy.Field() # 球员使用率
    OWS = scrapy.Field() # 进攻胜利贡献值
    DWS = scrapy.Field() # 防守胜利贡献值
    WS = scrapy.Field() # 胜利贡献值=进攻胜利贡献值+防守胜利贡献值
    WS_48 = scrapy.Field() # 估计:每48分钟胜利贡献值(联盟平均: .100)
    
    BPM =  scrapy.Field() # 每百回合球员/球队 正负值(基于联盟平均水平)
    OBPM = scrapy.Field() # 进攻BPM
    DBPM = scrapy.Field() # 防守BPM
    VORP =  scrapy.Field() # VORP -- Value over Replacement Player
    

class Per36MinsItem(BasicItem):
    """ 每36分钟基础数据
    """
    Total_MP = scrapy.Field(default='') # 总上场时间 minutes play


class Per100PossItem(BasicItem):
    """ 每百回合
    """
    
    Total_MP = scrapy.Field() # 总上场时间
    ORtg = scrapy.Field() # 每百回合(球员/球队)得分
    DRtg = scrapy.Field() # 每百回合(球员/球队)失分


class AdjustedShootingItem(NBAItem, CommonItem):
    """ 调整后出手统计
    """
    
    
    G = scrapy.Field() # 场次
    Total_MP = scrapy.Field() # 总上场时间 minutes play
    FGPct = scrapy.Field() # 命中率
    TwoPPct = scrapy.Field() # 2分命中率
    ThreePPct = scrapy.Field() # 3分命中率
    eFGPct = scrapy.Field() # 有效命中率
    FTPct = scrapy.Field() # 罚球命中率
    TS = scrapy.Field() # 真实命中率
    FTr = scrapy.Field() # 每次出手, 获得罚球率
    ThreePAr = scrapy.Field() # 每次出手时，3分出手率
    # 联盟平均
    league_FGPct = scrapy.Field() # 命中率
    league_TwoPPct = scrapy.Field() # 2分命中率
    league_ThreePPct = scrapy.Field() # 3分命中率
    league_eFGPct = scrapy.Field() # 有效命中率
    league_FTPct = scrapy.Field() # 罚球命中率
    league_TS = scrapy.Field() # 真实命中率
    league_FTr = scrapy.Field() # 每次出手, 获得罚球率
    league_ThreePAr = scrapy.Field() # 每次出手时，3分出手率
    # 调整后, 权重占比如：100*FG/league_FG(更直观对比联盟水平)
    adjusted_FGPct = scrapy.Field() # 命中率
    adjusted_TwoPPct = scrapy.Field() # 2分命中率
    adjusted_ThreePPct = scrapy.Field() # 3分命中率
    adjusted_eFGPct = scrapy.Field() # 有效命中率
    adjusted_FTPct = scrapy.Field() # 罚球命中率
    adjusted_TS = scrapy.Field() # 真实命中率
    adjusted_FTr = scrapy.Field() # 每次出手, 获得罚球率
    adjusted_ThreePAr = scrapy.Field() # 每次出手时，3分出手率
    
    FG_add = scrapy.Field() # 总出手比联盟平均值多多少分
    TS_add = scrapy.Field() # 真实命中率(所有投篮，包括罚球)比联盟平均值多多少分
    
    
class PlaybyPlayItem(NBAItem, CommonItem):
    """1997赛季开始才有统计
    场上表现: 球场位置, 在场落场对球队影响，badpass, 丢球, 造/被投射犯规 造/被进攻犯规， 被盖帽
    等
    """
    
    G = scrapy.Field() # 场次
    Total_MP = scrapy.Field() # 总上场时间 minutes play
    # 该球员场上各位置占比
    PG_pct = scrapy.Field() #
    SG_pct = scrapy.Field() #
    SF_pct = scrapy.Field() #
    PF_pct = scrapy.Field() #
    C_pct = scrapy.Field() #
    OnCourt_100poss = scrapy.Field() # 在场每百回合正负值
    OffCourt_100poss = scrapy.Field() # 不在场每百回合正负值
    TOV_BadPass = scrapy.Field() # 传球失误
    TOV_LostBall = scrapy.Field() # 丢球失误
    Foul_Shoot = scrapy.Field() # 投射犯规(被吹罚)
    Foul_Offensive = scrapy.Field() # 进攻犯规(被吹罚)
    FoulDrawn_Shoot = scrapy.Field() # 博得对方投射犯规
    FoulDrawn_Offensive = scrapy.Field() # 博得对方进攻犯规
    PointGenAst = scrapy.Field() # 助攻队友总得分
    And1 = scrapy.Field() # And one 次数
    BLKd = scrapy.Field() # 被封盖次数


class ShootingItem(NBAItem, CommonItem):
    """详细投篮数据，按距离以及各距离命中率
    """
    
    G = scrapy.Field() # 场次
    Total_MP = scrapy.Field() # 总上场时间 minutes play
    
    FGPct = scrapy.Field() # 命中率
    DistanceAvg = scrapy.Field() # 平均投射距离
    # % of FGA by Distance(英尺feet) 各距离出手占比总出手 
    Pct_FGA_Dist_2P = scrapy.Field() # 2 Point
    Pct_FGA_Dist_0_3 = scrapy.Field() # 0-3 feet
    Pct_FGA_Dist_3_10 = scrapy.Field() # 3-10 feet
    Pct_FGA_Dist_10_16 = scrapy.Field() # 10-16 feet
    Pct_FGA_Dist_16_3P = scrapy.Field() # 16-3 Point
    Pct_FGA_Dist_3P = scrapy.Field() # 3 Point
    
    # FG% by Distance 各距离命中率
    FGPct_Dist_2P = scrapy.Field()
    FGPct_Dist_0_3 = scrapy.Field()
    FGPct_Dist_3_10 = scrapy.Field()
    FGPct_Dist_10_16 = scrapy.Field()
    FGPct_Dist_16_3P = scrapy.Field()
    FGPct_Dist_3P = scrapy.Field()
    
    # % of FG Assisted 被助攻(吃饼)
    Pct_FG_Astd2P = scrapy.Field() # 2Point 受助攻率
    Pct_FG_Astd3P = scrapy.Field() # 3Point 受助攻率
    
    Pct_Dunk_FGA = scrapy.Field() # 扣篮占比
    Dunk_Make = scrapy.Field() # 扣篮次数
    
    Pct_Corner3_3FGA = scrapy.Field() # 底线三分占三分出手百分比
    Corner3_3FGPct = scrapy.Field() # 底线三分命中率
    
    # Heaves: 超过半场
    Heaves_Attempt = scrapy.Field() # 超过半场出手数
    Heaves_Make = scrapy.Field() # 超过半场命中数