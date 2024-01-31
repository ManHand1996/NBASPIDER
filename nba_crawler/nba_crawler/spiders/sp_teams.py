"""
TeamSpider, TeamSpiderHis
当赛季和历史赛季
    每支球队的信息
    TeamPerGame: 球队(球员)当赛季场均数据(基础数据)
    TeamRosterItem: 球队球员名单
    TeamInjuryItem: 球队伤病球员名单
    TeamItem: 各球队信息
"""

from scrapy import Request
from scrapy.http.response.html import HtmlResponse
from typing import Any, Iterable

from nba_crawler.utils.basespider import NBASpider

class TeamSpider(NBASpider):
    """当前赛季
    """
    name = 'TeamSpider'
    # prefix = 'Team'
    
    # db_file = 'nba_data.db' # 保存到SQLITE
    # if_exists = 'replace' # dataframe to_sql mode: 'append' 'replace' 'fail'
    
    def start_requests(self) -> Iterable[Request]:
        season_from = self.get_current_season()
        yield Request(f'https://www.basketball-reference.com/leagues/NBA_{season_from}.html', callback=self.parse) 
            
    
    def parse(self, rep: HtmlResponse):
        
        team_e_url = rep.xpath('//table[@id="divs_standings_E"]/tbody/tr/th/a')
        team_w_url = rep.xpath('//table[@id="divs_standings_W"]/tbody/tr/th/a')
        team_url = team_e_url + team_w_url
        # print(team_url)
        for i in team_url:
            conference = i.xpath('../../../../@id').get()[-1]
            conference = 'Eastern' if conference == 'E' else 'Western'
            yield rep.follow(rep.urljoin(i.attrib['href']), self.parse_team, meta={'conference': conference})
        

class TeamSpiderHis(NBASpider):
    """历史赛季
    """
    name = 'TeamSpiderHis'
    history = ':his'
    # 已爬取2023-2000
    
    # prefix = 'Team'
    # db_file = 'nba_data_history.db' # 保存到SQLITE
    # if_exists = 'append' # dataframe to_sql mode: 'append' 'replace' 'fail'
    
    def start_requests(self) -> Iterable[Request]:
        
        years = self.get_season_range()
            
        for i in years:
            yield Request(f'https://www.basketball-reference.com/leagues/NBA_{i}.html', callback=self.parse) 
            
    
    def parse(self, rep: HtmlResponse):
        
        team_e_url = rep.xpath('//table[@id="divs_standings_E"]/tbody/tr/th/a')
        team_w_url = rep.xpath('//table[@id="divs_standings_W"]/tbody/tr/th/a')
        team_url = team_e_url + team_w_url
        # print(team_url)
        for i in team_url:
            conference = i.xpath('../../../../@id').get()[-1]
            conference = 'Eastern' if conference == 'E' else 'Western'
            yield rep.follow(rep.urljoin(i.attrib['href']), self.parse_team, meta={'conference': conference})