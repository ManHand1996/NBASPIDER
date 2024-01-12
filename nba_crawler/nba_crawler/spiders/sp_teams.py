"""
每支球队的信息
基本信息：

"""

from scrapy import Spider
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urljoin
import re
from ..items import TeamPerGame, TeamRosterItem, TeamInjuryItem, TeamItem

class TeamSpider(Spider):
    name = 'NBATeamSpider'
    start_urls = [ 'https://www.basketball-reference.com/teams/POR/2024.html'
        # ,'https://www.basketball-reference.com/leagues/NBA_2024.html'
        ]
    
    
    def parse(self, rep: HtmlResponse):
        # team_e_url = rep.xpath('//table[@id="confs_standings_E"]/tbody/tr/th/a/@href').getall()
        # team_w_url = rep.xpath('//table[@id="confs_standings_W"]/tbody/tr/th/a/@href').getall()
        # team_url = team_e_url + team_w_url
       
        # for i in team_url:
        #     # print(i)
        #     yield rep.follow(rep.urljoin(i), self.parse_team)
        self.parse_team(rep)
        
        
        
            
    def parse_team(self, rep: HtmlResponse):
        xpath_start = '//div[@data-template="Partials/Teams/Summary"]'
        
        # 球队基本信息
        team_item = TeamItem()
        # xpath 方法
        team_item['logo'] = rep.css('img[src].teamlogo').get() # 球队Logo URL
        # 赛季，球队全程
        team_item['season'], team_item['team_name'], _ = rep.xpath(xpath_start + '/h1/span/text()').getall()
        team_item['team_short'] = re.search(r'teams\/[A-Z]{1,}',rep.url).group().replace('teams/', '')
        coach_selector = rep.xpath(xpath_start + '/p[4]/a')[0] # 主教练
        print('coach_selector:', coach_selector)
        team_item['coach'] = coach_selector.xpath('text()').get()
        team_item['coach_url'] = urljoin(rep.url, coach_selector.attrib['href'])
        
        executive_selector = rep.xpath(xpath_start + '/p[5]/a')[0]
        team_item['executive'] = executive_selector.xpath('text()').get() # 总经理
        team_item['executive_url'] =  urljoin(rep.url, executive_selector.attrib['href'])
        
        
        area_str =  ''.join(rep.xpath(xpath_start + '/p[11]/text()').getall()) # 球馆
        area_str = re.sub(r'\n\s*', '', area_str)
        re_g = re.match(r'([A-Za-z]+\s[A-Za-z]+)(\d+,?\d+)', area_str)
        if re_g:
            # 场馆与观看人次
            team_item['arena'],team_item['attendance']  = re_g.groups()
        yield team_item
        # css 方法
        # rep.css('div[data-template="Partials/Teams/Summary"] h1 span::text').getall()
        
        # 球员名单
        # @data-stat 全写number @aria-label 简写 No.
        
        roster_trs = rep.xpath('//table[@id="roster]/tbody/tr')
        for tr in roster_trs:
            roster_item = TeamRosterItem()
            roster_item['number'] = tr.xpath('/th[@data-stat="number"]/text()').get()
            roster_item['player_url']= tr.xpath('/td[@data-stat="player"]/a/@href').get()
            roster_item['player'] = tr.xpath('/td[@data-stat="player"]/a/text()').get()
            roster_item['positon'] = tr.xpath('/td[@data-stat="pos"]/text()').get()
            roster_item['height']  = tr.xpath('/td[@data-stat="height"]/text()').get()
            roster_item['weight'] = tr.xpath('/td[@data-stat="weight"]/text()').get()
            roster_item['birth_date'] = tr.xpath('/td[@data-stat="birth_date"]/text()').get()
            roster_item['birth_country'] = tr.xpath('/td[@data-stat="birth_country"]/span/text()').get()
            roster_item['exp'] = tr.xpath('/td[@data-stat="years_experience"]/text()').get()
            roster_item['college'] = tr.xpath('/td[@data-stat="college"]/a/text()').get()
            yield roster_item
            
        # 伤病名单
        injurys = rep.xpath('//table[@id="injuries"]/tbody/tr')
        
        for tr in injurys:
            in_item = TeamInjuryItem()
            tr_player = tr.xpath('/th[@data-stat="data-stat"]/a').get()
            in_item['player'] = tr_player.xpath('/text()').get()
            in_item['player_url'] = tr_player.attrib['href']
            in_item['team_name'] = team_item['team_name']
            in_item['season'] = team_item['season']
            in_item['date'] = tr.xpath('/td[@data-stat="date_update"]/text()').get()
            in_item['description'] = tr.xpath('/td[@data-stat="note"]/text()').get()
            yield in_item
        
        # 场均数据
        per_games = rep.xpath('//table[@id="per_game"]/tbody/tr')
        for tr in per_games:
            pg_item = TeamPerGame()
            pg_item['player'] = tr.xpath('/td[@data-stat="player"]/text()').get() # 球员
            pg_item['player_url'] = tr.xpath('/td[@data-stat="player"]a/@href').get() # 球员
            pg_item['GS'] = tr.xpath('/td[@data-stat="gs"]/text()').get() # 首发场次
            pg_item['G'] = tr.xpath('/td[@data-stat="g"]/text()').get() # 场次
            pg_item['MP'] = tr.xpath('/td[@data-stat="mp_per_g"]/text()').get() # 
            pg_item['FG'] = tr.xpath('/td[@data-stat="fg_per_g"]/text()').get() # 命中数
            pg_item['FGA'] = tr.xpath('/td[@data-stat="fga_per_g"]/text()').get() # 出手次数
            pg_item['FGPct'] = tr.xpath('/td[@data-stat="fg_pct"]/text()').get() # 命中率
            pg_item['ThreeP'] = tr.xpath('/td[@data-stat="fg3_per_g"]/text()').get() # 
            pg_item['ThreePA'] = tr.xpath('/td[@data-stat="fg3a_per_g"]/text()').get() # 
            pg_item['ThreePPct'] = tr.xpath('/td[@data-stat="fg3_pct"]/text()').get() # 
            pg_item['TwoP'] = tr.xpath('/td[@data-stat="fg2_per_g"]/text()').get() # 
            pg_item['TwoPA'] = tr.xpath('/td[@data-stat="fg2a_per_g"]/text()').get() # 
            pg_item['TwoPPct'] = tr.xpath('/td[@data-stat="fg2_pct"]/text()').get() # 
            pg_item['eFGPct'] = tr.xpath('/td[@data-stat="efg_pct"]/text()').get() # 有效命中率
            
            pg_item['FT'] = tr.xpath('/td[@data-stat="ft_per_g"]/text()').get() # 有效命中率
            pg_item['FTA'] = tr.xpath('/td[@data-stat="fta_per_g"]/text()').get() # 有效命中率
            pg_item['FTPct'] = tr.xpath('/td[@data-stat="ft_pct"]/text()').get() # 有效命中率
            pg_item['ORB'] = tr.xpath('/td[@data-stat="orb_per_g"]/text()').get() # 进攻篮板
            pg_item['DRB'] = tr.xpath('/td[@data-stat="drb_per_g"]/text()').get() # 防守篮板
            pg_item['TRB'] = tr.xpath('/td[@data-stat="trb_per_g"]/text()').get() # 防守篮板
            pg_item['AST'] = tr.xpath('/td[@data-stat="ast_per_g"]/text()').get() # 助攻
            pg_item['STL'] = tr.xpath('/td[@data-stat="stl_per_g"]/text()').get() # 抢断
            pg_item['BLK'] = tr.xpath('/td[@data-stat="blk_per_g"]/text()').get() # 盖帽
            pg_item['TOV'] = tr.xpath('/td[@data-stat="tov_per_g"]/text()').get() # 实物
            pg_item['PF'] = tr.xpath('/td[@data-stat="pf_per_g"]/text()').get() # 犯规
            pg_item['PTS'] = tr.xpath('/td[@data-stat="pts_per_g"]/text()').get() # 得分
            yield pg_item
        
        

