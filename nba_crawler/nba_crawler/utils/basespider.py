from scrapy import Spider
from typing import Any, Literal

from lxml import etree
import redis
import re
import json
import os
from datetime import datetime, timezone
from lxml.etree import _Element
from scrapy.http import HtmlResponse
from scrapy.exceptions import CloseSpider

from nba_crawler.utils.itemloader import GameItemLoader
from itemadapter import ItemAdapter 
from nba_crawler.items import GameDetailItem, GameDetailQuaterItem
from nba_crawler.items import TeamPerGame, TeamRosterItem, TeamInjuryItem, TeamItem
from nba_crawler.utils.tools import element_text
from global_settings import REDIS_UPDATE_GAME_KEY, REDIS_UPDATE_PLAYER_KEY

# from .. import items


# def all_item_classes(prefix):
#     """_summary_

#     Args
#         prefix (_type_): start_with scrapy.Item.__name__

#     Returns:
#         List[Class Object]: .
#     """
#     # members (ClassName, class_object)
#     members = inspect.getmembers(items, inspect.isclass)

#     return [ member[1] for member in members if member[0].startswith(prefix) ]
    
class NBASpider(Spider):
    """
    Spider init args:
        get_schedule (boolean): for sp_games.py.Spider
        season_from (int): start season
        season_to (int): end season
    """
    history = ''
    custom_settings = {
        'REDIS_UPDATE_GAME_KEY': REDIS_UPDATE_GAME_KEY,
        'REDIS_UPDATE_PLAYER_KEY': REDIS_UPDATE_PLAYER_KEY
    }
    
    def spider_errors(self, spider_name, info):
        error_path = os.path.join(self.settings.get('DATA_PATH', ''), 'custom_error.txt')
        with open(error_path, 'ab') as f:
            info_str = f'{spider_name}: \"{info}\"\n'
            f.write(info_str.encode('utf-8'))
    
    
    def get_season_range(self):
        season_from = getattr(self, 'season_from', None)
        season_to = getattr(self, 'season_from', None)
        if not season_from or not season_to or season_to < season_from:
            raise CloseSpider
        return list(range(season_from, season_to+1))
    
    def get_current_season(self):
        year = 0
        cur_date =  datetime.utcnow()
        if cur_date.month in range(10,13):
            year = cur_date.year + 1
        elif cur_date.month in range(1,6):
            year = cur_date.year
        else:
            raise CloseSpider('NBA offseason')
        return year
    
    
    def read_player_url(self):
        """Read player info from redis set
        args:
            his (str): '' or ':his'  
        """
        is_active = 'active' if getattr(self, "history", '') == '' else 'retired'
        try:
            conn: redis.StrictRedis = redis.StrictRedis.from_url(self.settings.get('REDIS_URL'))
            players_set = conn.smembers(self.settings.get('REDIS_UPDATE_PLAYER_KEY'))
            if len(players_set) == 0:
                print('PLAYERS SET,', players_set)
                return []
            results = [ json.loads(i) for i in players_set]
            conn.close()
            
            return [j for j in results if j['is_active'] == is_active]
        except (TypeError,ConnectionError) as e:
            raise e
    
    
    def game_details(self, bs_trs, game_info, adv_trs=None,  quater=None):
        """generate game detail info
        Args:
            bs_trs (SelectorList[Selector]): basic game info
            adv_trs (SelectorList[Selector]): advance game info
            game_meta (dict): season,game_id, team
            quater (str): Q1-Q4, OT1..
        return:
            items (list): list of  GameDetailItem, GameDetailQuaterItem dict
        """
        items = []
        for i,tr in enumerate(bs_trs):
            not_played = tr.xpath('./td[@data-stat="reason"]/text()').get()
            # if not not_played:
            if quater:
                item = GameDetailQuaterItem()
                item['quater'] = quater
            else:
                item = GameDetailItem()
            if quater and not_played:
                continue
            item['game_id'] = game_info['game_id']
            item['is_started'] = True if i < 5 else False
            item['season'] = game_info['season']
            item['team'] = game_info['team']
            item['date'] = game_info['date']
            item['player'] = tr.xpath('./th[@data-stat="player"]/a/text()').get()
            item['player_url'] = tr.xpath('./th[@data-stat="player"]/a/@href').get()
            item['MP'] = tr.xpath('./td[@data-stat="mp"]/text()').get()
            item['FG'] = tr.xpath('./td[@data-stat="fg"]/text()').get()
            item['FGA'] = tr.xpath('./td[@data-stat="fga"]/text()').get()
            item['FGPct'] = tr.xpath('./td[@data-stat="fg_pct"]/text()').get()
            item['ThreeP'] = tr.xpath('./td[@data-stat="fg3"]/text()').get()
            item['ThreePA'] = tr.xpath('./td[@data-stat="fg3a"]/text()').get()
            item['ThreePPct'] = tr.xpath('./td[@data-stat="fg3_pct"]/text()').get()
            item['FT'] = tr.xpath('./td[@data-stat="ft"]/text()').get()
            item['FTA'] = tr.xpath('./td[@data-stat="fta"]/text()').get()
            item['FTPct'] = tr.xpath('./td[@data-stat="ft_pct"]/text()').get()
            item['ORB'] = tr.xpath('./td[@data-stat="orb"]/text()').get()
            item['DRB'] = tr.xpath('./td[@data-stat="drb"]/text()').get()
            item['TRB'] = tr.xpath('./td[@data-stat="trb"]/text()').get()
            item['AST'] = tr.xpath('./td[@data-stat="ast"]/text()').get()
            item['STL'] = tr.xpath('./td[@data-stat="stl"]/text()').get()
            item['BLK'] = tr.xpath('./td[@data-stat="blk"]/text()').get()
            item['TOV'] = tr.xpath('./td[@data-stat="tov"]/text()').get()
            item['PF'] = tr.xpath('./td[@data-stat="pf"]/text()').get()
            item['PTS'] = tr.xpath('./td[@data-stat="pts"]/text()').get()
            item['PM'] = tr.xpath('./td[@data-stat="plus_minus"]/text()').get()
            # advance
            if adv_trs:
                item['TS'] = adv_trs[i].xpath('./td[@data-stat="ts_pct"]/text()').get()
                item['eFGPct'] = adv_trs[i].xpath('./td[@data-stat="efg_pct"]/text()').get()
                item['ThreePAr'] = adv_trs[i].xpath('./td[@data-stat="fg3a_per_fga_pct"]/text()').get()
                item['FTr'] = adv_trs[i].xpath('./td[@data-stat="fta_per_fga_pct"]/text()').get()
                item['ORBPct'] = adv_trs[i].xpath('./td[@data-stat="orb_pct"]/text()').get()
                item['DRBPct'] = adv_trs[i].xpath('./td[@data-stat="drb_pct"]/text()').get()
                item['TRBPct'] = adv_trs[i].xpath('./td[@data-stat="trb_pct"]/text()').get()
                item['ASTPct'] = adv_trs[i].xpath('./td[@data-stat="ast_pct"]/text()').get()
                item['STLPct'] = adv_trs[i].xpath('./td[@data-stat="stl_pct"]/text()').get()
                item['BLKPct'] = adv_trs[i].xpath('./td[@data-stat="blk_pct"]/text()').get()
                item['TOVPct'] = adv_trs[i].xpath('./td[@data-stat="tov_pct"]/text()').get()
                item['USGPct'] = adv_trs[i].xpath('./td[@data-stat="usg_pct"]/text()').get()
                item['ORtg'] = adv_trs[i].xpath('./td[@data-stat="off_rtg"]/text()').get()
                item['DRtg'] = adv_trs[i].xpath('./td[@data-stat="def_rtg"]/text()').get()
                item['BPM'] = adv_trs[i].xpath('./td[@data-stat="bpm"]/text()').get()
            items.append(ItemAdapter(GameItemLoader(item).load_item()).asdict())
                # yield item
        return items
    
                
    def parse_team(self, rep: HtmlResponse ):
        
        """NBA Team Page info
        https://www.basketball-reference.com/teams/BOS/2024.html
        """
        html_str = re.sub(r'(<!--|-->)', '', rep.text)
        html_parser = etree.HTML(html_str)
        
        
        season, team, _ = rep.xpath('//div[@data-template="Partials/Teams/Summary"]/h1/span/text()').getall()
        # 球队基本信息
        team_item = TeamItem()
        team_item['logo'] = rep.css('img[src].teamlogo')[0].attrib['src'] # 球队Logo URL
        team_item['season'] = season
        team_item['team'] = team
        team_item['team_short'] = re.search(r'teams\/[A-Z]{1,}',rep.url).group().replace('teams/', '')
        
        xpath_start = '//div[@data-template="Partials/Teams/Summary"]/p'
        team_info_values = html_parser.xpath(xpath_start)
        
        # p标签下所有文字
        base_infos = [re.sub(r'\s*\n\s*','',''.join(v.xpath('.//text()')) ) for v in team_info_values if 'Playoffs' not in v]
        base_infos = [info for info in base_infos if 'Playoffs' not in info]
        number_pattern = re.compile(r'\d+\.?\d+')
        for item in base_infos:
            if 'Record' in item:
                team_item['record'] = re.search(r'\d+-\d+', item).group()
                team_item['rank'] = re.search(r'\d+(st|nd|rd|th)', item).group()
                team_item['conference'] = rep.meta['conference']
            elif 'PTS/G' in item:
                pts_g, opp_pts_g_v = item.split('Opp PTS/G:')
                team_item['pts_g'] = re.search(number_pattern, pts_g).group()
                team_item['opp_pts_g'] = re.search(number_pattern, opp_pts_g_v).group()
            elif 'SRS' in item:
                src, pace_v = item.split('Pace:')
                team_item['src'] = re.search(number_pattern, src).group()
                team_item['pace'] = re.search(number_pattern, pace_v).group()
            elif 'Off Rtg' in item:
                vals = item.split(':')
                team_item['off_rtg'] = re.search(number_pattern, vals[1]).group()
                team_item['def_rtg'] = re.search(number_pattern, vals[2]).group()
                team_item['net_rtg'] = re.search(number_pattern, vals[3]).group()
            elif 'Expected W-L' in item:
                team_item['expected_W_L'] = re.search(r'\d+-\d+', item).group()
            elif 'Arena' in item:
                arena, atte_v = item.split('Attendance:')
                team_item['arena'] = arena.split(':')[1]
                team_item['attendance'] = re.search(r'\d+,?\d+', atte_v).group()
            else:
                title, v = item.split(':')
                team_item[title.replace(' ', '_').lower()] = v.strip()
        
        yield team_item
        
        # 球员名单
        # @data-stat 全写number @aria-label 简写 No.
        roster_trs = html_parser.xpath('//table[@id="roster"]/tbody/tr')
        for tr in roster_trs:
            roster_item = TeamRosterItem()
            roster_item['season'] = season
            roster_item['team'] = team
            
            roster_item['number'] = element_text(tr,'th[@data-stat="number"]/text()')
            roster_item['player_url']= element_text(tr,'td[@data-stat="player"]/a/@href')
            roster_item['player'] = element_text(tr,'td[@data-stat="player"]/a/text()')
            roster_item['position'] = element_text(tr,'td[@data-stat="pos"]/text()')
            roster_item['height']  = element_text(tr,'td[@data-stat="height"]/text()')
            roster_item['weight'] = element_text(tr,'td[@data-stat="weight"]/text()')
            roster_item['birth_date'] = element_text(tr,'td[@data-stat="birth_date"]/text()')
            roster_item['birth_country'] = element_text(tr,'td[@data-stat="birth_country"]/span/text()')
            roster_item['exp'] = element_text(tr,'td[@data-stat="years_experience"]/text()')
            roster_item['college'] = element_text(tr,'td[@data-stat="college"]//text()', join=True)
            yield roster_item
            # print(roster_item['number'])
            
        # 伤病名单

        injurys = html_parser.xpath('//table[@id="injuries"]/tbody/tr')
        for tr in injurys:
            inj_item = TeamInjuryItem()
            inj_item['player'] = element_text(tr,'th[@data-stat="data-stat"]/a/text()')
            inj_item['player_url'] = element_text(tr,'th[@data-stat="data-stat"]/a/@href')
            inj_item['team'] = team
            inj_item['season'] = season
            inj_item['date'] = element_text(tr,'td[@data-stat="date_update"]/text()')
            inj_item['description'] = element_text(tr,'td[@data-stat="note"]/text()')
            yield inj_item
        
        # 场均数据(基础)

        per_games = html_parser.xpath('//table[@id="per_game"]/tbody/tr')
        for tr in per_games:
            per_game_item = TeamPerGame()
            per_game_item['team'] = team
            per_game_item['season'] = season
            per_game_item['player'] = element_text(tr,'td[@data-stat="player"]/a/text()') # 球员
            per_game_item['player_url'] = element_text(tr,'td[@data-stat="player"]/a/@href') # 球员
            per_game_item['GS'] = element_text(tr,'td[@data-stat="gs"]/text()') # 首发场次
            per_game_item['G'] = element_text(tr,'td[@data-stat="g"]/a/text()') # 场次
            per_game_item['MP'] = element_text(tr,'td[@data-stat="mp_per_g"]/text()') # 
            per_game_item['FG'] = element_text(tr,'td[@data-stat="fg_per_g"]/text()') # 命中数
            per_game_item['FGA'] = element_text(tr,'td[@data-stat="fga_per_g"]/text()') # 出手次数
            per_game_item['FGPct'] = element_text(tr,'td[@data-stat="fg_pct"]/text()') # 命中率
            per_game_item['ThreeP'] = element_text(tr,'td[@data-stat="fg3_per_g"]/text()') # 三分命中数
            per_game_item['ThreePA'] = element_text(tr,'td[@data-stat="fg3a_per_g"]/text()') # 
            per_game_item['ThreePPct'] = element_text(tr,'td[@data-stat="fg3_pct"]/text()') # 
            per_game_item['TwoP'] = element_text(tr,'td[@data-stat="fg2_per_g"]/text()') # 两分命中数
            per_game_item['TwoPA'] = element_text(tr,'td[@data-stat="fg2a_per_g"]/text()') # 
            per_game_item['TwoPPct'] = element_text(tr,'td[@data-stat="fg2_pct"]/text()') # 
            per_game_item['eFGPct'] = element_text(tr,'td[@data-stat="efg_pct"]/text()') # 有效命中率
            
            per_game_item['FT'] = element_text(tr,'td[@data-stat="ft_per_g"]/text()') # 罚球
            per_game_item['FTA'] = element_text(tr,'td[@data-stat="fta_per_g"]/text()') # 罚球出手数
            per_game_item['FTPct'] = element_text(tr,'td[@data-stat="ft_pct"]/text()') # 罚球命中率
            per_game_item['ORB'] = element_text(tr,'td[@data-stat="orb_per_g"]/text()') # 进攻篮板
            per_game_item['DRB'] = element_text(tr,'td[@data-stat="drb_per_g"]/text()') # 防守篮板
            per_game_item['TRB'] = element_text(tr,'td[@data-stat="trb_per_g"]/text()') # 防守篮板
            per_game_item['AST'] = element_text(tr,'td[@data-stat="ast_per_g"]/text()') # 助攻
            per_game_item['STL'] = element_text(tr,'td[@data-stat="stl_per_g"]/text()') # 抢断
            per_game_item['BLK'] = element_text(tr,'td[@data-stat="blk_per_g"]/text()') # 盖帽
            per_game_item['TOV'] = element_text(tr,'td[@data-stat="tov_per_g"]/text()') # 失误
            per_game_item['PF'] = element_text(tr,'td[@data-stat="pf_per_g"]/text()') # 犯规
            per_game_item['PTS'] = element_text(tr,'td[@data-stat="pts_per_g"]/text()') # 得分
            yield per_game_item


    def extract_per_game(self, tr: _Element):
        """场均数据内容提取(球员/球队) baseitem.PerGameItem
        """
        item = {}
        item['GS'] = element_text(tr,'./td[@data-stat="gs"]//text()') # 首发场次
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['MP'] = element_text(tr,'td[@data-stat="mp_per_g"]//text()') # 场均时间
        item['FG'] = element_text(tr,'td[@data-stat="fg_per_g"]//text()') # 命中数
        item['FGA'] = element_text(tr,'td[@data-stat="fga_per_g"]//text()') # 出手次数
        item['FGPct'] = element_text(tr,'td[@data-stat="fg_pct"]//text()') # 命中率
        item['ThreeP'] = element_text(tr,'td[@data-stat="fg3_per_g"]//text()') # 三分命中数
        item['ThreePA'] = element_text(tr,'td[@data-stat="fg3a_per_g"]//text()') # 
        item['ThreePPct'] = element_text(tr,'td[@data-stat="fg3_pct"]//text()') # 
        item['TwoP'] = element_text(tr,'td[@data-stat="fg2_per_g"]//text()') # 两分命中数
        item['TwoPA'] = element_text(tr,'td[@data-stat="fg2a_per_g"]//text()') # 
        item['TwoPPct'] = element_text(tr,'td[@data-stat="fg2_pct"]//text()') # 
        item['eFGPct'] = element_text(tr,'td[@data-stat="efg_pct"]//text()') # 有效命中率
        
        item['FT'] = element_text(tr,'td[@data-stat="ft_per_g"]//text()') # 罚球
        item['FTA'] = element_text(tr,'td[@data-stat="fta_per_g"]//text()') # 罚球出手数
        item['FTPct'] = element_text(tr,'td[@data-stat="ft_pct"]//text()') # 罚球命中率
        item['ORB'] = element_text(tr,'td[@data-stat="orb_per_g"]//text()') # 进攻篮板
        item['DRB'] = element_text(tr,'td[@data-stat="drb_per_g"]//text()') # 防守篮板
        item['TRB'] = element_text(tr,'td[@data-stat="trb_per_g"]//text()') # 防守篮板
        item['AST'] = element_text(tr,'td[@data-stat="ast_per_g"]//text()') # 助攻
        item['STL'] = element_text(tr,'td[@data-stat="stl_per_g"]//text()') # 抢断
        item['BLK'] = element_text(tr,'td[@data-stat="blk_per_g"]//text()') # 盖帽
        item['TOV'] = element_text(tr,'td[@data-stat="tov_per_g"]//text()') # 失误
        item['PF'] = element_text(tr,'td[@data-stat="pf_per_g"]//text()') # 犯规
        item['PTS'] = element_text(tr,'td[@data-stat="pts_per_g"]//text()') # 得分
        
        return item
        
    
    def extract_advance(self, tr: _Element):
        """进阶数据解析提取 baseitem.AdvanceItem
        return:
            dict: {k:v}
        """
        item = {}
        
        
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'td[@data-stat="mp"]//text()') # 总分钟
        item['PER'] = element_text(tr,'./td[@data-stat="per"]//text()')
        item['TS'] = element_text(tr,'./td[@data-stat="ts_pct"]//text()')
        item['ThreePAr'] = element_text(tr,'./td[@data-stat="fg3a_per_fga_pct"]//text()')
        item['FTr'] = element_text(tr,'./td[@data-stat="fta_per_fga_pct"]//text()')
        item['ORBPct'] = element_text(tr,'./td[@data-stat="orb_pct"]//text()')
        item['DRBPct'] = element_text(tr,'./td[@data-stat="drb_pct"]//text()')
        item['TRBPct'] = element_text(tr, './td[@data-stat="trb_pct"]//text()')
        item['ASTPct'] = element_text(tr,'./td[@data-stat="ast_pct"]//text()')
        item['STLPct'] = element_text(tr,'./td[@data-stat="stl_pct"]//text()')
        item['BLKPct'] = element_text(tr,'./td[@data-stat="blk_pct"]//text()')
        item['TOVPct'] = element_text(tr,'./td[@data-stat="tov_pct"]//text()')
        item['USGPct'] = element_text(tr,'./td[@data-stat="usg_pct"]//text()')
        item['OWS'] = element_text(tr,'./td[@data-stat="ows"]//text()')
        item['DWS'] = element_text(tr,'./td[@data-stat="dws"]//text()')
        item['WS'] = element_text(tr,'./td[@data-stat="ws"]//text()')
        item['WS_48'] = element_text(tr,'./td[@data-stat="ws_per_48"]//text()')
        item['OBPM'] = element_text(tr,'./td[@data-stat="obpm"]//text()')
        item['DBPM'] = element_text(tr,'./td[@data-stat="dbpm"]//text()')
        item['BPM'] = element_text(tr,'./td[@data-stat="bpm"]//text()')
        item['VORP'] = element_text(tr,'./td[@data-stat="vorp"]//text()')
        return item
    
    def extract_per36mins(self, tr: _Element):
        """每36分钟数据提取 baseitem.Per36MinsItem
        """
        item = {}
        
        item['GS'] = element_text(tr,'./td[@data-stat="gs"]//text()') # 首发场次
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'td[@data-stat="mp"]//text()') # 场均时间
        item['FG'] = element_text(tr,'td[@data-stat="fg_per_mp"]//text()') # 命中数
        item['FGA'] = element_text(tr,'td[@data-stat="fga_per_mp"]//text()') # 出手次数
        item['FGPct'] = element_text(tr,'td[@data-stat="fg_pct"]//text()') # 命中率
        item['ThreeP'] = element_text(tr,'td[@data-stat="fg3_per_mp"]//text()') # 三分命中数
        item['ThreePA'] = element_text(tr,'td[@data-stat="fg3a_per_mp"]//text()') # 
        item['ThreePPct'] = element_text(tr,'td[@data-stat="fg3_pct"]//text()') # 
        item['TwoP'] = element_text(tr,'td[@data-stat="fg2_per_mp"]//text()') # 两分命中数
        item['TwoPA'] = element_text(tr,'td[@data-stat="fg2a_per_mp"]//text()') # 
        item['TwoPPct'] = element_text(tr,'td[@data-stat="fg2_pct"]//text()') # 
       
        item['FT'] = element_text(tr,'td[@data-stat="ft_per_mp"]//text()') # 罚球
        item['FTA'] = element_text(tr,'td[@data-stat="fta_per_mp"]//text()') # 罚球出手数
        item['FTPct'] = element_text(tr,'td[@data-stat="ft_pct"]//text()') # 罚球命中率
        item['ORB'] = element_text(tr,'td[@data-stat="orb_per_mp"]//text()') # 进攻篮板
        item['DRB'] = element_text(tr,'td[@data-stat="drb_per_mp"]//text()') # 防守篮板
        item['TRB'] = element_text(tr,'td[@data-stat="trb_per_mp"]//text()') # 防守篮板
        item['AST'] = element_text(tr,'td[@data-stat="ast_per_mp"]//text()') # 助攻
        item['STL'] = element_text(tr,'td[@data-stat="stl_per_mp"]//text()') # 抢断
        item['BLK'] = element_text(tr,'td[@data-stat="blk_per_mp"]//text()') # 盖帽
        item['TOV'] = element_text(tr,'td[@data-stat="tov_per_mp"]//text()') # 失误
        item['PF'] = element_text(tr,'td[@data-stat="pf_per_mp"]//text()') # 犯规
        item['PTS'] = element_text(tr,'td[@data-stat="pts_per_mp"]//text()') # 得分
        return item
    
    
    def extract_per100poss(self, tr: _Element):
        """每百回合 baseitem.Per100PossItem
        """
        item = {}
        
        item['GS'] = element_text(tr,'./td[@data-stat="gs"]//text()') # 首发场次
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'td[@data-stat="mp"]//text()') # 场均时间
        item['FG'] = element_text(tr,'td[@data-stat="fg_per_poss"]//text()') # 命中数
        item['FGA'] = element_text(tr,'td[@data-stat="fga_per_poss"]//text()') # 出手次数
        item['FGPct'] = element_text(tr,'td[@data-stat="fg_pct"]//text()') # 命中率
        item['ThreeP'] = element_text(tr,'td[@data-stat="fg3_per_poss"]//text()') # 三分命中数
        item['ThreePA'] = element_text(tr,'td[@data-stat="fg3a_per_poss"]//text()') # 
        item['ThreePPct'] = element_text(tr,'td[@data-stat="fg3_pct"]//text()') # 
        item['TwoP'] = element_text(tr,'td[@data-stat="fg2_per_poss"]//text()') # 两分命中数
        item['TwoPA'] = element_text(tr,'td[@data-stat="fg2a_per_poss"]//text()') # 
        item['TwoPPct'] = element_text(tr,'td[@data-stat="fg2_pct"]//text()') # 
       
        item['FT'] = element_text(tr,'td[@data-stat="ft_per_poss"]//text()') # 罚球
        item['FTA'] = element_text(tr,'td[@data-stat="fta_per_poss"]//text()') # 罚球出手数
        item['FTPct'] = element_text(tr,'td[@data-stat="ft_pct"]//text()') # 罚球命中率
        item['ORB'] = element_text(tr,'td[@data-stat="orb_per_poss"]//text()') # 进攻篮板
        item['DRB'] = element_text(tr,'td[@data-stat="drb_per_poss"]//text()') # 防守篮板
        item['TRB'] = element_text(tr,'td[@data-stat="trb_per_poss"]//text()') # 防守篮板
        item['AST'] = element_text(tr,'td[@data-stat="ast_per_poss"]//text()') # 助攻
        item['STL'] = element_text(tr,'td[@data-stat="stl_per_poss"]//text()') # 抢断
        item['BLK'] = element_text(tr,'td[@data-stat="blk_per_poss"]//text()') # 盖帽
        item['TOV'] = element_text(tr,'td[@data-stat="tov_per_poss"]//text()') # 失误
        item['PF'] = element_text(tr,'td[@data-stat="pf_per_poss"]//text()') # 犯规
        item['PTS'] = element_text(tr,'td[@data-stat="pts_per_poss"]//text()') # 得分
        
        item['ORtg'] = element_text(tr,'td[@data-stat="pts_per_poss"]//text()') # 每百回合(球员/球队)得分
        item['DRtg'] = element_text(tr,'td[@data-stat="pts_per_poss"]//text()') # 每百回合(球员/球队)失分
        return item
    
    def extract_adj_shoot(self, tr: _Element):
        """调整后出手 baseitem.AdjustedShootingItem
        """
        item = {}
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'./td[@data-stat="mp"]//text()') # 总时间
        
        item['FGPct'] = element_text(tr,'./td[@data-stat="fg_pct"]//text()')
        item['TwoPPct'] = element_text(tr,'./td[@data-stat="fg2_pct"]//text()')
        item['ThreePPct'] = element_text(tr,'./td[@data-stat="fg3_pct"]//text()')
        item['eFGPct'] = element_text(tr,'./td[@data-stat="efg_pct"]//text()')
        item['FTPct'] = element_text(tr,'./td[@data-stat="ft_pct"]//text()')
        item['TS'] = element_text(tr,'./td[@data-stat="ts_pct"]//text()')
        item['FTr'] = element_text(tr,'./td[@data-stat="fta_per_fga_pct"]//text()')
        item['ThreePAr'] = element_text(tr,'./td[@data-stat="fg3a_per_fga_pct"]//text()')
        # 联盟平均
        item['league_FGPct'] = element_text(tr,'./td[@data-stat="lg_fg_pct"]//text()')
        item['league_TwoPPct'] = element_text(tr,'./td[@data-stat="lg_fg2_pct"]//text()')
        item['league_ThreePPct'] = element_text(tr,'./td[@data-stat="lg_fg3_pct"]//text()')
        item['league_eFGPct'] = element_text(tr,'./td[@data-stat="lg_efg_pct"]//text()')
        item['league_FTPct'] = element_text(tr,'./td[@data-stat="lg_ft_pct"]//text()')
        item['league_TS'] = element_text(tr,'./td[@data-stat="lg_ts_pct"]//text()')
        item['league_FTr'] = element_text(tr,'./td[@data-stat="lg_fta_per_fga_pct"]//text()')
        item['league_ThreePAr'] = element_text(tr,'./td[@data-stat="lg_fg3a_per_fga_pct"]//text()')
        # 调整后, 权重占比如：100*FG/league_FG(更直观对比联盟水平)
        item['adjusted_FGPct'] = element_text(tr,'./td[@data-stat="adj_fg_pct"]//text()')
        item['adjusted_TwoPPct'] = element_text(tr,'./td[@data-stat="adj_fg2_pct"]//text()')
        item['adjusted_ThreePPct'] = element_text(tr,'./td[@data-stat="adj_fg3_pct"]//text()')
        item['adjusted_eFGPct'] = element_text(tr,'./td[@data-stat="adj_efg_pct"]//text()')
        item['adjusted_FTPct'] = element_text(tr,'./td[@data-stat="adj_ft_pct"]//text()')
        item['adjusted_TS'] = element_text(tr,'./td[@data-stat="adj_ts_pct"]//text()')
        item['adjusted_FTr'] = element_text(tr,'./td[@data-stat="adj_fta_per_fga_pct"]//text()')
        item['adjusted_ThreePAr'] = element_text(tr,'./td[@data-stat="adj_fg3a_per_fga_pct"]//text()')
        
        item['FG_add'] = element_text(tr,'./td[@data-stat="fg_pts_added"]//text()')
        item['TS_add'] = element_text(tr,'./td[@data-stat="ts_pts_added"]//text()')
        return item
    
    def extract_playbyplay(self, tr: _Element):
        """ Play By Play 场上表现 basitem.PlaybyPlayItem
        """
        item = {}
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'./td[@data-stat="mp"]//text()') # 总时间
        
        item['PG_pct'] = element_text(tr,'./td[@data-stat="pct_1"]//text()')
        item['SG_pct'] = element_text(tr,'./td[@data-stat="pct_2"]//text()')
        item['SF_pct'] = element_text(tr,'./td[@data-stat="pct_3"]//text()')
        item['PF_pct'] = element_text(tr,'./td[@data-stat="pct_4"]//text()')
        item['C_pct'] = element_text(tr,'./td[@data-stat="pct_5"]//text()')
        
        item['OnCourt_100poss'] = element_text(tr,'./td[@data-stat="plus_minus_on"]//text()')
        item['OffCourt_100poss'] = element_text(tr,'./td[@data-stat="plus_minus_net"]//text()')
        item['TOV_BadPass'] = element_text(tr,'./td[@data-stat="tov_bad_pass"]//text()')
        item['TOV_LostBall'] = element_text(tr,'./td[@data-stat="tov_lost_ball"]//text()')
        item['Foul_Shoot'] = element_text(tr,'./td[@data-stat="fouls_shooting"]//text()')
        item['Foul_Offensive'] = element_text(tr,'./td[@data-stat="fouls_offensive"]//text()')
        item['FoulDrawn_Shoot'] = element_text(tr,'./td[@data-stat="drawn_shooting"]//text()')
        item['FoulDrawn_Offensive'] = element_text(tr,'./td[@data-stat="drawn_offensive"]//text()')
        item['PointGenAst'] = element_text(tr,'./td[@data-stat="astd_pts"]//text()')
        item['And1'] = element_text(tr,'./td[@data-stat="and1s"]//text()')
        item['BLKd'] = element_text(tr,'./td[@data-stat="own_shots_blk"]//text()')
        return item
    
    
    def extract_shooting(self, tr: _Element):
        """Shooting 详细投篮数据，按距离以及各距离命中率
        baseitem.ShootingItem
        """
        item = {}
        
        item['G'] = element_text(tr,'./td[@data-stat="g"]//text()') # 场次
        item['Total_MP'] = element_text(tr,'./td[@data-stat="mp"]//text()') # 总时间
        
        item['FGPct'] = element_text(tr,'./td[@data-stat="fg_pct"]//text()')
        item['DistanceAvg'] = element_text(tr,'./td[@data-stat="avg_dist"]//text()')
        # % of FGA by Distance(英尺feet) 各距离出手占比总出手 
        item['Pct_FGA_Dist_2P'] = element_text(tr,'./td[@data-stat="pct_fga_fg2a"]//text()')
        item['Pct_FGA_Dist_0_3'] = element_text(tr,'./td[@data-stat="pct_fga_00_03"]//text()')
        item['Pct_FGA_Dist_3_10'] = element_text(tr,'./td[@data-stat="pct_fga_03_10"]//text()')
        item['Pct_FGA_Dist_10_16'] = element_text(tr,'./td[@data-stat="pct_fga_10_16"]//text()')
        item['Pct_FGA_Dist_16_3P'] = element_text(tr,'./td[@data-stat="pct_fga_16_xx"]//text()')
        item['Pct_FGA_Dist_3P'] = element_text(tr,'./td[@data-stat="pct_fga_fg3a"]//text()')
         # FG% by Distance 各距离命中率
        item['FGPct_Dist_2P'] = element_text(tr,'./td[@data-stat="fg_pct_fg2a"]//text()')
        item['FGPct_Dist_0_3'] = element_text(tr,'./td[@data-stat="fg_pct_00_03"]//text()')
        item['FGPct_Dist_3_10'] = element_text(tr,'./td[@data-stat="fg_pct_03_10"]//text()')
        item['FGPct_Dist_10_16'] = element_text(tr,'./td[@data-stat="fg_pct_10_16"]//text()')
        item['FGPct_Dist_16_3P'] = element_text(tr,'./td[@data-stat="fg_pct_16_xx"]//text()')
        item['FGPct_Dist_3P'] = element_text(tr,'./td[@data-stat="fg_pct_fg3a"]//text()')
        # % of FG Assisted 被助攻(吃饼)
        item['Pct_FG_Astd2P'] = element_text(tr,'./td[@data-stat="pct_ast_fg2"]//text()')
        item['Pct_FG_Astd3P'] = element_text(tr,'./td[@data-stat="pct_ast_fg3"]//text()')
        
        item['Pct_Dunk_FGA'] = element_text(tr,'./td[@data-stat="pct_fga_dunk"]//text()')
        item['Dunk_Make'] = element_text(tr,'./td[@data-stat="fg_dunk"]//text()')
        
        item['Pct_Corner3_3FGA'] = element_text(tr,'./td[@data-stat="pct_fg3a_corner3"]//text()')
        item['Corner3_3FGPct'] = element_text(tr,'./td[@data-stat="fg_pct_corner3"]//text()')
        # Heaves: 超过半场
        item['Heaves_Attempt'] = element_text(tr,'./td[@data-stat="fg3a_heave"]//text()')
        item['Heaves_Make'] = element_text(tr,'./td[@data-stat="fg3_heave"]//text()')
        
        return item
        
# class NBASpider(Spider):
#     """Base Class for all NBA Spider
#     class args:
#         df_objs (dict):  data frame object, {classItemName: pandas.dataframe}. each spider only has one instance
#         if_exists (str): Literal['replace', 'fail', 'append'] for df.to_sql(if_exists='replace')
#         prefix (str):  Class Item Prefix.
#         db_file (str):  SQLite|CSV saved file.
#         update_pipe (Boolean) default False: True, SavePipeLine didnt append 'update_tables' data to 'db_file'.
#         update_tables (List): while update_pipe == True, only update for classItemName._table_name in sqlitedb
#     """
#     df_objs = {}
#     prefix = ''
#     db_file = ''
#     if_exists: Literal['replace', 'fail', 'append'] = 'replace'
#     update_pipe = False
#     update_tables = []
     
#     def __new__(cls, *args: Any, **kwargs: Any):
        
#         obj = super().__new__(cls, *args, **kwargs)
#         if not cls.df_objs and cls.prefix:
#             # use attr(_table_name) of classItem as key
#             # value: dataframe
#             cls.df_objs = { item._table_name: pd.DataFrame(data={}, columns=list(item.fields.keys())) 
#                            for item in all_item_classes(cls.prefix)}
#         return obj