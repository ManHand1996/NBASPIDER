# # Define here the models for your scraped items
# #
# # See documentation in:
# # https://docs.scrapy.org/en/latest/topics/items.html


import scrapy
import sys
try:
    from nba_crawler.utils.baseitem import NBAItem, GameDetailItemMeta
    from nba_crawler.utils.baseitem import PlayerCommonItem, PerGameItem, AdvanceItem
    from nba_crawler.utils.baseitem import Per100PossItem, AdjustedShootingItem
    from nba_crawler.utils.baseitem import ShootingItem, PlaybyPlayItem, Per36MinsItem
except ModuleNotFoundError:
    from nba_crawler.nba_crawler.utils.baseitem import NBAItem, GameDetailItemMeta
    from nba_crawler.nba_crawler.utils.baseitem import PlayerCommonItem, PerGameItem, AdvanceItem
    from nba_crawler.nba_crawler.utils.baseitem import Per100PossItem, AdjustedShootingItem
    from nba_crawler.nba_crawler.utils.baseitem import ShootingItem, PlaybyPlayItem, Per36MinsItem
# class TestTeamItem(scrapy.Item):
#     pass


class TeamItem(NBAItem):
    """球队基本信息
    """
    _table_name = 'tb_team'
    _keys = ['season', 'team']
    season = scrapy.Field() # 赛季
    team = scrapy.Field() # 全称
    team_short = scrapy.Field() # 简称
    rank = scrapy.Field() # 排名
    conference = scrapy.Field() # 分区
    logo = scrapy.Field()
    coach = scrapy.Field()
    executive = scrapy.Field() # 总经理
    arena = scrapy.Field() # 场馆
    attendance = scrapy.Field() # 观众人次
    record = scrapy.Field() # 战绩
    pts_g = scrapy.Field() # 场均得分
    opp_pts_g = scrapy.Field() # 场均失分
    src = scrapy.Field() # 球队评级
    pace = scrapy.Field() # 节奏系数(控球/48min)
    off_rtg = scrapy.Field() # 进攻评级
    def_rtg = scrapy.Field() # 防守评级
    net_rtg = scrapy.Field() # (攻防)净评级
    expected_W_L = scrapy.Field() # 预期战绩
    last_game =  scrapy.Field(default='')
    next_game =  scrapy.Field(default='')
    preseason_odds = scrapy.Field(default='') # 赛季前赔率

class TeamRosterItem(NBAItem):
    """球队球员名单(球员基本信息)
    """
    _table_name = 'tb_roster'
    _keys = ['season', 'player_url']
    season = scrapy.Field() # 2023-24 赛季
    team = scrapy.Field() # 球队
    
    number = scrapy.Field()
    player_url =scrapy.Field()
    player = scrapy.Field()
    position = scrapy.Field()
    height = scrapy.Field() # 身高(英尺)
    weight = scrapy.Field() # 体重(磅)
    birth_date = scrapy.Field()
    birth_country = scrapy.Field()
    exp = scrapy.Field()
    college = scrapy.Field()
    
class TeamInjuryItem(NBAItem):
    """球队伤病名单
    """
    _table_name = 'tb_injury'
    _keys = ['season', 'player_url']
    season = scrapy.Field() # 赛季
    team = scrapy.Field() # 球队
    player = scrapy.Field() # 球员
    player_url = scrapy.Field() # 球员链接
    date = scrapy.Field() # 受伤日期
    description = scrapy.Field() # 详情
    
class TeamPerGame(PerGameItem):
    """Roster球员-场均数据(基础)
    """
    _table_name = 'tb_team_per_game'
    _keys = ['season', 'player_url']
    
    
    
