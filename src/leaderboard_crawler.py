# leaderboard_crawler.py

from typing import List

import scrapy

from chart import Chart
from score import Score

from piugame_crawler import PIUGAME_CRAWLER
from util import update_curr_tie_count, update_next_tie_count

class LeaderboardCrawler(scrapy.Spider):
    name = 'leaderboard_spider'

    def __init__(self, leaderboard_urls: dict[str, Chart], scores: dict, score_updates: List[tuple[Score, Score]]):
        """Initialize the leaderboard crawler.
        @param leaderboard_urls: dict of { url : Chart }
        @param scores: dict of { chart_id : dict of { player_id : Score } }
        @return: None
        """
        self.start_urls = leaderboard_urls.keys()
        self.charts = leaderboard_urls
        self.scores = scores
        self.score_updates = score_updates

    def parse(self, response):
        """Parse the leaderboard page.
        @param response: the response from the leaderboard page
        @return: None
        """
        chart = self.charts[response.request.meta['redirect_urls'][0] if 'redirect_urls' in response.request.meta else response.request.url]
        chart_key = chart.chart_id.lower()

        scores_dict = dict()

        tie_count = 1
        previous_rank = 0
        previous_player_id = ''
        curr_tied_players = []

        ranking_list = response.xpath('//div[@class="rangking_list_w"]//ul[@class="list"]/li')

        for i, ranking in enumerate(ranking_list):
            ranking_info = ranking.xpath('.//div[@class="in flex vc wrap"]')

            rank = PIUGAME_CRAWLER.parse_rank(ranking_info)
            player_id = PIUGAME_CRAWLER.parse_player_id(ranking_info, pumbility=False)
            score = PIUGAME_CRAWLER.parse_score(ranking_info)
            avatar_id = PIUGAME_CRAWLER.parse_avatar_id(ranking_info, pumbility=False)
            date = PIUGAME_CRAWLER.parse_date(ranking)

            tie_count = update_curr_tie_count(tie_count, rank, previous_rank, player_id, previous_player_id, curr_tied_players)
            scores_dict[player_id] = Score(chart=chart, player=player_id, score=score, rank=rank, tie_count=tie_count, avatar_id=avatar_id, date=date)
            tie_count = update_next_tie_count(tie_count, rank, previous_rank, i, player_id, scores_dict, ranking_list, curr_tied_players)

            previous_rank = rank
            previous_player_id = player_id

        # check for + store score updates if we have previous scores to compare to
        if chart_key in self.scores and len(self.scores[chart_key]) > 0:
            for player_id, score in scores_dict.items():
                if player_id in self.scores[chart_key]:
                    if score.score > self.scores[chart_key][player_id].score:
                        # score has been updated
                        self.score_updates.append((score, self.scores[chart_key][player_id]))
                else:
                    # new score
                    self.score_updates.append((score, None))

        self.scores[chart_key] = scores_dict
