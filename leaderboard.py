# leaderboard.py

import csv
import json
import os
import re

from typing import List
import discord

import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from crochet import setup, wait_for

from score import Score
from chart import Chart

setup()

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

        self.run_crawl(urls)

        await self.save()

    @wait_for(timeout=600.0)  # Adjust timeout as needed
    def run_crawl(self, urls):
        runner = CrawlerRunner(get_project_settings())
        for url, chart in urls.items():
            runner.crawl(LeaderboardCrawler, leaderboard_urls={ url : chart }, scores=self.scores)
        d = runner.join()  # This returns a Deferred that fires when all crawling jobs have finished.
        return d

    async def rescrape(self, chart_id: str) -> bool:
        """ Rescrape the leaderboard for a given chart.
        @param chart_id: the chart's ID
        @return: True if the chart was rescraped, False otherwise
        """
        chart_id = chart_id.lower()
        if chart_id in self.charts:
            await self.update(chart_id)
            return True

        return False

    async def query_score(self, player_id: str, chart_id: str) -> List[Score]:
        """ Query a player's score on a level.
        @param player_id: the player's ID, in the format of name[#tag]; If [#tag] is not specified, all players with the same name will be queried
        @param chart_id: the level's ID
        @return: list(Score) of all matching players' scores on the given level
        """
        if chart_id in self.scores:
            if '#' in player_id:
                return [value for key, value in self.scores[chart_id].items() if player_id.upper() == key]
            else:
                return [value for key, value in self.scores[chart_id].items() if player_id.upper() == key.split('#')[0]]

        return None

    async def query_rank(self, rank: int, chart_id: str) -> List[Score]:
        """ Query all scores with a given rank on a level.
        @param rank: the rank to query
        @param chart_id: the level's ID
        @return: list(Score) of all matching rank scores on the given level
        """
        # verify rank is between 1 and 100
        if rank < 1 or rank > 100:
            return None

        if chart_id in self.scores:
            scores = []
            i = 1
            for key, value in self.scores[chart_id].items():
                if rank == value['rank']:
                    scores.append(value)
                elif rank == i:
                    # score rank does not match actual rank, so there must be a tie with a higher rank
                    return await self.query_rank(value['rank'], chart_id)

                i += 1

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

    def __init__(self, guild_name: str):
        """ Initialize the guild's leaderboard.
        @param guild_name: the guild's name
        """
        self.players = set()
        self.players_file = os.path.join(SAVE_DIR, f'{guild_name}_{self.PLAYERS_SAVE_FILE}')
        if os.path.isfile(self.players_file):
            with open(self.players_file, 'r') as f:
                for line in f:
                    self.players.add(line.strip())

    async def add_player(self, player_id: str) -> bool:
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

    async def remove_player(self, player_id: str) -> bool:
        """ Remove a player from the guild's leaderboard. If the player is not being tracked, do nothing.
        @param player_id: the player's ID, in the format of name#tag
        @return: True if the player was removed, False otherwise
        """
        removed = player_id in self.players
        if removed:
            self.players.remove(player_id)

        await self.save()
        return removed

    async def get_leaderboard_updates(self, leaderboard: Leaderboard, channel: discord.TextChannel):
        """ Get the leaderboard updates for all the players being tracked in the guild.
        @param channel: the channel to send the updates to
        @return: None
        """
        for (new_score, prev_score) in leaderboard.updates:
            await channel.send(embed=new_score.embed(prev_score))

    async def save(self):
        with open(self.players_file, 'w', encoding='utf-8') as f:
            for player in self.players:
                f.write(f'{player}\n')

class LeaderboardCrawler(scrapy.Spider):
    name = 'leaderboard_spider'

    def __init__(self, leaderboard_urls: List[str], scores: dict):
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

        tie_count = 1
        previous_rank = 0
        previous_player_id = ''
        curr_tied_players = []

        ranking_list = response.xpath('//div[@class="rangking_list_w"]//ul[@class="list"]/li')

        for i, ranking in enumerate(ranking_list):
            ranking_info = ranking.xpath('.//div[@class="in flex vc wrap"]')

            rank = self.parse_rank(ranking_info)
            player_id = self.parse_player_id(ranking_info)
            score = self.parse_score(ranking_info)
            avatar_id = self.parse_avatar_id(ranking_info)
            date = self.parse_date(ranking)

            if rank == previous_rank:
                if tie_count == 1:
                    # make sure to count first tie
                    curr_tied_players.append(previous_player_id)

                curr_tied_players.append(player_id)
                tie_count += 1

            if i == len(ranking_list) - 1 or (rank != previous_rank and tie_count > 1):
                # set the tie count for all tied players
                for tied_player_id in curr_tied_players:
                    self.scores[chart['chart_id'].lower()][tied_player_id]['tie_count'] = tie_count

                # reset tie count
                tie_count = 1
                curr_tied_players = []

            self.scores[chart['chart_id'].lower()][player_id] = Score(chart, player_id, score, rank, 1, avatar_id, date)

            previous_rank = rank
            previous_player_id = player_id

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

    def parse_avatar_id(self, ranking) -> str:
        """ Parse the player's avatar ID.
        @param ranking: the ranking div
        @return: the player's avatar ID
        """
        profile_img = ranking.xpath('.//div[@class="profile_img"]//div[@class="resize"]//div[@class="re bgfix"]/@style').get()
        avatar_id =  re.search(r'(?<=background-image:url\(\'https://phoenix.piugame.com/data/avatar_img/)[0-9a-z]+(?=.png)', profile_img).group()

        return avatar_id

    def parse_date(self, ranking) -> str:
        """Parse the date the score was set.
        @param ranking: the ranking div
        @return: the date the score was set
        """
        return ranking.xpath('.//div[@class="date"]//i[@class="tt"]/text()').get()
