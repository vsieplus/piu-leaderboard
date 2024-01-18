# chart.py

BASE_URL = 'https://phoenix.piugame.com/leaderboard/over_ranking_view.php'

MODE_ABBREV = {
    'Single': 'S',
    'Double': 'D',
    'Co-op' : 'Co-op'
}

def get_chart_id(title, mode, level) -> str:
    mode_txt = 'Unknown'
    if mode in MODE_ABBREV:
        mode_txt = MODE_ABBREV[mode]

    return f'{title} {mode_txt}{level}'

class Chart():
    def __init__(self, title: str, mode: str, level: str, leaderboard_id: str, thumbnail_url: str):
        self.title = title
        self.mode = mode
        self.level = level
        self.leaderboard_id = leaderboard_id
        self.thumbnail_url = thumbnail_url

        self.chart_id = get_chart_id(title, mode, level)

    def get_leaderboard_url(self) -> str:
        return f'{BASE_URL}?no={self.leaderboard_id}'
