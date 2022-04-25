# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PttBeautyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    article_title = scrapy.Field()  # 文章標題
    author = scrapy.Field()  # 發文者
    date = scrapy.Field()  # 發文日期
    time_ = scrapy.Field()  # 發文時間
    picture_url = scrapy.Field()  # 圖片URL
    # url = scrapy.Field()  # 內文網址
