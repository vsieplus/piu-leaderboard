# leaderboard.py

import csv
import json
import os

import scrapy
from scrapy.crawler import CrawlerProcess

from score import Score
from chart import Chart

SAVE_DIR = 'data'

class Leaderboard:
    LEADERBOARD_SAVE_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')
    SONGLIST_SAVE_FILE = os.path.join(SAVE_DIR, 'songlist.csv')

    def __init__(self):
        # chart is dict of song_id : Chart
        self.charts = dict()
        if os.path.isfile(self.SONGLIST_SAVE_FILE):
            with open(self.SONGLIST_SAVE_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chart = Chart(row['title'], row['mode'], row['level'], row['id'], row['thumbnail'])
                    self.charts[chart.chart_id] = chart

        # scores is dict of { chart_id : dict of { player_id : Score } }
        if os.path.isfile(self.LEADERBOARD_SAVE_FILE):
            with open(self.LEADERBOARD_SAVE_FILE, 'r') as f:
                self.scores = json.loads(f.read())
        else :
            self.scores = dict()

    def update(self):
        """Update the entire leaderboard from the website."""
        for chart in self.charts.values():
            process = CrawlerProcess()
            process.crawl(LeaderboardCrawler, leaderboard_url=chart.get_leaderboard_url(), scores=self.scores)
            process.start()

        self.save()

    def query_score(self, player_id, level_id) -> Score:
        if level_id in self.scores:
            if player_id in self.scores[level_id]:
                return self.scores[level_id][player_id].rank

        return None

    def save(self):
        with open(self.LEADERBOARD_SAVE_FILE, 'w') as f:
            f.write(json.dumps(self.scores))

class GuildLeaderboard:
    PLAYERS_SAVE_FILE = 'players.txt'

    def __init__(self, guild_name):
        self.players = set()
        self.players_file = os.path.join(SAVE_DIR, f'{guild_name}_{self.PLAYERS_SAVE_FILE}')
        if os.path.isfile(self.players_file):
            with open(self.players_file, 'r') as f:
                for line in f:
                    self.players.add(line.strip())

    def add_player(self, player_id) -> bool:
        if player_id not in self.players:
            self.players.add(player_id)
            return True
        else:
            return False

        self.save()

    def remove_player(self, player_id) -> bool:
        if player_id in self.players:
            self.players.remove(player_id)
            return True
        else:
            return False

        self.save()

    async def get_leaderboard_updates(self, channel):
        await channel.send('Updating leaderboard...')

    def save(self):
        with open(self.players_file, 'w') as f:
            for player in self.players:
                f.write(f'{player}\n')

class LeaderboardCrawler(scrapy.Spider):
    name = 'leaderboard_spider'

    def __init__(self, leaderboard_url, scores):
        self.start_urls = [leaderboard_url]
        self.scores = scores

    def parse(self, response):
        ranking_list = response.xpath('//div[@class="rangking_list_w"]//ul[@class="list"]/li')
        for ranking in ranking_list:
            player_info = ranking.xpath('//div[@class="in flex vc wrap"]')

            player_num = player_info.xpath('//div[@class="num"]')
            rank = player_num.xpath('//i[@class="tt"]/text()').get()
            if rank is None:
                rank_image_path = player_num.xpath('//div[@class="img_wrap"]//span[@class="medal_wrap"]//i[@class="img"]//img/@src]').get()

                if 'goldmedal' in rank_image_path:
                    rank = 1
                elif 'silvermedal' in rank_image_path:
                    rank = 2
                elif 'bronzemedal' in rank_image_path:
                    rank = 3
                else:
                    rank = 0
            else:
                rank = int(rank)

            player_name = player_info.xpath('//div[@class="name flex vc wrap"]//div[@class="name_w"]')
            name = player_name.xpath('//div[@class="profile_name en"]/text()')
            tag = player_name.xpath('//div[@class="profile_name st1 en"]/text()')
            player_id = f'{name}{tag}'

            score = player_info.xpath('//div[@class="in_layOut flex vc wrap mgL"]//div[@class="score"]//i[@class="tt en"]/text()')

            date = ranking.xpath('//div[@class="date"]//i[@class="tt"]/text()').get()

            breakpoint()

            self.scores[self.chart.chart_id][player_id] = Score(self.chart, player_id, score, rank, date)