class GameScheduleItem(NBAItem):
    """赛程
    """
    _table_name = 'tb_game'
    _keys = ['game_id',]
    game_id = scrapy.Field() # 比赛url 除去.html(202305010BOS)
    season = scrapy.Field() # 赛季
    visitor = scrapy.Field() # 客队
    home = scrapy.Field() # 主队
    visitor_pts = scrapy.Field()
    home_pts = scrapy.Field()
    arena = scrapy.Field() # 球馆
    attendance = scrapy.Field() # 观众人次
    date = scrapy.Field() # 日期
    note = scrapy.Field() # 备注
    is_playoff = scrapy.Field(default=False) # 是否季后赛
    playoff_conference = scrapy.Field(default='') # 季后赛分区(Eastern|Western|Finals)
    playoff_round = scrapy.Field(default='') # 季后赛轮次(First Round|Semifinals|Finals|None)
    playoff_game = scrapy.Field(default='') # 该轮第N场比赛


class GameDetailItem(NBAItem, metaclass=GameDetailItemMeta):
    """每场比赛详细数据: total
    """
    _table_name = 'tb_game_detail'
    _keys = ['game_id', 'player']
    
    game_id = scrapy.Field() # 比赛url 除去.html(202305010BOS)
    
    date = scrapy.Field()
    
    season = scrapy.Field() # 赛季
    team = scrapy.Field()
    player = scrapy.Field() # 球员
    player_url = scrapy.Field() # 球员链接
    is_started = scrapy.Field() # 是否首发
    MP = scrapy.Field() # 场均上场时间
    FG = scrapy.Field() # 命中数
    FGA = scrapy.Field() # 出手数
    FGPct = scrapy.Field() # 命中率
    ThreeP = scrapy.Field() # 3分
    ThreePA = scrapy.Field()
    ThreePPct = scrapy.Field()
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
    PM = scrapy.Field() # 正负值
    
    # def __init__(self, *args, **kwargs):
        
    #     if self.__class__.__name__ == 'GameDetailItem':
    #         # 进阶数据(Pct:估计)：
    #         self.fields['TS'] = scrapy.Field() # 真实命中率
    #         self.fields['eFGPct'] = scrapy.Field() # 有效命中率
    #         self.fields['ThreePAr'] = scrapy.Field() # 每次出手时，3分出手率
    #         self.fields['FTr'] = scrapy.Field() # 每次出手, 获得罚球率
    #         self.fields['ORBPct'] = scrapy.Field() # 在场时，获得进攻篮板率
    #         self.fields['DRBPct'] = scrapy.Field() # 在场时，获得进攻篮板率
    #         self.fields['TRBPct']= scrapy.Field() # 在场时，总篮板率
    #         self.fields['ASTPct'] = scrapy.Field() # 助功率
    #         self.fields['STLPct'] = scrapy.Field() # 抢断率
    #         self.fields['BLKPct'] = scrapy.Field() # 盖帽率
    #         self.fields['TOVPct'] = scrapy.Field() # 每百回合失误数
    #         self.fields['USGPct'] = scrapy.Field() # 球员使用率
    #         self.fields['ORtg'] = scrapy.Field() # 每百回合(球员/球队)得分
    #         self.fields['DRtg'] = scrapy.Field() # 每百回合(球员/球队)失分
    #         self.fields['BPM'] =  scrapy.Field() # 每百回合正负值(基于联盟平均水平)
    #     super().__init__(*args, **kwargs)
    
        
class GameDetailQuaterItem(GameDetailItem):
    """按节统计比赛详细信息: quater include OT
    """
  
    _table_name = 'tb_game_detail_quater'
    _keys = ['game_id', 'player']
    quater = scrapy.Field()


class GameDetailListItem(NBAItem):
    """store each nba game detail info of list GameDetailItem
    like [dict(GameDetailItem)..,]
    """
    _table_name = 'tb_game_detail'
    data = scrapy.Field()
    

class GameDetailListQuaterItem(NBAItem):
    """store each nba game quater detail info of list GameDetailQuaterItem
    like [dict(GameDetailQuaterItem)..,]
    """
    _table_name = 'tb_game_detail_quater'
    data = scrapy.Field()
    

class AllPlayerSummaryItem(NBAItem):
    """ABA & NBA all players
    """
    _table_name = 'tb_all_player'
    _keys = ['player_url']
    player_url =scrapy.Field()
    player = scrapy.Field()
    season_from = scrapy.Field()
    season_to = scrapy.Field()
    position = scrapy.Field()
    height = scrapy.Field() # 身高(英尺)
    weight = scrapy.Field() # 体重(磅)
    birth_date = scrapy.Field()
    college = scrapy.Field()
    is_active = scrapy.Field() # yes: 退役, no: 现役(活跃与联盟或非联盟)
    hall_of_fame = scrapy.Field()


