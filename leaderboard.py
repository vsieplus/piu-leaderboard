# leaderboard.py

import csv
import json
import os

from score import Score
from chart import Chart

SAVE_DIR = 'data'

class Leaderboard:
    LEADERBOARD_SAVE_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')
    SONGLIST_SAVE_FILE = os.path.join(SAVE_DIR, 'songlist.csv')

    def __init__(self):
        # songs is dict of song_id : Song
        self.charts = dict()
        if os.path.isfile(self.SONGLIST_SAVE_FILE):
            with open(self.SONGLIST_SAVE_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chart = Chart(row['title'], row['mode'], row['level'], row['leaderboard_id'], row['thumbnail_url'])
                    self.charts[chart.chart_id] = chart

        # scores is dict of { chart_id : dict of { player_id : Score } }
        if os.path.isfile(self.LEADERBOARD_SAVE_FILE):
            with open(self.LEADERBOARD_SAVE_FILE, 'r') as f:
                self.scores = json.loads(f.read())
        else :
            self.scores = dict()

    def update(cls):
        """Update the entire leaderboard from the website."""
        pass

    def save(self):
        pass

class GuildLeaderboard:
    PLAYERS_SAVE_FILE = 'players.txt'

    def __init__(self, guild_name):
        self.players = set()
        self.players_file = os.path.join(self.SAVE_DIR, f'{guild_name}_{self.PLAYERS_SAVE_FILE}')
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

    def remove_player(self, player_id) -> bool:
        if player_id in self.players:
            self.players.remove(player_id)
            return True
        else:
            return False

    async def get_leaderboard_updates(self, channel):
        await channel.send('Updating leaderboard...')

    def query_score(self, player_id, level_id) -> Score:
        if level_id in self.scores:
            if player_id in self.scores[level_id]:
                return self.scores[level_id][player_id].rank

        return None

    def save(self):
        with open(self.players_file, 'w') as f:
            for player in self.players:
                f.write(f'{player}\n')