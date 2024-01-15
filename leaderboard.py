# leaderboard.py

import csv
import json
import os

from typing import List

import scrapy
from scrapy.crawler import CrawlerProcess

from score import Score
from chart import Chart

SAVE_DIR = 'data'

class Leaderboard:
    LEADERBOARD_SAVE_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')
    SONGLIST_SAVE_FILE = os.path.join(SAVE_DIR, 'songlist.csv')

    def __init__(self):
        """Initialize the master leaderboard."""
        # chart is dict of song_id : Chart
        self.charts = dict()
        if os.path.isfile(self.SONGLIST_SAVE_FILE):
            with open(self.SONGLIST_SAVE_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chart = Chart(row['title'], row['mode'], row['level'], row['id'], row['thumbnail'])
                    self.charts[chart['chart_id'].lower()] = chart

        # scores is dict of { chart_id : dict of { player_id : Score } }
        if os.path.isfile(self.LEADERBOARD_SAVE_FILE):
            with open(self.LEADERBOARD_SAVE_FILE, 'r', encoding='utf-8') as f:
                self.scores = json.loads(f.read())
        else :
            self.scores = dict()

    async def update(self, chart_id=None):
        """ Update the leaderboard(s)
        @param chart_id: the chart's ID, lowercase; if None, update all chart leaderboards
        @return: None
        """
        urls = {}
        if chart_id is not None:
            if chart_id in self.charts:
                chart = self.charts[chart_id]
                urls[chart.get_leaderboard_url()] = chart
            else:
                return
        else:
            for chart in self.charts.values():
                urls[chart.get_leaderboard_url()] = chart

        process = CrawlerProcess()
        process.crawl(LeaderboardCrawler, leaderboard_urls=urls, scores=self.scores)
        process.start()
        await self.save()

    async def query_score(self, player_id, chart_id) -> List[Score]:
        """ Query a player's score on a level.
        @param player_id: the player's ID, in the format of name[#tag]; If [#tag] is not specified, all players with the same name will be queried
        @param chart_id: the level's ID
        @return: list(Score) of all matching players' scores on the given level
        """
        # rescrape the scores for the given level
        chart_id = chart_id.lower()
        if chart_id in self.charts:
            await self.update(chart_id)
        else:
            return None

        if chart_id in self.scores:
            if '#' in player_id:
                return [value for key, value in self.scores[chart_id].items() if player_id.upper() == key]
            else:
                return [value for key, value in self.scores[chart_id].items() if player_id.upper() == key.split('#')[0]]

        return None

    async def query_rank(self, rank, chart_id) -> List[Score]:
        """ Query all scores with a given rank on a level.
        @param rank: the rank to query
        @param chart_id: the level's ID
        @return: list(Score) of all matching scores on the given level
        """
        # rescrape the scores for the given level
        chart_id = chart_id.lower()
        if chart_id in self.charts:
            await self.update(chart_id)
        else:
            return None

        if chart_id in self.scores:
            scores = []
            found = False
            for key, value in self.scores[chart_id].items():
                if rank == value['rank']:
                    scores.append(value)
                    found = True
                elif found:
                    # since the scores are sorted by rank, we can break once we've found all the scores with the given rank
                    break

            return scores

        return None

    async def save(self):
        """Save the leaderboard to a file in JSON format.
        @return: None
        """
        with open(self.LEADERBOARD_SAVE_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.scores, indent=2))

class GuildLeaderboard:
    PLAYERS_SAVE_FILE = 'players.txt'

    def __init__(self, guild_name):
        """ Initialize the guild's leaderboard.
        @param guild_name: the guild's name
        """
        self.players = set()
        self.players_file = os.path.join(SAVE_DIR, f'{guild_name}_{self.PLAYERS_SAVE_FILE}')
        if os.path.isfile(self.players_file):
            with open(self.players_file, 'r') as f:
                for line in f:
                    self.players.add(line.strip())

    async def add_player(self, player_id) -> bool:
        """ Add a player to the guild's leaderboard. If the player is already being tracked, do nothing.
        Players that are being tracked will have their leaderboard updates automatically sent to the guild's 'piu-leaderboard' channel.
        @param player_id: the player's ID, in the format of name#tag
        @return: True if the player was added, False otherwise
        """
        added = player_id not in self.players
        if added:
            self.players.add(player_id)

        await self.save()
        return added

    async def remove_player(self, player_id) -> bool:
        """ Remove a player from the guild's leaderboard. If the player is not being tracked, do nothing.
        @param player_id: the player's ID, in the format of name#tag
        @return: True if the player was removed, False otherwise
        """
        removed = player_id in self.players
        if removed:
            self.players.remove(player_id)

        await self.save()
        return removed

    async def get_leaderboard_updates(self, channel):
        """ Get the leaderboard updates for all the players being tracked in the guild.
        @param channel: the channel to send the updates to
        @return: None
        """
        await channel.send('Updating leaderboard...')

    async def save(self):
        with open(self.players_file, 'w', encoding='utf-8') as f:
            for player in self.players:
                f.write(f'{player}\n')

class LeaderboardCrawler(scrapy.Spider):
    name = 'leaderboard_spider'

    def __init__(self, leaderboard_urls, scores):
        """Initialize the leaderboard crawler.
        @param leaderboard_urls: dict of { url : Chart }
        @param scores: dict of { chart_id : dict of { player_id : Score } }
        @return: None
        """
        self.start_urls = leaderboard_urls.keys()
        self.charts = leaderboard_urls
        self.scores = scores

    def parse(self, response):
        """Parse the leaderboard page.
        @param response: the response from the leaderboard page
        @return: None
        """
        chart = self.charts[response.request.meta['redirect_urls'][0] if 'redirect_urls' in response.request.meta else response.request.url]
        self.scores[chart['chart_id'].lower()] = dict()

        ranking_list = response.xpath('//div[@class="rangking_list_w"]//ul[@class="list"]/li')
        for ranking in ranking_list:
            ranking_info = ranking.xpath('.//div[@class="in flex vc wrap"]')

            rank = self.parse_rank(ranking_info)
            player_id = self.parse_player_id(ranking_info)
            score = self.parse_score(ranking_info)
            date = self.parse_date(ranking)

            self.scores[chart['chart_id'].lower()][player_id] = Score(chart, player_id, score, rank, date)

    def parse_rank(self, ranking_info) -> int:
        """Parse the player's rank.
        @param ranking_info: the ranking info div
        @return: the player's rank
        """
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
        """Parse the player's ID.
        @param ranking_info: the ranking info div
        @return: the player's ID
        """
        player_name = ranking_info.xpath('.//div[@class="name flex vc wrap"]//div[@class="name_w"]')
        name = player_name.xpath('.//div[@class="profile_name en"]/text()').get()
        tag = player_name.xpath('.//div[@class="profile_name st1 en"]/text()').get()
        player_id = f'{name}{tag}'

        return player_id

    def parse_score(self, ranking_info) -> int:
        """Parse the player's score.
        @param ranking_info: the ranking info div
        @return: the player's score, or 0 if the player has no score
        """
        score = ranking_info.xpath('.//div[@class="in_layOut flex vc wrap mgL"]//div[@class="score"]//i[@class="tt en"]/text()').get()

        if score is None:
            return 0
        else:
            # remove commas from score
            return int(score.replace(',', ''))

    def parse_date(self, ranking) -> str:
        """Parse the date the score was set.
        @param ranking: the ranking div
        @return: the date the score was set
        """
        return ranking.xpath('.//div[@class="date"]//i[@class="tt"]/text()').get()
