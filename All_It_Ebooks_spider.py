#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author: time_thief

import csv
import os
import time
import requests
from fake_useragent import UserAgent
from lxml import etree


class AllItEbooksSpider:
    def _init_(self):
        self.base_url = "http://www.allitebooks.org/page/"
        self.User_Agent = UserAgent()
        # 创建csv文件对象
        self.save_csv_fp = open('IT_ebooks_save.csv', 'a', encoding='utf-8', newline='')
        # 创建csv写操作对象
        self.csv_writer = csv.writer(self.save_csv_fp)

    # 1.请求网页，获取原始字符串
    def get_response(self, url):
        # 每次获取网页数据都需要重新设置User-Agent
        headers = {
            "User-Agent": self.User_Agent.random
        }
        res = requests.get(url, headers=headers).text
        # print(res)
        return res

    # 2.拼接URL翻页
    def get_new_url(self, page):
        url = self.base_url+str(page)
        print('Downloading {} page:'.format(page) + url)
        data = self.get_response(url)
        return data

    # 3.分析数据，使用etree获取想要的信息
    def analysis_data(self, data):
        # 生成单页etree对象
        my_tree = etree.HTML(data)
        # 解析书本链接列表
        article_list = my_tree.xpath('//*[@id="main-content"]/div/article')
        # 若书本链接列表长度为0，则表明数据解析失败或已超出最后一页
        length = len(article_list)
        if length == 0:
            return 1
        # 迭代每一个书本链接
        for article in article_list:
            # 获取详情页链接
            detail_url = article.xpath('./div[2]/header/h2/a/@href')[0]
            # 获取详情页数据
            detail_data = self.get_response(detail_url)
            # 构建etree对象
            detail_tree = etree.HTML(detail_data)
            book_title = detail_tree.xpath('//*[@id="main-content"]/div/article/header/h1/text()')[0]
            book_author = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[1]/a/text()')
            if len(book_author) == 0:
                continue
            book_author = book_author[0]
            book_year = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[3]/text()')[0]
            book_page = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[4]/text()')[0]
            book_isbn = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[2]/text()')[0]
            book_category = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[8]/a/text()')[0]
            book_file_format = detail_tree.xpath('//*[@id="main-content"]/div/article/header/div/div[2]/dl/dd[7]/text()')[0]
            info_list = [book_title, book_author, book_year, book_page, book_isbn, book_category, book_file_format]
            down_list = detail_tree.xpath('//*[@class="download-links"]')
            url_list = []
            for down_url in down_list:
                url_list.append(down_url.xpath('./a/@href'))
            if self.download_books(book_category, url_list) == 1:
                continue
            self.save_csv(info_list)

    # 4.保存数据，保存成cvs
    def save_csv(self, info_list):
        self.csv_writer.writerow(info_list)
        print(info_list[0] + " is writen")

    # 5.保存书籍下载链接
    @staticmethod
    def download_books(category, url_list):
        # 创建路径
        book_path = ".\\" + category
        if not os.path.exists(book_path):
            os.mkdir(book_path)
        # 检测是否已经下载相应文件链接
        if os.path.exists(book_path + "\\" + category + ".txt"):
            with open(book_path + "\\" + category + ".txt", 'r') as url_file:
                lines = url_file.readlines()
                for line in lines:
                    if line.strip() == url_list[0][0]:
                        print('Already download!')
                        return 1
        # 如果并没有下载过当前文件，则保存所有文件下载链接
        with open(book_path + "\\" + category + ".txt", 'a') as url_file:
            for down_url in url_list:
                url_file.write(down_url[0] + '\n')
            return 0

    # 6.运行程序
    def start(self):
        self._init_()
        for page in range(1, 1000):
            data = self.get_new_url(page)
            # 有时会出现 etree对象生成失败的情况，缓冲3秒钟重新解析，如果函数返回1则表明当前页面解析错误
            try:
                if self.analysis_data(data) == 1:
                    break
            except Exception as e:
                print(e)
                time.sleep(3)
                if self.analysis_data(data) == 1:
                    break
        print("Done!")


if __name__ == "__main__":
    AllItEbooksSpider().start()
