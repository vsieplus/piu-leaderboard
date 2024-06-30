# pumbility_crawler.py

import re
from typing import List

import scrapy

from piugame_crawler import PIUGAME_CRAWLER
from pumbility import Pumbility, PUMBILITY_LEADERBOARD_URL
from util import update_curr_tie_count, update_next_tie_count

class PumbilityCrawler(scrapy.Spider):
    name = 'pumbility_spider'
    start_urls = [PUMBILITY_LEADERBOARD_URL]

    def __init__(self, pumbility_ranking: dict[str, Pumbility]):
        """Initialize the pumbility crawler.
        @param pumbility_ranking: list of Pumbility objects
        @return: None
        """
        self.pumbility_ranking = pumbility_ranking

    def parse(self, response):
        self.pumbility_ranking.clear()

        tie_count = 1
        previous_rank = 0
        previous_player_id = ''
        curr_tied_players = []

        ranking_list = response.xpath('//ul[@class="list pumbilitySt"]/li')

        for i, ranking in enumerate(ranking_list):
            player_id = PIUGAME_CRAWLER.parse_player_id(ranking, pumbility=True)
            pumbility = PIUGAME_CRAWLER.parse_score(ranking)
            rank = PIUGAME_CRAWLER.parse_rank(ranking)
            title = PIUGAME_CRAWLER.parse_title(ranking)
            avatar_id = PIUGAME_CRAWLER.parse_avatar_id(ranking)
            date = PIUGAME_CRAWLER.parse_date(ranking)

            tie_count = update_curr_tie_count(tie_count, rank, previous_rank, player_id, previous_player_id, curr_tied_players)
            self.pumbility_ranking[player_id] = Pumbility(player_id=player_id, pumbility=pumbility, rank=rank, tie_count=tie_count, title=title, avatar_id=avatar_id, date=date)
            tie_count = update_next_tie_count(tie_count, rank, previous_rank, i, player_id, self.pumbility_ranking, ranking_list, curr_tied_players)
