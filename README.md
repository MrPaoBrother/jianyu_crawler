# 网络爬虫-剑鱼标讯

## 前言
* [剑鱼标讯](https://www.jianyu360.com/)，国内专业的招投标信息服务平台
剑鱼标讯基于云计算、大数据分析技术，通过移动端和PC端向用户提供招标搜索、招标订阅、拟建项目获取、项目关注等服务，帮助投标企业的管理、市场销售等人员随时随地掌握全国招标信息。

## 环境准备
* win10
* python2.7
* vscode
* chrome(version > 64.0) [如何查看chorme版本?](https://zhidao.baidu.com/question/439968677.html)

## 安装
### python库安装

```bash
$ pip install lxml
$ pip install pychrome
$ pip install pymysql
$ pip install django == 1.11.6
```

### mysql安装
* [mysql server 5.7安装](https://dev.mysql.com/downloads/mysql/5.7.html)
* [python mysql安装](https://blog.csdn.net/g8433373/article/details/90476493)
* [python连接mysql的几种姿势](https://foofish.net/python-mysql.html)

## 配置
* [配置PythonPath](https://blog.csdn.net/Tona_ZM/article/details/79463284), 将app_data目录配置为直接可以索引到的位置
* 配置```app_data/settings.py```
```python
db_name = "数据库名"

DATABASES = {
   db_name: {
       'ENGINE': 'django.db.backends.mysql',
       'NAME':   db_name,
       'USER': 'xxx',
       'PASSWORD': 'xxx',
       'HOST': '127.0.0.1',
       'PORT': 3306,
   }
}
```
* 在```jianyu```目录下的```settings.py```文件中配置cookie, 改成自己的就行
```python
cookies = {
    "limitSearchTextFlag": "yrsCQ1566113293866977775",
    "SESSIONID": "a86ee7a4a0f8495736f7c8a7b347cf4f3835988a",
    "Hm_lvt_72331746d85dcac3dac65202d103e5d9": "1566113367",
    "Hm_lpvt_72331746d85dcac3dac65202d103e5d9": "1566113958"
}
```
> 这个cookie是从app中抓到的, [如何使用fiddler抓取app接口?](https://www.cnblogs.com/yyhh/p/5140852.html)

## 运行
* 以下方式使用一个即可
### web+app抓取(推荐)
* web端抓取公司列表和文章link_id
* app端找到文章详情页链接 如何抓app数据
* 配置文件

```bash
$ cd jianyu
$ python handler.py
```

### web+chrome_headless
* mac使用参考[这里](https://blog.csdn.net/g8433373/article/details/79833471)\
* 先将chrome浏览器关闭
* win环境下 先使用cmd命令打开chrome

```bach
$ chrome.exe --remote-debugging-port=9222 --disable-gpu https://chromium.org
```
* 运行
```bash
$ cd handless_spider
$ python run_jianyu.py
```

## 存储
* ```app_data/models/entity.py```
* mysql建表语句(根据需求建自己的表)
```sql
CREATE TABLE `jianyu` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `company_name` varchar(200) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `link_id` varchar(200) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `publish_time` varchar(100) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `bid_time` varchar(100) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `project_name` varchar(500) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `bid_amount` varchar(200) CHARACTER SET utf8 NOT NULL DEFAULT '0',
  `article_url` varchar(500) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `origin_article_url` varchar(2000) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `title` varchar(300) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `labels` varchar(255) NOT NULL,
  `content` longtext NOT NULL,
  `create_time` datetime NOT NULL,
  `modify_time` datetime NOT NULL,
  `extra` varchar(255) CHARACTER SET utf8 NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
```
* 代码中使用django queryset的orm框架进行开发, 使用参考[官方文档](https://docs.djangoproject.com/en/2.2/ref/models/querysets/)

## 采坑过程
* 账号封禁特别厉害, 先封ip后账号(针对详情页)
    * 解决方法
        * 调整抓取速度, 失败后切换账号和ip(使用web+app的方式问题不大, 需要实时更新cookie)
        * web端抓取linkid, app端抓包 通过cookie伪造

* chrome_headless抓取慢问题
    * 速度快了很快就被封了, 调整慢了也没用, 估计网站做了账号级别的访问计数...
    * 使用第二种方法需要对内核比较了解, 重点需要看下[chrome开发者协议](https://chromedevtools.github.io/devtools-protocol/)
* mysql存储注意对content字段进行long_text的存储, 不然too long 错误...

## 参考资料
[1] [Fiddler 抓包](https://www.cnblogs.com/yyhh/p/5140852.html)
[2] [python连接mysql](https://foofish.net/python-mysql.html)
[3] [ChromeHeadless使用](https://blog.csdn.net/g8433373/article/details/79833471)
[4] [Chrome开发者协议](https://chromedevtools.github.io/devtools-protocol/)
[5] [PostMan官方文档](https://learning.getpostman.com/docs/postman/launching_postman/installation_and_updates/)