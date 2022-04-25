from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

import os
import re
import time
from datetime import datetime
import pandas as pd


class Search:
    def __init__(self):
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_LOCAL'] = '1'
        self.index = ['發文者', '文章標題', '發文日期', '發文時間', '圖片']
        self.total_pages = 10
        self.result = None
        self.domain = "https://www.ptt.cc"
        self.browser = webdriver.Chrome(ChromeDriverManager().install())
        self.targetURL = f"{self.domain}/bbs/Beauty/index.html"

    def data2df(self, data):  # data to Series and then to DataFrame
        series = pd.Series(data, index=self.index)

        return pd.DataFrame(series).T

    def detect_18page(self):
        print("確認是否為年齡詢問頁面！！")
        if len(self.browser.find_element(By.XPATH, "//div[@class='over18-notice']").text) > 0:
            print("確認目前頁面為年齡詢問頁面！！")
            print("點擊「我同意，我已年滿十八歲」")
            self.browser.find_element(By.XPATH, "//button[@value='yes']").click()
            time.sleep(5)

    def decode_listpage(self):
        article_urls = []

        # with open("00.html", encoding="utf-8") as f:
        #     soup = BeautifulSoup(f, 'html.parser')

        soup = BeautifulSoup(self.browser.page_source, 'html.parser')

        title_list = soup.find_all("div", {"class": "title"})
        for i in title_list:
            if "[公告]" in i.text.strip() or "(本文已被刪除)" in i.text.strip():
                continue
            else:
                article_url = self.domain + i.find("a").get("href")
                article_urls.append(article_url)

        return article_urls

    def decode_article(self):
        article_results = []
        pictures = []
        # with open("01.html", encoding="utf-8") as f:
        #     soup = BeautifulSoup(f, 'html.parser')

        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        article_data = soup.find_all("span", {"class": "article-meta-value"})

        for i, data in enumerate(article_data):
            if i == 0:  # 搜尋文章作者
                author = data.text.split(" ")[0]
                article_results.append(author)
            elif i == 2:  # 搜尋文章標題
                article_results.append(data.text)
            elif i == len(article_data)-1:  # 搜尋文章發佈日期
                time_list = data.text.split(" ")
                datestring = f"{time_list[1]} {time_list[2]}, {time_list[4]} {time_list[3]}"
                dateFormatter = "%b %d, %Y %H:%M:%S"
                date = str(datetime.strptime(datestring, dateFormatter)).split(" ")[0]
                time_ = str(datetime.strptime(datestring, dateFormatter)).split(" ")[1]
                article_results.append(date)
                article_results.append(time_)

        # 搜尋文章內的圖片
        picture_url = soup.find_all("a", {'href': re.compile('https:\/\/(imgur|i\.imgur)\.com\/*')})
        for i in picture_url:
            pictures.append(i['href'])

        article_results.append(pictures)

        self.browser.back()  # 返回上一頁
        time.sleep(5)

        return article_results

    def close(self):
        self.browser.quit()
        print("=" * 100)

    def search_mainindex(self):
        self.browser.get(self.targetURL)
        print("進入PTT！！")
        time.sleep(5)

        self.detect_18page()  # 檢查是否為18禁頁面

        # with open("01.html", "w", encoding="utf-8") as html:
        #     html.write(self.browser.page_source)

        for pages in range(self.total_pages):
            urls = self.decode_listpage()  # 分析list頁面個文章的URL
            print("=" * 100)
            print(urls)
            print("="*100)

            print(f"準備抓取第{pages + 1}頁文章內容")
            for i, url in enumerate(urls):
                self.browser.get(url)  # 前往list頁面的某一篇文章
                time.sleep(5)

                if pages == 0:  # 只有第一頁需要這樣做資料儲存
                    if i != 0:  # 除第一篇文章外其他文章
                        nonfitst_article_data = self.decode_article()
                        print(nonfitst_article_data)

                        nonfitst_article_data_df = self.data2df(nonfitst_article_data)
                        self.result = self.result.append(nonfitst_article_data_df, ignore_index=True)
                    else:  # 第一篇文章
                        first_article_data = self.decode_article()
                        print(first_article_data)

                        self.result = self.data2df(first_article_data)
                else:
                    nonfitst_article_data = self.decode_article()
                    print(nonfitst_article_data)

                    nonfitst_article_data_df = self.data2df(nonfitst_article_data)
                    self.result = self.result.append(nonfitst_article_data_df, ignore_index=True)

            print(f"第{pages + 1}頁文章內容抓取完畢")

            if pages != self.total_pages - 1:  # 最後一頁不需要繼續點擊上一頁
                self.browser.find_element(By.LINK_TEXT, "‹ 上頁").click()  # 點擊上一頁
                time.sleep(5)

        print(self.result)
        self.result.to_csv("PTT_Beauty.csv", index=False)

        self.close()
        print("PTT表特爬蟲結束")


if __name__ == "__main__":

    a = Search()
    a.search_mainindex()




