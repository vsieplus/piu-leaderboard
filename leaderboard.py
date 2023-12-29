# leaderboard.py

import os

from score import Score
from song import Song

class Leaderboard:
    LEADERBOARD_SAVE_FILE = 'leaderboard.json'
    PLAYERS_SAVE_FILE = 'players.txt'

    # scores is dict of song_id : level_id : dict of player_id : Score
    scores = dict()

    # songs is dict of song_id : Song
    songs = dict()

    @classmethod
    async def update(cls):
        """Update the entire leaderboard from the website."""
        pass

    def __init__(self, guild_name):
        self.players = set()
        self.players_file = os.path.join('data', f'{guild_name}_{self.PLAYERS_SAVE_FILE}')
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

    def update_leaderboard(self, channel):
        pass

    def save(self):
        with open(self.players_file, 'w') as f:
            for player in self.players:
                f.write(f'{player}\n')

    def query_score(self, player_id, level_id) -> Score:
        if level_id in self.scores:
            if player_id in self.scores[level_id]:
                return self.scores[level_id][player_id].rank

        return None


