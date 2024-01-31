# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import inspect
import pandas as pd
from datetime import datetime
import json
import redis
# class UpdatePipeLine:
#     """
#     only work for spider.update_tables and spider.update_pipe == True
#     """
#     def process_item(self, item, spider):
#         table_name = item._table_name
        
#         # update_tables didn't store in df
#         if spider.update_pipe and table_name in spider.update_tables:
#             data = ItemAdapter(item).asdict()
#             sql_str = f"UPDATE {table_name} SET "
#             vals_sql = ','.join([f"{key}='{data[key]}'" for key in data.keys() if key not in item._keys])
#             where_sql = " where " + ' and '.join([f"{k}='{data[k]}'" for k in item._keys])
#             self.conn.execute(sql_str + vals_sql + where_sql)
#             self.conn.commit() # 是否可以一次性commit?
#         return item
    
#     def open_spider(self, spider):
#         self.conn = sqlite3.connect(spider.db_file)
        
    
#     def close_spider(self, spider):
#         self.conn.close()

# class SavePipeLine:
    
#     def process_item(self, item, spider):
#         table_name = item._table_name

#         # update_tables didn't store in df
#         if spider.update_pipe and table_name in spider.update_tables:
#             return item
        
#         data = ItemAdapter(item).asdict()
#         df = spider.df_objs[table_name]
#         df.loc[len(df)] = data
#         return item
    
#     def open_spider(self, spider):
#         """启动时(执行一次)
#         """
#         # 获取spider.db_file 存储路径文件
#         print("start SavePipeLine")
#         self.conn = sqlite3.connect(spider.db_file)
        
    
#     def close_spider(self, spider):
#         """爬虫退出时(执行一次)
#         """

#         # 退出时一次性保存
#         for table_name, df in spider.df_objs.items():
            
#             # update_tables didn't insert to 'table'
#             if len(df) == 0 or (spider.update_pipe and table_name in spider.update_tables):
#                 continue
            
            
#             df.to_sql(table_name, con=self.conn, if_exists=spider.if_exists, index=False)
#             self.conn.execute("insert into crawler_log (store_date, store_table) values(?,?)", 
#                             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),table_name))
#             self.conn.commit()
#             print(f'{table_name}:size:{len(df)}')

#         self.conn.close()
        
#     # @classmethod
#     # def from_crawler(cls, crawler):
#     #     """生成该对象时
#     #     """
#     #     return cls(
#     #         db_file=crawler.settings.get("SQLITE_DB")
#     #     )
    

class CSVSavePipeLine:
    
    def process_item(self, item, spider):
        data = ItemAdapter(item).asdict()
        
        with open(spider.db_file, 'ab') as f:
            row = ','.join([data[k] for k in spider.csv_headers]) + '\n'
            f.write(row.encode('utf-8'))
        return item
    
    def open_spider(self, spider):
        print('start CSVSavePipeLine')
        with open(spider.db_file, 'w') as f:
            f.write(','.join(spider.csv_headers) + '\n')
    

class RedisPipeLine:
    """数据量较大, 先存入redis, 爬取后结构化存储
    k(item._table_name): item.asdict().str
    """
    def __init__(self, redis_url) -> None:
        self.redis_url = redis_url
    
    
    def process_item(self, item, spider):
        """redis set key => item._table_name
            like: tb_game:his or tb_game
        """
        set_key = item._table_name + spider.history
        data = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        self.redis_conn.sadd(set_key, data)
        
        return item
    
    def open_spider(self, spider):
        self.redis_conn: redis.StrictRedis = redis.StrictRedis.from_url(self.redis_url)
        
        
    def close_spider(self, spider):
        self.redis_conn.close()
    
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
             redis_url=crawler.settings.get("REDIS_URL")
         )