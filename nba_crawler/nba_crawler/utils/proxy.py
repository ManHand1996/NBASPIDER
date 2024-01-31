"""
使用https://github.com/jhao104/proxy_pool?tab=readme-ov-file
代理池
返回的不一定可以使用
"""
import requests
import re
from json import JSONDecodeError
import socket, socks
if __name__ != '__main__':
    from nba_crawler.settings import DEFAULT_PROXY



def get_proxy():
    """ proxy_pool
    Args:
        req (_type_): scrapy request object
    """
    
    try:
        proxy_obj = requests.get("http://127.0.0.1:5010/get/", proxies={}, timeout=1).json()
        proxy_prefix = 'http://'
        return proxy_prefix + proxy_obj['proxy']
    except JSONDecodeError:
        return DEFAULT_PROXY

def delete_proxy(proxy: str):
    """proxy_pool 
    """
    proxy = re.sub(r'https?:\/\/', '', proxy)
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy),  proxies={})


def get_random_proxy():
    """获取代理 from 'ProxyPool'
    """
    
    proxy_str = requests.get("http://127.0.0.1:5555/random", proxies={}, timeout=1).text
    if not proxy_str:
        return DEFAULT_PROXY
    return 'http://' + proxy_str

def del_proxy(proxy: str):
    """ProxyPool
    """
    requests.get(f'http://127.0.0.1:5555/del?proxy={proxy}', proxies={})


def geo_proxy():
    proxy_str = "socks4://140.250.150.56:1080"
    
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, "140.250.150.56", 1080)
    socket.socket = socks.socksocket
    
    rep = requests.get("https://www.baidu.com",
                        timeout=5
                       )
    print(rep.status_code)
    

if __name__ == '__main__':
    geo_proxy()