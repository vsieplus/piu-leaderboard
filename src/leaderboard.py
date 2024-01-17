# leaderboard.py

import csv
import json
import os
from typing import List

from crochet import setup, wait_for
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from score import Score
from chart import Chart
from leaderboard_crawler import LeaderboardCrawler

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
