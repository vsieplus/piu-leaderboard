# chart.py

BASE_URL = 'https://phoenix.piugame.com/leaderboard/over_ranking.php'

MODE_ABBREV = {
    'single': 'S',
    'double': 'D',
    'co-op' : 'Co-op'
}

class Chart:
    def __init__(self, title, mode, level, leaderboard_id, thumbnail_url):
        self.title = title
        self.mode = mode
        self.level = level
        self.chart_id = self.get_chart_id()
        self.leaderboard_id = leaderboard_id
        self.thumbnail_url = thumbnail_url

    def get_leaderboard_url(self) -> str:
        return f'{BASE_URL}?no={self.leaderboard_id}'

    def get_chart_id(self) -> str:
        mode_txt = 'Unknown'
        if self.mode in MODE_ABBREV:
            mode_txt = MODE_ABBREV[self.mode]

        return f'{self.chart.title} {mode_txt}{self.level}'
