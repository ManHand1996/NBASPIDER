# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import pandas as pd
class NbaCrawlerPipeline:
    def process_item(self, item, spider):
        return item


class SavePipeLine:
    
    def __init__(self, db_file) -> None:
        self.db_file = db_file
        
    
    def process_item(self, item, spider):
        table_name = item._table_name
        data = ItemAdapter(item).asdict()
        df = pd.DataFrame(data=data).reset_index()
        df.to_sql(table_name, self.conn, if_exists='append', index=False)
        return item
    
    def open_spider(self, spider):
        """启动时(执行一次)
        """
        self.conn = sqlite3.connect(self.db_file)
    
    def close_spider(self, spider):
        """爬虫退出时(执行一次)
        """
        self.conn.close()
    
    @classmethod
    def from_crawler(cls, crawler):
        """生成该对象时
        """
        return cls(
            db_file=crawler.settings.get("SQLITE_DB")
        )