"""
使用https://github.com/jhao104/proxy_pool?tab=readme-ov-file
代理池
返回的不一定可以使用
"""
import requests
import re
import urllib3
def get_proxy():
    """获取代理
    Args:
        req (_type_): scrapy request object
    """
    proxy_obj = requests.get("http://127.0.0.1:5010/get/", proxies={}).json()
    proxy_prefix = 'https://' if proxy_obj['https'] else 'http://'
    return proxy_prefix + proxy_obj['proxy']

def delete_proxy(proxy: str):
    proxy = re.sub(r'https?:\/\/', '', proxy)
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy),  proxies={})

