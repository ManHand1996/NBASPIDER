from lxml.etree import _Element
import re

def element_text(ele:_Element, xpath: str, join=False):
    r = ele.xpath(xpath)
    if r:
        return ','.join(r) if join else r[0]
    return ''


def search_text(pattern, text):
    p = re.compile(pattern=pattern)
    try:
        return re.search(p, text).groups() or (re.search(p, text).group(),)
    except AttributeError:
        return ('',)