class PlayerInfoItem(NBAItem):
    """Player Personal information
    """
    _table_name = 'tb_player_info'
    _keys = ['player_url']
    player_url =scrapy.Field()
    player = scrapy.Field()
    is_active = scrapy.Field()
    avatar = scrapy.Field()
    positions = scrapy.Field() # 球场位置, 多个
    shots = scrapy.Field() # 投篮手
    birth_date = scrapy.Field()
    born_loc = scrapy.Field() # 出生地(市,州,国家)
    height = scrapy.Field() # 身高(英尺)
    weight = scrapy.Field() # 体重(磅)
    college = scrapy.Field()
    season_from = scrapy.Field() # 赛季起
    season_to = scrapy.Field() # 赛季止
    experience = scrapy.Field() # 球龄(赛季)
    relatives = scrapy.Field(default='') # 球员关系
    draft_team = scrapy.Field(default='') # 选秀球队
    draft_year = scrapy.Field(default='') # 选秀年
    draft_round = scrapy.Field(default='') # 第几轮
    draft_pick = scrapy.Field(default='') # 顺位
    draft_overall = scrapy.Field(default='') # 总顺位
    hall_of_fame_year = scrapy.Field(default='') # 名人堂年份
    hall_of_fame_pct = scrapy.Field(default='') # 名人堂机率
    champions = scrapy.Field() # 冠军数
    fmvps = scrapy.Field() # FMVP次数
    east_fmvps = scrapy.Field() # 东决MVP
    west_fmvps = scrapy.Field() # 西决MVP
    all_star = scrapy.Field() # 全明星数
    mvps = scrapy.Field() # 常规赛MVP次数
    dpoys = scrapy.Field() # 最佳防守球员次数
    mips = scrapy.Field() # 进步最快球员次数
    roys = scrapy.Field() # 年度最佳新秀
    sixthmans = scrapy.Field() # 最佳第六人次数
    first_teams = scrapy.Field() # 年度一阵
    second_teams = scrapy.Field() # 年度二阵
    third_teams = scrapy.Field() # 年度三阵
    def_first_teams = scrapy.Field() # 年度防守一阵
    def_second_teams = scrapy.Field() # 年度防守二阵
    def_third_teams = scrapy.Field() # 年度防守三阵
    anniv_75th = scrapy.Field() # 周年75大巨星
    died = scrapy.Field() # 已故

class PlayerPerGameItem(PlayerCommonItem, PerGameItem):
    """赛季数据
    球员场均基础数据 Per Game
    """
    _table_name = 'tb_player_per_game'
    _keys = ['season', 'player_url']

class PlayerAdvGameItem(PlayerCommonItem, AdvanceItem):
    """ 球员场均进阶数据 Advanced
    """
    _table_name = 'tb_player_advanced'
    _keys = ['season', 'player_url']
  
class Player36mGameItem(PlayerCommonItem, Per36MinsItem):
    """球员每36分钟 Per 36 Minutes
    """
    _table_name = 'tb_player_per36mins'
    _keys = ['season', 'player_url']

class Player100PossGameItem(PlayerCommonItem, Per100PossItem):
    """球员每百回合
    """
    _table_name = 'tb_player_per100poss'
    _keys = ['season', 'player_url']
class PlayerAdjShootItem(PlayerCommonItem, AdjustedShootingItem):
    """球员 Adjusted Shooting
    """
    _table_name = 'tb_player_adj_shooting'
    _keys = ['season', 'player_url']
class PlayerPlayByPlayItem(PlayerCommonItem, PlaybyPlayItem):
    """球员 按场上表现
    """
    _table_name = 'tb_player_pbp'
    _keys = ['season', 'player_url']

class PlayerShootingItem(PlayerCommonItem, ShootingItem):
    """球员 投射(按距离)
    """
    _table_name = 'tb_player_shooting'
    _keys = ['season', 'player_url']