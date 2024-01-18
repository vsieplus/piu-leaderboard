# songlist_crawler.py
# Run this script to scrape the leaderboard songlist from the website and save it to a CSV file.

import csv
import os
import re

import scrapy
from scrapy.crawler import CrawlerProcess

BASE_URL = 'https://phoenix.piugame.com/leaderboard/over_ranking.php'
START_URL = f'{BASE_URL}?&&page=1'
OUTPUT_FILE = os.path.join('data', 'songlist.csv')

MODE_PREFIX_DICT = {
    'c': 'Co-op',
    'd': 'Double',
    's': 'Single',
}

class SonglistCrawler(scrapy.Spider):
    name = 'songlist_crawler'
    start_urls = [START_URL]

    def __init__(self):
        self.songlist = []

    def parse(self, response):
        ranking_list = response.xpath('//ul[@class="rating_ranking_list flex wrap overRangking_st"]/li')
        for ranking in ranking_list:
            self.parse_ranking(ranking)

        page_buttons = response.xpath('.//div[@class="board_paging"]/button')
        follow_next = False
        for button in page_buttons:
            if follow_next:
                next_url_suffix = re.search(r'(?<=location\.href=\').+(?=\')', button.xpath('./@onclick').get()).group()
                next_page_url = f'{BASE_URL}{next_url_suffix}'
                yield response.follow(next_page_url, callback=self.parse)
            else:
                follow_next = button.xpath('./@class').get() == 'on'

        self.save()

    def parse_ranking(self, ranking):
        leaderbord_url = ranking.xpath('.//a[@class="in flex vc wrap"]/@href').get()
        leaderboard_id = re.search(r'(?<=over_ranking_view\.php\?no=).+', leaderbord_url).group()

        bg_image = ranking.xpath('.//div[@class="re img bgfix"]/@style').get()
        thumbnail_url = re.search(r'(?<=background-image:url\(\').+(?=\'\))', bg_image).group()

        title = ranking.xpath('.//div[@class="songName_w"]//p[@class="tt"]/text()').get()

        stepball = ranking.xpath('.//div[@class="stepBall_in flex vc col hc wrap bgfix cont"]')
        stepball_img = stepball.xpath('@style').get()
        mode_prefix =  re.search(r'(?<=background-image:url\(\'https://phoenix.piugame.com/l_img/stepball/full/)[cds](?=_bg.png)', stepball_img).group()
        mode = MODE_PREFIX_DICT[mode_prefix]

        level = ''
        level_imgs = stepball.xpath('.//div[@class="numw flex vc hc"]//div[@class="imG"]')
        for img in level_imgs:
            img_url = img.xpath(".//img/@src").get()
            level_num = re.search(r'(?<=https://phoenix.piugame.com/l_img/stepball/full/[cds]_num_)[0-9]+(?=\.png)', img_url)
            if level_num is not None:
                level += level_num.group()
            else:
                level += 'x'

        self.songlist.append({
            'title': title,
            'mode': mode,
            'level': level,
            'id': leaderboard_id,
            'thumbnail': thumbnail_url,
        })

    def save(self):
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'mode', 'level', 'id', 'thumbnail'])
            writer.writeheader()
            writer.writerows(self.songlist)

def main():
    process = CrawlerProcess()
    process.crawl(SonglistCrawler)
    process.start()

if __name__ == '__main__':
    main()
