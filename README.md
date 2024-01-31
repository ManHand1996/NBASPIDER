# NBA 数据爬取
时间：2023-24赛季
ss
## 球员
基本信息：时间, 身高体重年龄等

比赛信息(来自Games)
    基本信息: 得分，篮板等
    高阶信息：效率值，有效命中率等

## 球队信息
基本信息：
Logo,时间，名称，分区(东西区),  教练，总经理，助教人员，球馆，观众人次, 比赛
球员名单
Totals 
Advanced


## 比赛Games *** 比赛信息为主
A VS B
详细比赛信息，包括分节(1-4节 和OT)
https://www.basketball-reference.com/boxscores/202310250NYK.html
GamesBase

GamesDetail
Q1
Q2
Q3
Q4
OT

爬取顺序：
当季球队信息是一次性获取的。
先获取球队 -> 球员
—> 比赛信息

## 技术栈
Scrapy sqlite pandas

mongodb?
redis?

## 存储方式
SQLITE

## 说明


https://www.basketball-reference.com/boxscores/202401210LAL.html

sp_xxx_his 获取历史赛季的数据
sp_xxx 获取最新赛季数据

sp_teams.py:
1.球队信息
2.球员名单
3.伤病名单
4.当季球队(球员) 场均数据(基础)

sp_games.py:
1.各队的赛程
2.每场比赛数据(总)
3.每次比赛数据(按节)


## 开发日志
2024-01-20
1.修改tb_team：
增加rank, conference
需要重新获取一次

2.sp_games_daily
赛程获取一次
更新每天的tb_game(赛程)
然后插入对应的详细数据


2024-01-24:

当赛季: team, games 已获取并通过测试
历史: 需要重新获取games

1.SQL表没有进阶数据, 需要重新获取tb_game_detail
    历史
    当前赛季 (完成)
2.历史数据赛程只有4月份，


'2007-08': 1310, 
'2005-06': 1310, 
'2010-11': 1306, 
'2013-14': 1259, 
'2008-09': 1310, 
'2003-04': 1241, 
'2006-07': 1304, 
'2002-03': 205, 
'2011-12': 776, 
'2009-10': 1305, 
'2012-13': 316,
 '2004-05': 7