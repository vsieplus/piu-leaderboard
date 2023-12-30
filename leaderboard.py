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
                    self.charts[chart['chart_id']] = chart

        # scores is dict of { chart_id : dict of { player_id : Score } }
        if os.path.isfile(self.LEADERBOARD_SAVE_FILE):
            with open(self.LEADERBOARD_SAVE_FILE, 'r') as f:
                self.scores = json.loads(f.read())
        else :
            self.scores = dict()

    def update(self):
        """Update the entire leaderboard from the website."""
        urls = {}
        for chart in self.charts.values():
            urls[chart.get_leaderboard_url()] = chart

        process = CrawlerProcess()
        process.crawl(LeaderboardCrawler, leaderboard_urls=urls, scores=self.scores)
        process.start()
        self.save()

    def query_score(self, player_id, level_id) -> Score:
        if level_id in self.scores:
            if player_id in self.scores[level_id]:
                return self.scores[level_id][player_id]

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

    def __init__(self, leaderboard_urls, scores):
        self.start_urls = leaderboard_urls.keys()
        self.charts = leaderboard_urls
        self.scores = scores

    def parse(self, response):
        chart = self.charts[response.request.meta['redirect_urls'][0]]
        self.scores[chart['chart_id']] = dict()

        ranking_list = response.xpath('//div[@class="rangking_list_w"]//ul[@class="list"]/li')
        for ranking in ranking_list:
            ranking_info = ranking.xpath('.//div[@class="in flex vc wrap"]')

            rank = self.parse_rank(ranking_info)
            player_id = self.parse_player_id(ranking_info)
            score = self.parse_score(ranking_info)
            date = self.parse_date(ranking)

            self.scores[chart['chart_id']][player_id] = Score(chart, player_id, score, rank, date)

    def parse_rank(self, ranking_info) -> int:
        player_num = ranking_info.xpath('.//div[@class="num"]')
        rank = player_num.xpath('.//i[@class="tt"]/text()').get()
        if rank is None:
            rank_image_path = player_num.xpath('.//div[@class="img_wrap"]//span[@class="medal_wrap"]//i[@class="img"]//img/@src').get()

            if rank_image_path is not None:
                if 'goldmedal' in rank_image_path:
                    rank = 1
                elif 'silvermedal' in rank_image_path:
                    rank = 2
                elif 'bronzemedal' in rank_image_path:
                    rank = 3
                else:
                    rank = 0
            else:
                rank = 0
        else:
            try:
                rank = int(rank)
            except ValueError:
                rank = 0

        return rank

    def parse_player_id(self, ranking_info) -> str:
        player_name = ranking_info.xpath('.//div[@class="name flex vc wrap"]//div[@class="name_w"]')
        name = player_name.xpath('.//div[@class="profile_name en"]/text()').get()
        tag = player_name.xpath('.//div[@class="profile_name st1 en"]/text()').get()
        player_id = f'{name}{tag}'

        return player_id

    def parse_score(self, ranking_info) -> int:
        return ranking_info.xpath('.//div[@class="in_layOut flex vc wrap mgL"]//div[@class="score"]//i[@class="tt en"]/text()').get()

    def parse_date(self, ranking) -> str:
        return ranking.xpath('.//div[@class="date"]//i[@class="tt"]/text()').get()
