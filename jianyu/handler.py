# -*- coding:utf8 -*-

import jianyu.settings as settings
import requests
from requests.cookies import RequestsCookieJar

import json
import time
from lxml.html import etree
import django
import re
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'app_data.settings'
django.setup()
import codecs
from app_data.models.entity import JianYu

class JianYuHandler(object):
    def __init__(self):
        self.company_names = [company.replace(" ", "").decode("utf8") for company in settings.company_names.split("\n") if company.replace(" ", "")]
    
    def tp_to_datetime(self, tp, ft = "%Y-%m-%d"):
        if not tp:
            return tp

        time_local = time.localtime(tp)
        return time.strftime(ft,time_local)

    def fetch_post_data(self, url, data):
        while True:
            try:
                resp = requests.post(url=url, data=data, headers= settings.headers)
                if not resp.status_code == 200:
                    print "[get_post_data] url:%s, status_code:%s, retry..." % (url, resp.status_code)
                    time.sleep(1)
                    continue

                return json.loads(resp.text)
            except Exception as e:
                print "[get_post_data] url:%s, exception:%s, retry..." % (url, str(e))
                time.sleep(1)
                continue

    def fetch_jianyu_list(self, search_name):
        result = []
        data = self.fetch_post_data(settings.base_search_url, {"searchvalue": search_name, "currentPage": 1})
        total_page = data.get("totalPage", 1)
        result += data.get("list", [])
        if total_page == 1:
            return result

        for page in range(2, total_page+1):
            data = self.fetch_post_data(settings.base_search_url, {"searchvalue": search_name, "currentPage": page})
            result += data.get("list", [])
        return result
    def parse_data(self, data, is_int=False):
        if data == None:
            if is_int: return "0"
            return ""

        return data
    
    def save_jianyu_list(self, company_name, items):
        for list_data in items:
            link_id = list_data.get("linkid", "")
            if not link_id:
                print "[save_jianyu_list] company_name:%s, list_data:%s" % (company_name, list_data)
                return
            publish_time = self.tp_to_datetime(list_data.get("zbtime", 0))
            bid_time = self.tp_to_datetime(list_data.get("jgtime", 0))
            JianYu.objects.update_or_create(
                link_id = link_id,
                defaults = dict(
                    company_name = self.parse_data(company_name),
                    link_id = link_id,
                    publish_time = self.parse_data(publish_time),
                    bid_time = self.parse_data(bid_time),
                    project_name = self.parse_data(list_data.get("projectname", "")),
                    bid_amount = self.parse_data(list_data.get("bidamount", 0), True),
                    article_url = settings.base_article_url.format(link_id=link_id)
                )
            )

    def write_to_file(self, path, data):
        with open(path, 'wb') as fs:
            fs.write(data.encode("utf8"))

    def read_file(self, file_path):
        with codecs.open(file_path, 'r', encoding='utf-8') as fs:
            return "".join(fs.readlines())

    def fetch_detail(self, link_id):
        while True:
            try:
                url = settings.base_app_url.format(link_id=link_id)
                resp = requests.get(url, headers = settings.headers, cookies = settings.cookies)
                if not resp.text:
                    print "[fetch_detail] link_id:%s error:%s" % (link_id, "null resp.text")
                    time.sleep(3)
                    continue
                return resp.text
            except Exception as e:
                print "[fetch_detail] link_id:%s error:%s" % (link_id, str(e))
                time.sleep(1)

    def parse_labels(self, html):
        area = re.compile('var area="(.*?)";').findall(html)[0]
        article_type = re.compile('var type =.*?if.*?"(.*?)".*?', re.S).findall(html)[0]
        industry = re.compile('var industry = "(.*?)";').findall(html)[0]
        if not industry:
            industry = re.compile('var subscopeclass = "(.*?)";').findall(html)[0].split("_")[0]
        result = [item for item in [area, article_type, industry] if item.replace(" ", "")]
        return ";".join(result)

    def save(self, article):
        JianYu.objects.update_or_create(
            link_id = article.link_id,
            defaults = dict(
                title = article.title,
                labels = article.labels,
                content = article.content,
                origin_article_url = article.origin_article_url
            )
        )

    def update_detail(self, objs):
        count = 0
        for obj in objs:
            if count % 10 == 0:
                print "[update_detail] process: %s | %s" % (count, len(objs))
            
            # html = self.fetch_detail(obj.link_id)
            html = self.fetch_detail("ABCY2EBYDI%2FKDY7NHxhcHUJJzACHj1mZnB%2FKSgwPS8ecGlwGDNUCZA%3D")
            import pdb;pdb.set_trace()
            dom = etree.HTML(html)
            title = dom.xpath('//div[@id="title"]/text()')[0]
            title = title.encode("gbk", "ignore").decode("gbk").replace(" ", "").replace("\n", "")
            labels = self.parse_labels(html)
            content = dom.xpath('//pre[@id="h_content"]')[0].xpath('string(.)').strip().encode("gbk", "ignore").decode("gbk")
            origin_article_url = dom.xpath('//div[@class="abs"]//a/@href')[0]
            obj.title = title
            obj.labels = labels
            obj.content = content
            obj.origin_article_url = origin_article_url
            self.save(obj)
            count += 1
            return

    def fetch_list(self):
        for company in self.company_names:
            print "[fetch_list] fetching company:%s" % company
            result = self.fetch_jianyu_list(company)
            self.save_jianyu_list(company, result)

    def process(self):
        # self.fetch_list()
        objs = JianYu.objects.all()
        objs = [item for item in objs if not item.title or not item.content]
        self.update_detail(objs)

handler = JianYuHandler()

if __name__ == "__main__":
    handler.process()