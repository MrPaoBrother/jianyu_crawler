# --*-- coding:utf8 --*--

from django.db import models

class JianYu(models.Model):
    class Meta:
        db_table = "jianyu"

    id = models.BigIntegerField(primary_key=True, auto_created=True)
    company_name = models.CharField(max_length=200, default="")
    link_id = models.CharField(max_length=200, default="")
    publish_time = models.CharField(max_length=100, default="")
    bid_time = models.CharField(max_length=100, default="")
    project_name = models.CharField(max_length=500, default="")
    bid_amount = models.CharField(max_length=200, default="0")
    article_url = models.CharField(max_length=500, default="")
    origin_article_url = models.CharField(max_length=500, default="")
    title = models.CharField(max_length=300, default="")
    labels = models.CharField(max_length=255, default="")
    content = models.TextField(default="")
    create_time = models.DateTimeField(auto_now_add=True)
    modify_time = models.DateTimeField(auto_now=True)
    extra = models.CharField(max_length=300, default='')
    article_type = models.IntegerField(default=0)