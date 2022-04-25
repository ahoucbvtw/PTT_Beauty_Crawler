from ptt_Beauty.items import PttBeautyItem
from datetime import datetime
import logging
import scrapy
import re
from scrapy.http import FormRequest
from bs4 import BeautifulSoup


class PTTBeautySpider(scrapy.Spider):
    name = 'ptt_Beauty'
    allowed_domains = ['ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/Beauty/index.html']

    def __init__(self):
        self.page18_retries = 0
        self.page18_maxretries = 3
        self.crawl_pages = 0
        self.total_pages = 10
        self.result = None
        self.domain = "https://www.ptt.cc"

    def decode_listpage(self, response):
        article_urls = []

        soup = BeautifulSoup(response.body, 'html.parser')

        title_list = soup.find_all("div", {"class": "title"})
        for i in title_list:
            if "[公告]" in i.text.strip() or "(本文已被刪除)" in i.text.strip():
                continue
            else:
                article_url = self.domain + i.find("a").get("href")
                article_urls.append(article_url)

        nextpage = soup.find("div", {"class": "btn-group btn-group-paging"}).find_all("a")  # 搜尋下一頁URL

        button_group = {}
        for i in nextpage:
            try:
                button_group[i.text.strip()] = self.domain + i['href']
            except:
                button_group[i.text.strip()] = None

        return article_urls, button_group

    def parse(self, response):
        if len(response.xpath("//div[@class='over18-notice']")) > 0:
            logging.warning("確認目前頁面為年齡詢問頁面")

            if self.page18_retries < self.page18_maxretries:
                self.page18_retries += 1
                logging.warning("點擊「我同意，我已年滿十八歲」")

                # 利用 FormRequest 在遇到詢問頁時，為了盡量模擬人類的行為，所以決定真正的送出表單
                yield FormRequest.from_response(response,
                                                formdata={'yes': 'yes'},
                                                callback=self.parse)
            else:
                logging.warning('被擋在年齡詢問頁面')
        else:
            self.page18_retries = 0
            # # 儲存網頁
            # filename = response.url.split('/')[-2] + '.html'
            # with open(filename, 'wb') as f:
            #     f.write(response.body)

            # 尋找文章以及上一頁URL
            urls, button_group = self.decode_listpage(response)

            for href in urls:
                yield scrapy.Request(href, callback=self.parse_article)

            self.crawl_pages += 1
            if self.crawl_pages < self.total_pages:  # 利用這2變數確認停止爬蟲時機
                next_page = button_group["‹ 上頁"]

                if next_page:
                    logging.warning(f'前往上一頁URL: {next_page}')
                    yield scrapy.Request(next_page, callback=self.parse)

    def parse_article(self, response):  # 解析內文
        item = PttBeautyItem()
        pictures = []

        soup = BeautifulSoup(response.body, 'html.parser')
        article_data = soup.find_all("span", {"class": "article-meta-value"})

        for i, data in enumerate(article_data):
            if i == 0:  # 搜尋文章作者
                author = data.text.split(" ")[0]
                item['author'] = author

            elif i == 2:  # 搜尋文章標題
                item['article_title'] = data.text

            elif i == len(article_data) - 1:  # 搜尋文章發佈日期
                time_list = data.text.split(" ")
                datestring = f"{time_list[1]} {time_list[2]}, {time_list[4]} {time_list[3]}"
                dateFormatter = "%b %d, %Y %H:%M:%S"
                date = str(datetime.strptime(datestring, dateFormatter)).split(" ")[0]
                time_ = str(datetime.strptime(datestring, dateFormatter)).split(" ")[1]
                item['date'] = date
                item['time_'] = time_

        # 搜尋文章內的圖片
        picture_url = soup.find_all("a", {'href': re.compile('https:\/\/(imgur|i\.imgur|upload)\/*')})
        for i in picture_url:
            pictures.append(i['href'])

        item['picture_url'] = pictures

        print("=" * 100)

        yield item
