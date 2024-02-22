# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals,Spider
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from .utils import proxy
import random
import logging
import redis

class NbaCrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class ProcessStatusMiddleware:
    
    def __init__(self, redis_url) -> None:
        self.redis_url = redis_url
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(redis_url=crawler.settings.get("REDIS_URL"))
    
    def spider_opened(self, spider):
        self.redis_conn: redis.StrictRedis = redis.StrictRedis.from_url(self.redis_url)
    
    def process_response(self, request, response, spider: Spider):
        req_cnt = spider.crawler.stats.get_value('downloader/request_count','0')
        rep_cnt = spider.crawler.stats.get_value('downloader/response_count','-1')
        spider.logger.info(f'ProcessStatus:response:{rep_cnt}, request:{req_cnt}')
        return response

class RandomUserAgent(object):

    def __init__(self,agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls,crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self,request,spider):

        request.headers.setdefault('User-Agent',random.choice(self.agents))


class ProxyMiddlerware:
    
    
    def process_request(self, request, spider):
        request.meta['proxy'] = proxy.get_proxy()
        # request.meta['proxy'] = 'http://127.0.0.1:7890'
    
class ProxyRetryMiddleware(RetryMiddleware):
    logger = logging.getLogger(__name__)
    def __init__(self, settings):
        super().__init__(settings)
        self.failed_path = settings.get('LOG_PATH')

    def process_response(self, request, response, spider):
        if request.meta.get("dont_retry", False):
            return response
        if response.status in self.retry_http_codes:
            proxy.delete_proxy(request.meta['proxy'])
            reason = response_status_message(response.status)
            request.meta['proxy'] = proxy.get_proxy()
            
            return self._retry(request, reason, spider) or response
        return response

    def _retry(self, request, reason, spider):
        rep = super()._retry(request, reason, spider)
        if not rep:
            self.logger.error(f'failed to retry request ({request.url})')
        return rep