"""
每支球队的信息
基本信息：

"""

from scrapy import Spider
from scrapy.http.response.html import HtmlResponse
from urllib.parse import urljoin
import re

class TeamSpider(Spider):
    name = 'NBATeams'
    start_urls = ['https://www.basketball-reference.com/teams/BOS/2024.html']
    
    def parse(self, rep: HtmlResponse):
        xpath_start = '//div[@data-template="Partials/Teams/Summary"]'
        
        # 球队基本信息
        
        # xpath 方法
        logo = rep.css('img[@class="teamlogo"]::attr("src")').get() # 球队Logo URL
        # 赛季，球队全程
        time_state, team_full_name, _ = rep.xpath(xpath_start + '/h1/span/text()').getall()
        coach_selector = rep.xpath(xpath_start + '/p[4]/a').get() # 主教练
        coach = coach_selector.xpath('text()').get()
        coach_url = urljoin(rep.url, coach_selector.attrib['href'])
        
        executive_selector = rep.xpath(xpath_start + '/p[5]/a').get()
        executive = executive_selector.xpath('text()').get() # 总经理
        executive_url =  urljoin(rep.url, executive_selector.attrib['href'])
        
        
        area_str =  rep.xpath(xpath_start + '/p[11]/text()').getall() # 球馆
        area_str = re.sub(r'\n\s*', '', area_str)
        re_g = re.match(r'([A-Za-z]+\s[A-Za-z]+)(\d+,?\d+)', area_str)
        if re_g:
            # 场馆与观看人次
            arena, attendance = re_g.groups()
        # css 方法
        # rep.css('div[data-template="Partials/Teams/Summary"] h1 span::text').getall()
        
        # 球员名单
        # @data-stat 全写number @aria-label 简写 No.
        roster_headers = rep.xpath('//table[@id="roster"]/thead/tr/th/@data-stat')
        roster_trs = rep.xpath('//table[@id="roster]/tbody/tr').getall()
        for tr in roster_trs:
            number = tr.xpath('/th[@data-stat="number"]/text()').get()
            player_url = tr.xpath('/td[@data-stat="player"]/a/@href').get()
            player = tr.xpath('/td[@data-stat="player"]/a/text()').get()
            positon = tr.xpath('/td[@data-stat="pos"]/text()').get()
            height = tr.xpath('/td[@data-stat="height"]/text()').get()
            weight = tr.xpath('/td[@data-stat="weight"]/text()').get()
            birth_date = tr.xpath('/td[@data-stat="birth_date"]/text()').get()
            birth_country = tr.xpath('/td[@data-stat="birth_country"]/span/text()').get()
            exp = tr.xpath('/td[@data-stat="years_experience"]/text()').get()
            college = tr.xpath('/td[@data-stat="college"]/a/text()').get()
        
        print('logo:',logo)
        

