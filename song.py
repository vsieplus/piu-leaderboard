# song.py

class Song:
    BASE_URL = 'https://phoenix.piugame.com/leaderboard/over_ranking.php'

    def __init__(self, title, leaderboard_id, thumbnail_url):
        self.title = title
        self.leaderboard_id = leaderboard_id
        self.thumbnail_url = thumbnail_url

    def get_leaderboard_url(self) -> str:
        return f'{self.BASE_URL}?no={self.leaderboard_id}'
