import os, sys, argparse

import inspect
from scrapy.crawler import CrawlerProcess
from nba_crawler.utils.basespider import NBASpider
from nba_crawler.spiders.sp_games import GameSpider, GameSpiderHis
from nba_crawler.spiders.sp_teams import TeamSpider, TeamSpiderHis
from nba_crawler.spiders.sp_players import PlayerSpider, PlayerSpiderHis ,PlayerSummary
from scrapy.utils.project import get_project_settings


from global_settings import REDIS_UPDATE_GAME_KEY, REDIS_UPDATE_PLAYER_KEY

# REDIS_UPDATE_GAME_KEY = os.environ.get('REDIS_UPDATE_GAME_KEY', '') # 每天需要更新的每场比赛数据 ''
# REDIS_UPDATE_PLAYER_KEY = os.environ.get('REDIS_UPDATE_PLAYER_KEY', '') # 更新球员库

settings = get_project_settings()
settings.set('REDIS_UPDATE_GAME_KEY', REDIS_UPDATE_GAME_KEY )
settings.set('REDIS_UPDATE_PLAYER_KEY', REDIS_UPDATE_PLAYER_KEY)
print(os.environ.get("SCRAPY_SETTINGS_MODULE"))
# print(settings.get('NEWSPIDER_MODULE'))

def start_crawler(cls: NBASpider ,**kwargs):
    print(cls)
    print(kwargs)
    if 'His' in cls.__name__:
        try:
            kwargs['season_from'] = int(kwargs['season_from'])
            kwargs['season_to'] = int(kwargs['season_to'])
        except ValueError:
            return
    # 添加爬取日志.
    process = CrawlerProcess(settings=settings)
    process.crawl(cls, **kwargs)
    
    process.start()

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--name', '--name', help='spider class name', required=True, type=str)
    arg_parser.add_argument('-f', '--season_from', help='crawl history season from', default=0, type=int)
    arg_parser.add_argument('-t', '--season_to', help='crawl history season to', default=0, type=int)
    arg_parser.add_argument('-s', '--get_schedule', help='Game Spider get current season schedule', default=False, type=bool)
    cmd_args = arg_parser.parse_args()
    
    spider_cls_name = cmd_args.name
    
    season_from = getattr(cmd_args, 'season_from', '0')
    season_to = getattr(cmd_args, 'season_to', '0')
    get_schedule = getattr(cmd_args, 'get_schedule', False)
    spider_cls = [i[1] for i in inspect.getmembers(sys.modules[__name__], inspect.isclass) if i[0] == spider_cls_name]
    if len(spider_cls) == 0:
        print('Spider Class Name Not Found')
        return
    start_crawler(spider_cls[0], **{'season_from': season_from, 'season_to': season_to, 'get_schedule': get_schedule})
    
    

if __name__ == "__main__":
    main()
# 已获取
#start_crawler(process=process,cls=GameHisSpider, season_from=2017, season_to=2019)
# start_crawler(process=process,cls=GameSpiderHis, season_from=2014, season_to=2017)
# # start_crawler(process=process,cls=TeamSpider, season_from=2024, season_to=2024)
# 2024-01-28：2010,2011-2013

# process.start()

# from scrapy import cmdline

# cmdline.execute("scrapy crawl NBAGameHistory".split())
