# pumbility_crawler.py

import re
from typing import List

import scrapy

from piugame_crawler import PIUGAME_CRAWLER
from pumbility import Pumbility

PUMBILITY_LEADERBOARD_URL = 'https://piugame.com/leaderboard/pumbility_ranking.php'

class PumbilityCrawler(scrapy.Spider):
    name = 'pumbility_spider'
    start_urls = [PUMBILITY_LEADERBOARD_URL]

    def __init__(self, pumbility_ranking: List[Pumbility]):
        """Initialize the pumbility crawler.
        @param pumbility_ranking: list of Pumbility objects
        @return: None
        """
        self.pumbility_ranking = pumbility_ranking

    def parse(self, response):
        self.pumbility_ranking.clear()

        tie_count = 1

        ranking_list = response.xpath('//ul[@class="list pumbilitySt"]/li')

        for i, ranking in enumerate(ranking_list):
            player = PIUGAME_CRAWLER.parse_player_id(ranking, pumbility=True)
            pumbility = PIUGAME_CRAWLER.parse_score(ranking)
            rank = PIUGAME_CRAWLER.parse_rank(ranking)
            title = PIUGAME_CRAWLER.parse_title(ranking)
            avatar_id = PIUGAME_CRAWLER.parse_avatar_id(ranking)
            date = PIUGAME_CRAWLER.parse_date(ranking)

            self.pumbility_ranking.append(
                Pumbility(player=player,
                          pumbility=pumbility,
                          rank=rank,
                          tie_count=tie_count,
                          title=title,
                          avatar_id=avatar_id,
                          date=date)
            )

