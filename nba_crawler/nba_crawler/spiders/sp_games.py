"""
GameSpider, GameSpiderHis

    获取每场比赛的详细数据：
    1.总计
    2.按小节统计
"""
import re
import redis
import json

from lxml import etree
from typing import Any, Iterable, Optional
from dateutil.parser import parse,ParserError

from scrapy import Request
from scrapy.http.response.html import HtmlResponse

from nba_crawler.items import GameScheduleItem, GameDetailListItem, GameDetailListQuaterItem
from nba_crawler.utils.basespider import NBASpider
from nba_crawler.utils.tools import element_text
from nba_crawler.utils.itemloader import GameItemLoader



class GameSpider(NBASpider):
    """每天获取最新赛季的赛程数据
    GameSpider(get_schedule=[True, False]) 是否获取赛程
        默认: False
    """
    name = 'GameSpider'
    # prefix = 'Game'
    # db_file = 'nba_data.db'
    # if_exists = 'append' # dataframe to_sql mode: 'append' 'replace' 'fail'
    # update_pipe = True
    # update_tables = ['tb_game']
    # start_urls = ['https://www.basketball-reference.com/leagues/NBA_2024_games-january.html']
    
    def start_requests(self) -> Iterable[Request]:
        # 每赛季分月份
        if not getattr(self, 'get_schedule', False):
            link_prefix = "https://www.basketball-reference.com/boxscores/"
            results = self.get_newest_games()
            for item in results:
                url = f"{link_prefix+item['game_id']}.html" 
                yield Request(url, callback=self.parse_game_detail, meta={'game_info': item})
        else:
            # 赛季开始当年10月份-次年6月份
            year = self.get_current_season()
            
            yield Request(f'https://www.basketball-reference.com/leagues/NBA_{year}_games.html', self.parse_game)
        
    
    def get_newest_games(self):
        """当前赛季的比赛链接, 从redis读取
        https://www.basketball-reference.com/boxscores/{game_id}.html
        """
        conn: redis.StrictRedis = redis.StrictRedis.from_url(self.settings.get('REDIS_URL'))
        try:
            # 总场次: (82*30(常规赛) + 16*7(PLAYOFF 1ST) + 8*7(PLAYOFF 2RD) + 4*7(CONFERENS FINAL) + 2*7(FINNAL) + 8) / 2
            schedules = conn.spop(self.settings.get('REDIS_UPDATE_GAME_KEY'), 1340)
            results = [json.loads(i) for i in schedules]
            return results
        except (TypeError, ConnectionError) as e:
            raise e
    
    
    def parse_game(self, rep: HtmlResponse):
        """获取当赛季赛程, 只获取一次
        当前赛季只有常规赛,
        季后赛需要等到指定日期
        https://www.basketball-reference.com/leagues/NBA_2024_games.html
        """
        html_parser = etree.HTML(rep.text)
        games_tr = html_parser.xpath('//table[@id="schedule"]/tbody/tr[not(@class)]')

        season = html_parser.xpath('//div[@id="meta"]/div[2]/h1/span/text()')[0]
        for tr in games_tr:
            game_meta = {}
            # game_meta['date'] = tr.xpath('./th[@data-stat="date_game"]')
            # 日期
            time = element_text(tr, './td[@data-stat="game_start_time"]/text()')
            d_str = time+','+ element_text(tr, './th[@data-stat="date_game"]/a/text()')
            game_meta['visitor'] = element_text(tr, './td[@data-stat="visitor_team_name"]/a/text()')
            game_meta['visitor_pts'] = element_text(tr, './td[@data-stat="visitor_pts"]/text()')
            game_meta['home'] = element_text(tr, './td[@data-stat="home_team_name"]/a/text()')
            game_meta['home_pts'] = element_text(tr, './td[@data-stat="home_pts"]/text()')
            game_meta['attendance'] = element_text(tr, './td[@data-stat="attendance"]/text()')
            game_meta['arena'] = element_text(tr, './td[@data-stat="arena_name"]/text()')
            game_meta['note'] = element_text(tr, './td[@data-stat="game_remarks"]/text()')
            game_meta['season'] = season
            link = element_text(tr, './td[@data-stat="box_score_text"]/a/@href')
            
            # 根据球队缩写传到meta用于查找比赛详细数据
            home_short = element_text(tr, './td[@data-stat="home_team_name"]/a/@href')
            home_short = re.search(r'\/teams\/(\w+)', home_short).groups()[0]
            
            visitor_short = element_text(tr, './td[@data-stat="visitor_team_name"]/a/@href')
            visitor_short = re.search(r'\/teams\/(\w+)', visitor_short).groups()[0]
            game_meta['date'] = d_str

            if link:
                game_meta['game_id'] = re.search(r'\d+\w+', link).group()
                # yield rep.follow(link, self.parse_game_detail, meta={
                #     'game_info': game_meta, 'home': home_short, 'visitor': visitor_short})
            else:
                # 未开始赛程
                # 可以根据日期和主队组成 /boxscores/202401150LAL.html /teams/LAL/2024
                try:
                    game_meta['game_id'] = f'{parse(d_str).strftime("%Y%m%d")}0{home_short}'
                except ParserError:
                    game_meta['game_id'] = 'id_parse_error'
            yield GameItemLoader(GameScheduleItem(**game_meta)).load_item()

    
    def parse_game_detail(self, rep: HtmlResponse):
        """box scores 每天比赛详情可能会出现404, 网站未更新， 北京时间晚上9点后才有 
        https://www.basketball-reference.com/boxscores/200904180BOS.html
        比赛详细数据: 总统计,按节统计
        包含基础数据与进阶数据
        GameDetailListItem[GameDetailItem], GameDetailListQuaterItem[GameDetailQuaterItem]
        存储每一场比赛的详细数据(上场球员)
        最后 yield GameDetailListItem, GameDetailListQuaterItem
        减少 yield次数
        """
        
        game_meta = rep.meta['game_info']
        game_bs_item = GameScheduleItem(**game_meta) # game schedule
        home = rep.xpath('//div[@id="content"]/div[@class="scorebox"]/div[2]/div/strong/a/@href').get() 
        visitor = rep.xpath('//div[@id="content"]/div[@class="scorebox"]/div[1]/div/strong/a/@href').get()
        home = re.search(r'\/teams\/(\w+)', home).groups()[0] # home team short name
        visitor = re.search(r'\/teams\/(\w+)', visitor).groups()[0]  # visitor team short name
        
        
        game_title = rep.xpath('//div[@id="content"]/h1/text()').get()
        game_bs_item['home_pts'] = rep.xpath('//div[@id="content"]/div[@class="scorebox"]/div[2]/div[@class="scores"]/div/text()').get() 
        game_bs_item['visitor_pts'] = rep.xpath('//div[@id="content"]/div[@class="scorebox"]/div[1]/div[@class="scores"]/div/text()').get()
        game_bs_item['attendance'] = rep.xpath('//div[@id="content"]/div[not(@class)]/div[3]/text()').get()
        
        # 较新的赛季进入详情页才能知道是否为:季后赛
        title_pattern = re.compile(r'(Eastern Conference|Western Conference|Finals) (First Round |Semifinals |Finals )?Game (\d)')
        playoff_match = re.search(title_pattern, game_title)
        if playoff_match:
            game_bs_item['playoff_conference'] = playoff_match[1]
            if game_bs_item['playoff_conference'] != 'Finals':
                game_bs_item['playoff_round'] = playoff_match[2]
            game_bs_item['playoff_game'] = playoff_match[3]
        
        yield GameItemLoader(game_bs_item).load_item()
        
        # game details
        # tr[@data-row=[0,4]] 为首发
        # game basic: table[@id="box-{visitor}-game-basic"] -> GameDetailItem
        # game advanced: table[@id="box-{visitor}-game-advanced"] -> GameDetailItem
        
        vis_bs_trs = rep.xpath(f'//table[@id="box-{visitor}-game-basic"]/tbody/tr[not(@class)]')
        vis_adv_trs = rep.xpath(f'//table[@id="box-{visitor}-game-advanced"]/tbody/tr[not(@class)]')
        home_bs_trs = rep.xpath(f'//table[@id="box-{home}-game-basic"]/tbody/tr[not(@class)]')
        home_adv_trs = rep.xpath(f'//table[@id="box-{home}-game-advanced"]/tbody/tr[not(@class)]')
        home_info = {'team': game_meta['home'], 'date': game_meta['date'],
                     'game_id': game_meta['game_id'], 'season': game_meta['season']}
        vis_info = {'team': game_meta['visitor'], 'date': game_meta['date'],
                     'game_id': game_meta['game_id'], 'season': game_meta['season']}
        
        detail_list_data = []
        # visitor team:
        detail_list_data.extend(self.game_details(vis_bs_trs, vis_info, vis_adv_trs))
        # home team:
        detail_list_data.extend(self.game_details(home_bs_trs, home_info, home_adv_trs))
        detail_list_item = GameDetailListItem() 
        detail_list_item['data'] = detail_list_data
        yield detail_list_item
        
       
        # quaters: table[@id="box-MIN-q4-basic"] -> GameDetailQuaterItem
        quaters_name = rep.xpath('//div[@class="filter switcher"]/div[@class!="current"]/a/text()').getall()
        
        detail_quater_list_data = []
        for q in quaters_name:
            # print(q)
            # 排除半场统计
            quater_name = q.lower()
            if q not in ['H1', 'H2']:
                q_vis_trs = rep.xpath(f'//table[@id="box-{visitor}-{quater_name}-basic"]/tbody/tr[not(@class)]')
                q_home_trs = rep.xpath(f'//table[@id="box-{home}-{quater_name}-basic"]/tbody/tr[not(@class)]')
                
                detail_quater_list_data.extend(self.game_details(q_home_trs, home_info, None, q))
                detail_quater_list_data.extend(self.game_details(q_vis_trs, vis_info, None, q))
        # all quater
        detail_quater_list_item = GameDetailListQuaterItem()
        detail_quater_list_item['data'] = detail_quater_list_data
        yield detail_quater_list_item
        
