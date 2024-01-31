"""
持久化到数据库
"""
import os
import inspect
import importlib.util
import sys
import redis
import sqlite3
import json
import pandas as pd
from typing import List, Literal
from nba_crawler.global_settings import REDIS_UPDATE_GAME_KEY, REDIS_UPDATE_PLAYER_KEY

BASE_PATH = os.path.dirname(__file__)
DB_PATH_HISTORY = os.path.join(BASE_PATH,'data', 'nba_data_history.db')
DB_PATH = os.path.join(BASE_PATH, 'data', 'nba_data.db')
NBA_CRAWLER_PATH = os.path.join(BASE_PATH, 'nba_crawler', 'nba_crawler') # 爬虫项目路径
REDIS_URL = 'redis://127.0.0.1:6379'
REDIS_MAX_POP = 100000

def get_table_infos(file_path, attr='_table_name'):
    """get spider item._table_name attribute
    """
    # 动态导入
    items_path = os.path.join(file_path, 'items.py')
    items_spec = importlib.util.spec_from_file_location('items', items_path)
    items_module = importlib.util.module_from_spec(items_spec)
    sys.modules[items_module.__name__] = items_module
    items_spec.loader.exec_module(items_module)
    
    
    items_cls = [i[1] for i in inspect.getmembers(items_module, inspect.isclass) 
                 if 'List' not in i[0] and getattr(i[1], attr, '') != '']
    
    return { getattr(t, attr, ''): {'name': getattr(t, attr, ''),'cols':list(t.fields.keys()), 'keys': t._keys} for t in items_cls }


def test_import(file_path):
    sys.path.insert(1, NBA_CRAWLER_PATH)
    print(sys.path)
    
    items_path = os.path.join(NBA_CRAWLER_PATH, 'nba_crawler' , 'items.py')
    items_spec = importlib.util.spec_from_file_location('items', items_path)
    items_module = importlib.util.module_from_spec(items_spec)
    sys.modules[items_module.__name__] = items_module
    items_spec.loader.exec_module(items_module)
    items_cls = [i[1] for i in inspect.getmembers(items_module, inspect.isclass) 
                 if 'List' not in i[0] and getattr(i[1], '_table_name', '') != '']
    print(items_cls)
    
    # print(sys.path)
    # print(sys.modules)
    # print(m2.__name__)


class RedisClient:
    _pool = None
    
    def __init__(self):
        self.conn: redis.StrictRedis = redis.Redis.from_pool(self._pool)
        
    def __new__(cls):
        if not cls._pool:
            cls.pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
        return super().__new__(cls)
    
    
    def __del__(self):
        self.conn.close()

    def read_set(self, redis_key=''):
        if redis_key == 'tb_all_player':
            data_set = self.conn.smembers(redis_key)
        else:
            data_set = self.conn.spop(redis_key, REDIS_MAX_POP)
        
        # test........
        # data_set = self.conn.smembers(redis_key)
        
        print(f'read: {redis_key} , {len(data_set)}')
        if not data_set:
            return None
        return data_set
    
    def write_set(self,redis_key, vals):
        self.conn.sadd(redis_key, *vals)


class SQLClient:
    
    def __init__(self, db_path) -> None:
        self.conn = sqlite3.connect(db_path)
    
    def execute(self, sql_str, *args):
        cursor = self.conn.cursor()
        cursor.execute(sql_str, *args)
        self.conn.commit()
        cursor.close()
    
    def __del__(self):
        self.conn.close()


def create_tables(sql_cli: SQLClient, tables, is_his=False):
    """create tables for sqlite database
    """
    
    for k, v in tables.items():
        if k == 'tb_all_player' and is_his:
            continue
        cols_str = ','.join([ f'{col} TEXT' for col in v['cols']])
        sql_cli.execute(f'CREATE TABLE IF NOT EXISTS {k} ({cols_str})')

    # tb_log 存储日志时间
    
    sql_cli.execute("""CREATE TABLE IF NOT EXISTS tb_log(
        table_name TEXT,
        crawler_date TEXT
    )
    """)


