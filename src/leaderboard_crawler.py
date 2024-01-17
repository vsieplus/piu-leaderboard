# leaderboard_crawler.py

import re
from typing import List

import scrapy

from score import Score

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
