# NBA 数据爬取
时间：2023-24赛季

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
Scrapy

## 存储方式CSV
