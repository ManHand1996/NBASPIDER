"""
获取url
"""
import requests
from lxml import etree
from urllib.parse import urljoin

MAIN_URL = 'https://www.basketball-reference.com/leagues/NBA_2024.html'

def get_teams_urls():
    
    urls = []
    rep = requests.get(MAIN_URL)
    selector = etree.HTML(rep.content)

    east_eles = selector.xpath('//table[@id="confs_standings_E"]//a')
    west_eles = selector.xpath('//table[@id="confs_standings_W"]//a')
    for i in east_eles:
        urls.append((urljoin(MAIN_URL,i.get('href'))))
    for J in west_eles:
        urls.append(urljoin(MAIN_URL,J.get('href')))
    return urls
        
        
if __name__ == '__main__':
    get_teams_urls()