def update_insert(sql_cli: SQLClient ,table_info: dict, data_raw: List[dict]):
    """
    """
    vals_str = ','.join(['?' for k in data_raw[0].keys()])

    for data_row in data_raw:
        # (for i in range) is a generator not a list!!!
        # vals_parameter = (data_row[k] for k in data_row.keys())
        vals_parameter = tuple(data_row[k] for k in data_row.keys())
        cols_str = ','.join(data_row.keys())
        insert_sql = f'insert into {table_info["name"]}({cols_str}) values ({vals_str});' 
        
        keys = table_info['keys']
        where_sql = " where " + ' and '.join([f"{k}='{data_row[k]}'" for k in keys])
        del_sql = f"delete from {table_info['name']} {where_sql};"
        try:
            sql_cli.execute(del_sql)
            # 避免None对象变成字符串插入
            sql_cli.execute(insert_sql, vals_parameter)
        except ValueError:
            print('del_sql:', del_sql)
            print('insert_sql:', insert_sql)
            print('insert_parameter:', vals_parameter)
            raise ValueError


def write_to_sql(data_set: set, table_info: dict, sql_cli: SQLClient, is_his=False):
    if not data_set:
        return
    
    data_raw = []
    for i in data_set:
        data_raw.append(json.loads(i))
    
    
    table_name = table_info['name']
    oper = 'append'
    
    if table_name in ['tb_game_detail', 'tb_game_detail_quater']:
        # new_raw: 该场比赛的一个球员的详细数据
        # data_raw: 每场比赛详细数据(球员)
        new_raw = []
        [ new_raw.extend(d['data']) for d in data_raw]
        data_raw = new_raw
    
    elif not is_his:
        oper = 'replace'
        if table_name == 'tb_game':
            # 赛程更新或插入 -> 先删除再插入
            oper = 'update_del'
            
    print('write raws:',len(data_raw))
    if oper == 'append' or oper == 'replace':
        
        # tb_game_detail has no col TS
        df = pd.DataFrame(data=data_raw, columns=table_info['cols'])
        # print(df.loc[0])
        df.to_sql(table_name, sql_cli.conn, if_exists=oper, index=False)
    else:
        update_insert(sql_cli, table_info, data_raw)


def push_games_for_daily():
    """ 每天需要更新的比赛放入redis中,
    爬虫每天获取一次赛程
    """
    redis_cli = RedisClient()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = cursor.execute("SELECT * FROM tb_game where home_pts ='' and "+
                 "STRFTIME('%Y-%m-%d',date) <= STRFTIME('%Y-%m-%d', DATETIME('now', '-1 day'))").fetchall()
    
    # get <= 2024-01-18 
    # results = cursor.execute("SELECT * FROM tb_game where "+
    #              "STRFTIME('%Y-%m-%d',date) <= STRFTIME('%Y-%m-%d', DATETIME('2024-01-18'))").fetchall()
    rows = [json.dumps(dict(i), ensure_ascii=False) for i in results]
    print(rows)
    cursor.close()
    conn.close()
    redis_cli.write_set(REDIS_UPDATE_GAME_KEY, rows)

    
def store_to_history():
    redis_cli = RedisClient()
    
    sql_cli = SQLClient(DB_PATH_HISTORY)
    
    tables = get_table_infos(NBA_CRAWLER_PATH)
    
    create_tables(sql_cli, tables, True)
    
    print(tables.keys())
    
    for table, table_info in tables.items():
        data_set = redis_cli.read_set(table+":his")
        if data_set:
            write_to_sql(data_set, table_info, sql_cli, True)
            

def store_to():
    redis_cli = RedisClient()
    
    sql_cli = SQLClient(DB_PATH)
    
    tables = get_table_infos(NBA_CRAWLER_PATH)
    
    create_tables(sql_cli, tables)

    
    for table, table_info in tables.items():
        
        data_set = redis_cli.read_set(table)
        if data_set:
            write_to_sql(data_set, table_info, sql_cli)
    
def main():
    store_args = sys.argv
    if len(store_args) > 1 and store_args[1] == 'history':
        # print('call history store')
        store_to_history()
    elif len(store_args) > 1 and store_args[1] == 'schedule':
        push_games_for_daily()
    else:
        store_to()

if __name__ == '__main__':
    main()
    # redis_cli = RedisClient()
    # player_set = redis_cli.read_set('tb_all_player')
    # players = list(player_set)
    # l_players = [ json.loads(i) for i in player_set]
    # print(players[697:699])
    # print(l_players[697:699])