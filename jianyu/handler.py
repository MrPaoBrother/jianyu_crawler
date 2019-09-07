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

from Queue import Queue

task_queue = Queue()

class JianYuHandler(object):
    def __init__(self):
        self.company_names = [company.replace(" ", "").decode("utf8") for company in settings.company_names.split("\n") if company.replace(" ", "")]
    
    def tp_to_datetime(self, tp, ft = "%Y-%m-%d"):
        if not tp:
            return tp

        time_local = time.localtime(tp)
        return time.strftime(ft,time_local)

    def fetch_post_data(self, url, data, cookies=None, retry = 3):
        while retry > 0:
            try:
                resp = requests.post(url=url, data=data, headers= settings.headers, cookies=cookies)
                if not resp.status_code == 200:
                    print "[get_post_data] url:%s, status_code:%s, retry..." % (url, resp.status_code)
                    time.sleep(1)
                    continue

                return json.loads(resp.text)
            except Exception as e:
                retry -= 1
                print "[get_post_data] url:%s, exception:%s, retry..." % (url, str(e))
                time.sleep(1)
                continue
        return {}

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
    
    def fetch_jianyu_app_list(self, search_name):
        result = []
        current_page = 1
        has_next = True
        while has_next:
            data = self.fetch_post_data(settings.base_app_search_url, 
                {"searchname": search_name, "pageNum": current_page, "source":"app"}, cookies=settings.cookies)
            if not data.get("hasNextPage", "") or data.get("hasNextPage", "") == "false":
                has_next = False
            result += data.get("proList", [])
            current_page += 1

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
    def save_jianyu_app_list(self, company_name, items):
        for list_data in items:
            link_id = list_data.get("sourceinfoid", "")
            if not link_id:
                print "[save_jianyu_list] company_name:%s, list_data:%s" % (company_name, list_data)
                return
            publish_time = list_data.get("zbtime", 0)
            bid_time = list_data.get("jgtime", 0)
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
            article_type = article.article_type,
            defaults = dict(
                title = article.title,
                labels = article.labels,
                content = article.content,
                origin_article_url = article.origin_article_url
            )
        )
        del article

    def monitor_thread(self):
        while not task_queue.empty():
            print "[monitor] current queue size:%s" % (task_queue.qsize())
            time.sleep(1)

    def update_thread(self):
        while not task_queue.empty():
            if task_queue.qsize() < 1:
                time.sleep(0.1)
                continue
            task = task_queue.get()
            self.update_detail([task], need_print_process=False)

    def update_detail(self, objs, need_print_process=True):
        count = 0
        for obj in objs:
            count += 1
            if count % 10 == 0 and need_print_process:
                print "[update_detail] process: %s | %s" % (count, len(objs))
            try:
                html = self.fetch_detail(obj.link_id)
                # html = self.fetch_detail("ABCY2ZrcT0FKD07NFV4c3U8DzNfASB3V3xxKAUgOTpFY3xwGB1UCgY%3D")
                dom = etree.HTML(html)
                title = dom.xpath('//div[@id="title"]/text()')
                if not title:
                    title = obj.project_name
                else:
                    title = title[0].encode("gbk", "ignore").decode("gbk").replace(" ", "").replace("\n", "")
                labels = self.parse_labels(html)
                content = dom.xpath('//pre[@id="h_content"]')
                if content:
                    content = content[0].xpath('string(.)').strip().encode("gbk", "ignore").decode("gbk")
                else:
                    content = ""
                if dom.xpath('//div[@class="abs"]//a/@href'):
                    origin_article_url = dom.xpath('//div[@class="abs"]//a/@href')[0]
                else:
                    origin_article_url = ""

                if not obj.title:
                    obj.title = title
                if not obj.labels:
                    obj.labels = labels
                obj.content = content
                obj.origin_article_url = origin_article_url
                self.save(obj)
                del obj
                del html
                del dom
                del content
            except Exception as e:
                print "[update_detail] link_id:%s error:%s" % (obj.link_id, str(e))
            

    def fetch_list(self):
        for company in self.company_names:
            print "[fetch_list] fetching company:%s" % company
            result = self.fetch_jianyu_list(company)
            self.save_jianyu_list(company, result)

    def fetch_app_list(self):
        process = 0
        for company in self.company_names:
            process += 1
            try:
                print "[fetch_app_list] fetching company:%s, process:%s|%s" % (company, process, len(self.company_names))
                result = self.fetch_jianyu_app_list(company)
                self.save_jianyu_app_list(company, result)
            except Exception as e:
                print "[fetch_app_list] fetching, process:%s|%s error:%s" % (process, len(self.company_names), str(e))


    def fetch_super_list(self):
        import company
        import jianyu.settings as settings
        single_companies = [(item, settings.super_search_single) for item in company.super_single_companies.split("\n") if item.replace(" ", "").replace("\n", "")]
        bid_companies = [(item, settings.super_search_bid) for item in company.super_companies.split("\n") if item.replace(" ", "").replace("\n", "")]
        all_companies = single_companies + bid_companies
        count = 0
        for name, search_type in all_companies:
            count += 1
            print "[fetch_super_list] all process %s | %s" % (count, len(all_companies))
            data = {"searchvalue": name, "selectType":"title"}
            page_num = 1
            if search_type == settings.super_search_single:
                data["subtype"] = "单一"

            elif search_type == settings.super_search_bid:
                data["subtype"] = "中标"

            while True:
                data["pageNum"] = page_num
                print "[fetch_super_list] name:%s page %s" % (name, page_num)
                json_data = self.fetch_post_data(settings.base_super_list_url, data=data)
                data_list = json_data.get("list", [])
                for item in data_list:
                    jianyu = JianYu()
                    jianyu.company_name = name
                    jianyu.link_id = item.get("_id")
                    obj = JianYu.objects.filter(link_id=jianyu.link_id, article_type=search_type).first()

                    if obj:
                        continue
                    jianyu.publish_time = self.tp_to_datetime(item.get("publishtime"))
                    jianyu.bid_time = self.tp_to_datetime(item.get("bidopentime", ""))
                    jianyu.project_name = item.get("projectname", "")
                    jianyu.bid_amount = item.get("bidamount", 0)
                    jianyu.article_url = settings.base_article_url.format(link_id=item.get("_id"))
                    
                    jianyu.title = item.get("title")
                    jianyu.labels = ";".join([t for t in [item.get("area"), item.get("subtype"), item.get("industry")] if t])
                    jianyu.article_type = search_type
                    jianyu.save()

                if not json_data.get("hasNextPage"):
                    break

                page_num += 1

    def process(self):
        import threading
        import jianyu.settings as settings
        # self.fetch_app_list()
        objs = list(JianYu.objects.all())
        # objs = objs[40000: len(objs) - 1]
        # objs = [item for item in objs if not item.title or not item.content]
        # self.update_detail(objs)
        [task_queue.put(item) for item in objs if not item.title]
        print "[process] queue size init: %s" % task_queue.qsize()
        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=self.update_thread))
        threads.append(threading.Thread(target=self.monitor_thread))

        for thread in threads:
            thread.setDaemon(True)
            thread.start()

        while not task_queue.empty():
            time.sleep(10)

        time.sleep(10)
        print "[process] end"

handler = JianYuHandler()

if __name__ == "__main__":
    handler.process()