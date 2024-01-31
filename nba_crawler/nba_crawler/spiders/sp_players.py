"""
class PlayerSummary
    所有球员链接

class PlayerSpider, PlayerSpiderHis:
现役球员(包括不在联盟中)和退役球员
    https://www.basketball-reference.com/players/a/
    球员数据：
    1.球员信息
    2.该球员各赛季(包括季后赛):
        场均基础数据 Per Game
        场均进阶数据 Advanced
        每36分钟 Per 36 Minutes
        调整后出手 Adjusted Shooting
        投射 Shooting
        场上表现 Play By Play
        每百回合 per 100 poss
"""
from typing import Iterable
from scrapy.http import Request, HtmlResponse
from urllib.parse import urljoin
from string import ascii_lowercase
from lxml import etree
import re
from nba_crawler.utils.basespider import NBASpider
from nba_crawler.utils.tools import search_text, element_text
from nba_crawler.utils.itemloader import PlayerItemLoader, NBAItemLoader
from nba_crawler.items import AllPlayerSummaryItem, PlayerInfoItem, PlayerPerGameItem
from nba_crawler.items import PlayerAdvGameItem, Player36mGameItem, Player100PossGameItem
from nba_crawler.items import PlayerPlayByPlayItem, PlayerShootingItem, PlayerAdjShootItem
from scrapy.exceptions import CloseSpider



POSITIONS = {
    'Power Forwar': 'PF',
    'Small Forwar': 'SF',
    'Shooting Guard': 'SG',
    'Point Guard': 'PG',
    'Center': 'C',
}

class PlayerSummary(NBASpider):
    """Get All Players List:
    get player by last name starting with letter 
        https://www.basketball-reference.com/players/a        
    Player	From(season)	To(season)	Pos	Ht	Wt	Birth Date	Colleges
    Kareem Abdul-Jabbar*	1970	1989	C	7-2	225	April 16, 1947	UCLA
    """
    name = "PlayerSummary"
    
    def start_requests(self) -> Iterable[Request]:
        for i in ascii_lowercase:
            yield Request(f'https://www.basketball-reference.com/players/{i}/', self.parse)
        # yield Request(f'https://www.basketball-reference.com/players/a/', self.parse)
        
        
    def parse(self, rep: HtmlResponse):
        player_trs = rep.xpath('//table[@id="players"]/tbody/tr[not(@class)]')
        for tr in player_trs:
            player = AllPlayerSummaryItem()
            player['player'] = tr.xpath('./th[@data-stat="player"]//a/text()').get()
            
            is_active = tr.xpath('./th[@data-stat="player"]/strong').get()
            hall_of_fame = tr.xpath('./th[@data-stat="player"]/text()').get('')
            player['is_active'] = 'active' if is_active else 'retired'
            player['hall_of_fame'] = 'yes' if hall_of_fame else 'no'
                 
            player['player_url'] = tr.xpath('./th[@data-stat="player"]//a/@href').get()
            player['season_from'] = tr.xpath('./td[@data-stat="year_min"]/text()').get()
            player['season_to'] = tr.xpath('./td[@data-stat="year_max"]/text()').get()
            player['position'] = tr.xpath('./td[@data-stat="pos"]/text()').get()
            player['height'] = tr.xpath('./td[@data-stat="height"]/text()').get()
            player['weight'] = tr.xpath('./td[@data-stat="weight"]/text()').get()
            player['birth_date'] = tr.xpath('./td[@data-stat="birth_date"]/a/text()').get('').replace(',','')
            player['college'] = tr.xpath('./td[@data-stat="colleges"]/a/text()').get('').replace(',', '-')
            
            yield player
            