class GameSpiderHis(NBASpider):
    """历史赛季比赛数据
    """
    name = 'GameSpiderHis'
    history = ':his'
    # prefix = 'Game'
    # db_file = 'nba_data_history.db' # 保存到SQLITE
    # if_exists = 'append' # dataframe to_sql mode: 'append' 'replace' 'fail'
    
    # start_urls = ['https://www.basketball-reference.com/leagues/NBA_2024_games-january.html']
    
    def start_requests(self) -> Iterable[Request]:
        
        
        # 每赛季分月份
        years = self.get_season_range()
        # years = [2016]
        for year in years:
            yield Request(f'https://www.basketball-reference.com/leagues/NBA_{year}_games.html', callback=self.parse_links)

            
    # def parse(self, rep):
    #     return self.parse_game(rep)
    #     # return self.parse_game_detail(rep)
    
    def parse_links(self, rep: HtmlResponse):
        """获取各月份赛程
        """
        months = rep.xpath('//div[@id="content"]/div[@class="filter"]/div/a/@href').getall()
        for i in months:
            yield rep.follow(rep.urljoin(i), self.parse_game)
            # print(rep.urljoin(i))
            # yield rep.follow(rep.urljoin(i), self.parse_game)
            
            
    def parse_game(self, rep: HtmlResponse):
        """获取当赛季赛程
        根据赛程跳转到详细数据页
        """
        html_parser = etree.HTML(rep.text)
        games_tr = html_parser.xpath('//table[@id="schedule"]/tbody/tr[not(@class)]')

        season = html_parser.xpath('//div[@id="meta"]/div[2]/h1/span/text()')[0]
        for tr in games_tr:
            game_meta = {}
            # game_meta['date'] = tr.xpath('./th[@data-stat="date_game"]')
            # 日期
            time = element_text(tr, './td[@data-stat="game_start_time"]/text()')
            d_str = time+','+element_text(tr, './th[@data-stat="date_game"]/a/text()')
            game_meta['visitor'] = element_text(tr, './td[@data-stat="visitor_team_name"]/a/text()')
            game_meta['visitor_pts'] = element_text(tr, './td[@data-stat="visitor_pts"]/text()')
            game_meta['home'] = element_text(tr, './td[@data-stat="home_team_name"]/a/text()')
            game_meta['home_pts'] = element_text(tr, './td[@data-stat="home_pts"]/text()')
            game_meta['attendance'] = element_text(tr, './td[@data-stat="attendance"]/text()')
            game_meta['arena'] = element_text(tr, './td[@data-stat="arena_name"]/text()')
            game_meta['note'] = element_text(tr, './td[@data-stat="game_remarks"]/text()')
            game_meta['season'] = season
            link = element_text(tr, './td[@data-stat="box_score_text"]/a/@href')
            
            # 根据球队缩写传到meta用于查找比赛详细数据
            home_short = element_text(tr, './td[@data-stat="home_team_name"]/a/@href')
            home_short = re.search(r'\/teams\/(\w+)', home_short).groups()[0]
            
            visitor_short = element_text(tr, './td[@data-stat="visitor_team_name"]/a/@href')
            visitor_short = re.search(r'\/teams\/(\w+)', visitor_short).groups()[0]
            game_meta['date'] = d_str

            if link:
                game_meta['game_id'] = re.search(r'\d+\w+', link).group()
                yield rep.follow(rep.urljoin(link), self.parse_game_detail, meta={
                    'game_info': game_meta, 'home': home_short, 'visitor': visitor_short})
                # print(rep.urljoin(link), ' ', d_str)
                # yield rep.follow(link, self.test_link, meta= {'game_info': game_meta})

    
    def test_link(self, rep: HtmlResponse):
        """_summary_

        Args:
            rep (HtmlResponse): _description_
        """
        game_meta = rep.meta['game_info']
        game_bs_item = GameScheduleItem(**game_meta)
        print(game_bs_item['date'])
        
     
    def parse_game_detail(self, rep: HtmlResponse, update=False):
        """box scores
        比赛详细数据: 总统计,按节统计
        包含基础数据与进阶数据
        """
        
        game_meta = rep.meta['game_info']
        game_bs_item = GameScheduleItem(**game_meta)
        home = rep.meta['home'] # home team short name
        visitor = rep.meta['visitor'] # visitor team short name
        
        game_title = rep.xpath('//div[@id="content"]/h1/text()').get()

        
        # 较新的赛季进入详情页才能知道是否为:季后赛
        title_pattern = re.compile(r'(Eastern Conference|Western Conference|Finals) (First Round |Semifinals |Finals )?Game (\d)')
        playoff_match = re.search(title_pattern, game_title)
        if playoff_match:
            game_bs_item['playoff_conference'] = playoff_match[1]
            if game_bs_item['playoff_conference'] != 'Finals':
                game_bs_item['playoff_round'] = playoff_match[2]
            game_bs_item['playoff_game'] = playoff_match[3]
        # 
        yield GameItemLoader(game_bs_item).load_item()
        
        # game details
        # tr[@data-row=[0,4]] 为首发
        # game basic: table[@id="box-{visitor}-game-basic"] -> GameDetailItem
        # game advanced: table[@id="box-{visitor}-game-advanced"] -> GameDetailItem
        
        vis_bs_trs = rep.xpath(f'//table[@id="box-{visitor}-game-basic"]/tbody/tr[not(@class)]')
        vis_adv_trs = rep.xpath(f'//table[@id="box-{visitor}-game-advanced"]/tbody/tr[not(@class)]')
        home_bs_trs = rep.xpath(f'//table[@id="box-{home}-game-basic"]/tbody/tr[not(@class)]')
        home_adv_trs = rep.xpath(f'//table[@id="box-{home}-game-advanced"]/tbody/tr[not(@class)]')
        home_info = {'team': game_meta['home'], 'date': game_meta['date'],
                     'game_id': game_meta['game_id'], 'season': game_meta['season']}
        vis_info = {'team': game_meta['visitor'], 'date': game_meta['date'],
                     'game_id': game_meta['game_id'], 'season': game_meta['season']}
        
        detail_list_data = []
        # visitor team:
        detail_list_data.extend(self.game_details(vis_bs_trs, vis_info, vis_adv_trs))
        # home team:
        detail_list_data.extend(self.game_details(home_bs_trs, home_info, home_adv_trs))
        detail_list_item = GameDetailListItem() 
        detail_list_item['data'] = detail_list_data
        yield detail_list_item
        
       
        # quaters: table[@id="box-MIN-q4-basic"] -> GameDetailQuaterItem
        quaters_name = rep.xpath('//div[@class="filter switcher"]/div[@class!="current"]/a/text()').getall()
        
        detail_quater_list_data = []
        for q in quaters_name:
            # print(q)
            # 排除半场统计
            quater_name = q.lower()
            if q not in ['H1', 'H2']:
                q_vis_trs = rep.xpath(f'//table[@id="box-{visitor}-{quater_name}-basic"]/tbody/tr[not(@class)]')
                q_home_trs = rep.xpath(f'//table[@id="box-{home}-{quater_name}-basic"]/tbody/tr[not(@class)]')
                
                detail_quater_list_data.extend(self.game_details(q_home_trs, home_info, None, q))
                detail_quater_list_data.extend(self.game_details(q_vis_trs, vis_info, None, q))
        # all quater
        detail_quater_list_item = GameDetailListQuaterItem()
        detail_quater_list_item['data'] = detail_quater_list_data
        yield detail_quater_list_item
            
