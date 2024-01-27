# leaderboard.py

import asyncio
import concurrent.futures
import csv
import json
import os
from typing import List, Set

from crochet import setup, wait_for
from fuzzywuzzy import process
from discord.ext import commands
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings

from score import Score
from chart import Chart
from leaderboard_crawler import LeaderboardCrawler

setup()

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

MODES = [
    'Single',
    'Double',
    'Co-op',
]

class Leaderboard:
    LEADERBOARD_SAVE_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')
    SONGLIST_SAVE_FILE = os.path.join(SAVE_DIR, 'songlist.csv')

    def __init__(self):
        """Initialize the master leaderboard."""
        # chart is dict of { chart_id : Chart }
        self.charts = dict()
        if os.path.isfile(self.SONGLIST_SAVE_FILE):
            with open(self.SONGLIST_SAVE_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chart = Chart(title=row['title'], mode=row['mode'], level=row['level'], leaderboard_id=row['id'], thumbnail_url=row['thumbnail'])
                    self.charts[chart.chart_id.lower()] = chart

        # split chart ids into 3 batches to reduce the number of requests per batch
        self.curr_mode_idx = 0

        # scores is dict of { chart_id : dict of { player_id : Score } }
        if os.path.isfile(self.LEADERBOARD_SAVE_FILE):
            with open(self.LEADERBOARD_SAVE_FILE, 'r', encoding='utf-8') as f:
                self.scores = {
                    chart_id: { 
                        player_id: Score.from_dict(score, self.charts[chart_id] if chart_id in self.charts else None)
                        for player_id, score in chart_scores.items() 
                    }
                    for chart_id, chart_scores in json.load(f).items()
                }
        else :
            self.scores = dict()

        self.score_updates = []

    async def update(self, chart_id: str) -> bool:
        """ Update the leaderboard for a given chart.
        @param chart_id: the chart's ID, lowercase
        @return: None
        """
        urls = {}
        if chart_id is not None and chart_id in self.charts:
            chart = self.charts[chart_id]
            urls[chart.get_leaderboard_url()] = chart
        else:
            return False

        await self.crawl_in_thread(urls)
        await self.save()

        return True

    async def update_all(self):
        """ Update all chart leaderboards.
        @return: None
        """
        curr_mode = MODES[self.curr_mode_idx]
        self.curr_mode_idx = (self.curr_mode_idx + 1) % len(MODES)

        urls = { chart.get_leaderboard_url() : chart for chart in self.charts.values() if chart.mode == curr_mode }

        await self.crawl_in_thread(urls)
        await self.save()

    async def crawl_in_thread(self, urls: dict[str, Chart]):
        """ Run the leaderboard crawler in a thread.
        @param urls: dict of { url : Chart }
        @return: None
        """
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = loop.run_in_executor(executor, self.run_crawl, urls)
            await future

    @wait_for(timeout=600.0)
    def run_crawl(self, urls):
        self.score_updates.clear()

        runner = CrawlerRunner(get_project_settings())
        runner.crawl(LeaderboardCrawler, leaderboard_urls=urls, scores=self.scores, score_updates=self.score_updates)
        d = runner.join()  # returns a Deferred that fires when all crawling jobs have finished
        return d

    async def rescrape(self, bot: commands.Bot, ctx: commands.Context, chart_id: str) -> str:
        """ Rescrape the leaderboard for a given chart.
        @param chart_id: the chart's ID
        @return: the chart's ID if a viable match was found, None otherwise
        """
        chart_id = chart_id.lower()
        if chart_id in self.charts:
            if await self.update(chart_id):
                return chart_id
        else:
            best_matches = await self.get_best_matches(chart_id)
            if len(best_matches) > 0:
                best_matches_str = "\n".join([f"{i + 1}. {match[0].title()}" for i, match in enumerate(best_matches)])
                await ctx.send(f'Chart `{chart_id}` not found. Did you mean one of the following?\n'
                               f'```{best_matches_str}```')
            try:
                # Wait for a message from the user who invoked the command
                message = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                if message.content.isnumeric() and int(message.content) - 1 < len(best_matches):
                    chart_id = best_matches[int(message.content) - 1][0]
                    async with ctx.typing():
                        if await self.update(chart_id):
                            return chart_id
            except asyncio.TimeoutError:
                await ctx.send('Sorry, you took too long to respond.')

        return None

    async def get_best_matches(self, chart_id: str) -> List[tuple[str, int]]:
        """ Get the best matching chart ID for a given chart.
        @param chart_id: the chart's ID
        @return: the best matching chart IDs
        """
        return process.extractBests(chart_id, self.charts.keys(), score_cutoff=60, limit=10)

    async def query_score(self, player_ids: List[str], chart_id: str) -> List[Score]:
        """ Query a player's score on a level.
        @param player_ids: the player IDs, in the format of name[#tag]; If [#tag] is not specified, all players with the same name will be queried
        @param chart_id: the level's ID
        @return: list(Score) of all matching players' scores on the given level
        """
        chart_id = chart_id.lower()

        if chart_id in self.scores:
            scores = []
            for player_id in player_ids:
                if '#' in player_id:
                    scores.extend([value for key, value in self.scores[chart_id].items() if player_id.upper() == key])
                else:
                    scores.extend([value for key, value in self.scores[chart_id].items() if player_id.upper() == key.split('#')[0]])

            # sort scores by rank
            scores.sort(key=lambda score: score.rank)

            return scores

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

        chart_id = chart_id.lower()

        if chart_id in self.scores:
            scores = []
            i = 1
            for key, value in self.scores[chart_id].items():
                if rank == value.rank:
                    scores.append(value)
                elif rank == i:
                    # score rank does not match actual rank, so there must be a tie with a higher rank
                    return await self.query_rank(value.rank, chart_id)

                i += 1

            return scores

        return None

    async def get_score_updates(self, players: Set[str]) -> List[tuple[Score, Score]]:
        """ Get the leaderboard updates for all the players being tracked.
        @param players: the players to get updates for
        @return: list of (new_score, prev_score) tuples
        """
        updates = []
        for (new_score, prev_score) in self.score_updates:
            if new_score is not None and new_score.player in players:
                updates.append((new_score, prev_score))

        return updates

    async def save(self):
        """Save the leaderboard to a file in JSON format.
        @return: None
        """
        with open(self.LEADERBOARD_SAVE_FILE, 'w', encoding='utf-8') as f:
            f.write(
                json.dumps(
                    { chart_id: { player_id: score.to_dict() for player_id, score in chart_scores.items() }
                        for chart_id, chart_scores in self.scores.items() },
                    indent=2
                )
            )
