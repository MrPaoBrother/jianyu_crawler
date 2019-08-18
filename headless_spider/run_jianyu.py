# -*- coding:utf8 -*-

import sys
from chrome_spider import ChromeSpider
import settings
from datetime import datetime
import django
import os
import time
import codecs
from lxml import etree
os.environ['DJANGO_SETTINGS_MODULE'] = 'app_data.settings'
django.setup()
from app_data.models.entity import JianYu
import random

def write_to_file(path, data):
    with open(path, 'wb') as fs:
        fs.write(data.encode("utf8"))

def read_file(file_path):
    with codecs.open(file_path, 'r', encoding='utf-8') as fs:
        return "".join(fs.readlines())

def parse_dom_data(dom_data):
    if len(dom_data) < 1:
        return ""

    return dom_data[0]

def get_labels(dom):
    area = parse_dom_data(dom.xpath('//div[@id="statusbar"]//span[@class="com-area"]//a/text()'))
    tp = parse_dom_data(dom.xpath('//div[@id="statusbar"]//span[@class="com-type"]//a/text()'))
    industry = parse_dom_data(dom.xpath('//div[@id="statusbar"]//span[@class="com-industry"]//a/text()'))
    result = [item for item in [area, tp, industry] if item]
    return ";".join(result)

def get_content(dom):
    try:
        # return ''.join(dom.xpath('//div[@class="com-detail"]')[0].itertext()).encode("gbk", "ignore").decode("gbk")
        return dom.xpath('//div[@class="com-detail"]')[0].xpath('string(.)').strip().encode("gbk", "ignore").decode("gbk")
    except Exception as e:
        print "[get_content] error:%s" % str(e)
        return ""

def get_title(dom):
    data = parse_dom_data(dom.xpath('./head/title/text()')).split("-")
    if len(data) < 2:
        return ""
    return data[0]

def stringify_children(node):
    s = node.text
    if s is None:
        s = ''
    for child in node:
        s += etree.tostring(child, encoding='unicode')
    return s

def parse_html(html):
    dom = etree.HTML(html)
    title = get_title(dom)
    labels = get_labels(dom)
    content = get_content(dom)
    origin_url = parse_dom_data(dom.xpath('//div[@class="biddetail-content"]//div[@class="original-text"]//a[@class="com-original"]/@href')).encode("gbk", "ignore").decode("gbk")
    # for item in [title, labels, content, origin_url]:
    #     print item
    return title, labels, content, origin_url

def save(article):
    JianYu.objects.update_or_create(
        link_id = article.link_id,
        defaults = dict(
            title = article.title,
            labels = article.labels,
            content = article.content,
            origin_article_url = article.origin_article_url
        )
    )

def run(save_path, delay=4):
    
        articles = JianYu.objects.all()
        
        chrome_spider = ChromeSpider(**settings.CONF)
        download_count = 0
        while True:
            articles = [item for item in articles if not item.title]
            for article in articles:
                download_count += 1

                try:
                    if download_count % 10 == 0:
                        print "[run] current process: %s | %s" % (download_count, len(articles))

                    html = chrome_spider.download_html(url=article.article_url, delay=delay, close_tab=True)
                    title, labels, content, origin_article_url = parse_html(html)
                    if not title or not content:
                        # print "[run] company_name:%s title null retrying..." % article.company_name
                        print "[run] title null retrying..."
                        time.sleep(random.randint(1, 2))
                        continue

                    article.title = title
                    article.labels = labels
                    article.content = content
                    article.origin_article_url = origin_article_url
                    save(article)
                    # time.sleep(random.randint(2, 4))
                except Exception as e:
                    print "[run] error: %s" % str(e)

            time.sleep(10)

if __name__ == '__main__':
    save_path = "./data/jianyu/"
    run(save_path, delay=random.randint(2, 3))