class PlayerSpider(NBASpider):
    """Active player data
    """
    name = 'PlayerSpider'
    # db_file = 'nba_data.db'
    # prefix = 'Player'
    # if_exists = 'replace'
    
    def start_requests(self) -> Iterable[Request]:
        players = self.read_player_url()
        
        url_prefix = 'https://www.basketball-reference.com'
        for player in players:
            yield Request(urljoin(url_prefix, player['player_url']), self.parse_player_info, meta={'player_info': player})

        # test = 'https://www.basketball-reference.com/players/m/martisl01.html'
        # yield Request(urljoin(url_prefix, test), self.parse_player_info )
    
    
    def parse_player_info(self, rep: HtmlResponse):
        
        info_div = rep.xpath('//div[@id="meta"]')
        
        player_item = PlayerInfoItem()
        # player_item ={}
        player_info = rep.meta['player_info']
        player_item['player'] = player_info['player']
        player_item['player_url'] = player_info['player_url']
        player_item['height'] = player_info['height']
        player_item['weight'] = player_info['weight']
        player_item['college'] = player_info['college']
        player_item['season_from'] = player_info['season_from']
        player_item['season_to'] = player_info['season_to']
        player_item['birth_date'] = player_info['birth_date']
        player_item['is_active'] = 1 if player_info['is_active'] == 'active' else 0
        player_item['avatar'] = info_div.xpath('./div[@class="media-item"]/img/@src').get('')
        
        base_infos = [re.sub(r'\s*\n\s*','','|'.join(v.xpath('.//text()').getall()) ) 
                      for v in info_div.xpath('./div[2]/p')]
        base_infos = [re.sub(r'[\|\xa0]+', ' ', i) for i in base_infos]
        # print(base_infos)
        for item in base_infos:
            
            if 'Position' in item:
                player_item['shots'] = search_text(r'(Right|Left)', item)[0]
                player_item['positions'] = ','.join([ POSITIONS[k] for k in POSITIONS.keys() if k in item])
            elif 'Born' in item:
                player_item['born_loc'] = search_text(r'in (.+\w)', item)[0]
            elif 'Draft' in item:
                # 通过选秀
                draft_str = re.sub(r'Draft:\s?','',item).split(',')
                try:
                    player_item['draft_team'] = draft_str[0].strip()
                    round_str, pick_str = draft_str[1].split('round')
                    player_item['draft_round'] = search_text(r'\d+', round_str)[0]
                    player_item['draft_pick'] = search_text(r'\d+', pick_str)[0]
                    player_item['draft_year'] = search_text(r'\d+', draft_str[3])[0]
                    player_item['draft_overall'] = search_text(r'\d+', draft_str[2])[0]
                except Exception as e:
                    print(':',rep.url)
                    player_item['draft_team'] = draft_str[0].strip()
                    player_item['draft_round'] = search_text(r'\d+', draft_str[1])[0]
                    player_item['draft_year'] = search_text(r'\d+', draft_str[2])[0]
                    self.spider_errors(self.__class__.__name__, f'parse_player_info() parse {e}, {rep.url}')
            elif 'Experience' in item or 'Career Length' in item:
                player_item['experience'] = search_text(r'(\d+) year(s)?', item)[0]
            elif 'Relatives' in item:
                player_item['relatives'] = item.split(': ')[1].strip()
            elif 'Hall of Fame' in item:
                player_item['hall_of_fame_year'] = item.split(': ')[1].strip()
            elif 'Died' in item:
                player_item['died'] = item
        
                # raise CloseSpider(f'custom stop:{e}\n{player_item["player"]}')
        # Appearances on Leaderboards, Awards, and Honors 
        # HTML内容被注释
        
        html_parser = etree.HTML(re.sub(r'(<!--|-->)', '', rep.text))
        awards_text = element_text(html_parser,'//div[@id="leaderboard_notable-awards"]//text()', True)
        all_star_game_text = element_text(html_parser,'//div[@id="leaderboard_allstar"]//td/a/text()', True)
        champs_text = len(html_parser.xpath('//div[@id="leaderboard_championships"]//td'))
        all_league = element_text(html_parser,'//div[@id="leaderboard_all_league"]//td/text()', True)
        hall_of_fame_ = element_text(html_parser,'//div[@id="leaderboard_hof_prob"]//td/a/text()')
        
        player_item['hall_of_fame_pct'] = hall_of_fame_
        player_item['champions'] = champs_text
        player_item['fmvps'] = len(re.findall(r'\d+ Finals Most Valuable', awards_text))
        player_item['west_fmvps'] = len(re.findall(r'Western Conference Finals Most Valuable', awards_text))
        player_item['east_fmvps'] = len(re.findall(r'Eastern Conference Finals Most Valuable', awards_text))
        player_item['mvps'] = len(re.findall(r'\d+-\d+ Most Valuable Player', awards_text))
        player_item['dpoys'] = len(re.findall(r'Defensive Player of the Year', awards_text))
        player_item['mips'] = len(re.findall(r'Most Improved Player', awards_text))
        player_item['sixthmans'] = len(re.findall(r'Sixth Man of the Year', awards_text))
        player_item['roys'] = len(re.findall(r'\d+-\d+ Rookie of the Year', awards_text))
        player_item['anniv_75th'] = len(re.findall(r'NBA 75th Anniversary Team', awards_text))
        
        player_item['all_star'] = len(re.findall(r'\d+ NBA', all_star_game_text))
        
        player_item['first_teams'] = len(re.findall(r'All-NBA \(1st\)', all_league))
        player_item['second_teams'] = len(re.findall(r'All-NBA \(2nd\)', all_league))
        player_item['third_teams'] = len(re.findall(r'All-NBA \(3rd\)', all_league))
        player_item['def_first_teams'] = len(re.findall(r'All-Defensive \(1st\)', all_league))
        player_item['def_second_teams'] = len(re.findall(r'All-Defensive \(2nd\)', all_league))
        player_item['def_third_teams'] = len(re.findall(r'All-Defensive \(3rd\)', all_league))
        
        yield PlayerItemLoader(player_item).load_item()
        
        # per game
        trs_per_game = html_parser.xpath('//table[@id="per_game"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_per_game"]/tbody/tr')
        # per 36 minutes
        trs_per_36mins = html_parser.xpath('//table[@id="per_minute"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_per_minute"]/tbody/tr')
        # per 100 possess
        trs_100poss = html_parser.xpath('//table[@id="per_poss"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_per_poss"]/tbody/tr')
        # advanced data
        trs_advanced = html_parser.xpath('//table[@id="advanced"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_advanced"]/tbody/tr')
        # adjusted shooting
        trs_adj_shooting = html_parser.xpath('//table[@id="adj_shooting"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_adj_shooting"]/tbody/tr')
        # play by play since season 1997
        trs_pbp = html_parser.xpath('//table[@id="pbp"]/tbody/tr') \
            + html_parser.xpath('//table[@id="playoffs_pbp"]/tbody/tr')
        # shooting
        trs_shooting = html_parser.xpath('//table[@id="shooting"]/tbody/tr') \
            +  html_parser.xpath('//table[@id="shooting"]/tbody/tr')
       
        all_trs = trs_per_game + trs_per_36mins + trs_100poss + trs_advanced \
             + trs_adj_shooting + trs_shooting + trs_pbp
        for tr in all_trs:
            item = {}
            item_name = element_text(tr, '../../@id')
            item['is_playoff'] = 1 if 'playoffs' in item_name else 0
            item['team'] = element_text(tr, './td[@data-stat="team_id"]//text()')
            item['season'] = element_text(tr, './th[@data-stat="season"]//text()')
            # item['player'] = player_item['player']
            item['player_url'] = rep.url
            
            item['age'] = element_text(tr, './td[@data-stat="age"]//text()')
            item['league'] = element_text(tr, './td[@data-stat="lg_id"]//text()')
            item['positions'] = element_text(tr, './td[@data-stat="pos"]//text()')
            
            
            if 'per_game' in item_name:
                item.update(self.extract_per_game(tr))
                tr_item = PlayerPerGameItem(item)
            elif 'per_minute' in item_name:
                item.update(self.extract_per36mins(tr))
                tr_item = Player36mGameItem(item)
            elif 'per_poss' in item_name:
                item.update(self.extract_per100poss(tr))
                    
                tr_item = Player100PossGameItem(item)
            elif 'advanced' in item_name:
                item.update(self.extract_advance(tr))
                
                tr_item = PlayerAdvGameItem(item)
            elif 'adj_shooting' in item_name:
                item.update(self.extract_adj_shoot(tr))
                tr_item = PlayerAdjShootItem(item)
            elif 'pbp' in item_name:
                item.update(self.extract_playbyplay(tr))
                tr_item = PlayerPlayByPlayItem(item)
            else:
                item.update(self.extract_shooting(tr))
                tr_item = PlayerShootingItem(item)
            # print(NBAItemLoader(tr_item).load_item())
            yield NBAItemLoader(tr_item).load_item()

class PlayerSpiderHis(PlayerSpider):
    """Retired player data
    """
    name = 'PlayerSpiderHis'
    history = ':his'
    
    def start_requests(self) -> Iterable[Request]:
        players = self.read_player_url()
        
        url_prefix = 'https://www.basketball-reference.com'
        for player in players:
            
            yield Request(urljoin(url_prefix, player['player_url']), self.parse_player_info, meta={'player_info': player})
        # print(len(players))
        # test = 'https://www.basketball-reference.com/players/l/lillada01.html'
        # yield Request(urljoin(url_prefix, test), self.parse_player_info )
    