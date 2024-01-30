# score.py

import discord

from chart import Chart
from emojis import AVATAR_EMOJIS, GRADE_EMOJIS, RANKING_EMOJIS

RANKING_SUFFIXES = {
    1 : 'st',
    2 : 'nd',
    3 : 'rd',
    4 : 'th',
    5 : 'th',
    6 : 'th',
    7 : 'th',
    8 : 'th',
    9 : 'th',
    0 : 'th',
}

MODE_COLORS = {
    'Single': discord.Color.red(),
    'Double': discord.Color.green(),
    'Co-op' : discord.Color.yellow()
}

MODE_ICON_URLS = {
    'Single': 'https://phoenix.piugame.com/l_img/stepball/full/s_bg.png',
    'Double': 'https://phoenix.piugame.com/l_img/stepball/full/d_bg.png',
    'Co-op' : 'https://phoenix.piugame.com/l_img/stepball/full/c_bg.png'
}

class Score():
    def __init__(self, chart: Chart, player: str, score: int, rank: int, tie_count: int, avatar_id: str, date: str):
        self.chart = chart
        self.player = player
        self.score = score
        self.grade = Score.calculate_grade(score)
        self.rank = rank
        self.tie_count = tie_count
        self.avatar_id = avatar_id
        self.date = date

    async def embed(self, prev_score: 'Score', compare: bool) -> discord.Embed:
        embed_color = MODE_COLORS[self.chart.mode] if self.chart.mode in MODE_COLORS else discord.Color.black()
        avatar_emoji = f'{AVATAR_EMOJIS[self.avatar_id]} ' if self.avatar_id in AVATAR_EMOJIS else ''

        embed =  discord.Embed(
            title=f'{avatar_emoji}{self.player}',
            description=await self.embed_description(prev_score, compare),
            color=embed_color,
        )

        icon_url = MODE_ICON_URLS[self.chart.mode] if self.chart.mode in MODE_ICON_URLS else None
        embed.set_author(name=self.chart.chart_id, url=self.chart.get_leaderboard_url(), icon_url=icon_url)
        embed.set_thumbnail(url=self.chart.thumbnail_url)
        embed.set_footer(text=f'Date • {self.date}')

        return embed

    async def embed_description(self, prev_score: 'Score', compare: bool) -> str:
        rank_emoji = f'{RANKING_EMOJIS[self.rank]} ' if self.rank in RANKING_EMOJIS else '<:graymedal:1196960956517982359> '
        grade_emoji = f'{GRADE_EMOJIS[self.grade]} ' if self.grade in GRADE_EMOJIS else ''

        rank_suffix = Score.get_rank_suffix(self.rank)
        tied_text = f' ({self.tie_count}-way tie)' if self.tie_count > 1 else ''
        formatted_score = format(self.score, ',')

        if prev_score is None:
            new_rank_text = ' (new)' if compare else ''
            return f'{rank_emoji}*{self.rank}{rank_suffix}*{new_rank_text}{tied_text}\n' \
                   f'{grade_emoji}*{formatted_score}*'
        else:
            prev_rank_suffix = Score.get_rank_suffix(prev_score.rank)
            prev_formatted_score = format(prev_score.score, ',')

            return f'{rank_emoji}*{prev_score.rank}{prev_rank_suffix}* -> *{self.rank}{rank_suffix}*{tied_text}\n' \
                   f'{grade_emoji}*{prev_formatted_score}* -> *{formatted_score}*'

    def to_dict(self) -> dict:
        return {
            'player' : self.player,
            'score' : self.score,
            'grade' : self.grade,
            'rank' : self.rank,
            'tie_count' : self.tie_count,
            'avatar_id' : self.avatar_id,
            'date' : self.date
        }

    @classmethod
    def from_dict(cls, data: dict, chart: Chart) -> 'Score':
        return cls(
            chart,
            data['player'],
            data['score'],
            data['rank'],
            data['tie_count'],
            data['avatar_id'],
            data['date'],
        )

    @classmethod
    def get_rank_suffix(cls, rank) -> str:
        if rank >= 11 and rank <= 13:
            return 'th'

        return RANKING_SUFFIXES[rank % 10]

    @classmethod
    def calculate_grade(cls, score: int) -> str:
        if score >= 995000:
            return 'SSS+'
        elif score >= 990000:
            return 'SSS'
        elif score >= 985000:
            return 'SS+'
        elif score >= 980000:
            return 'SS'
        elif score >= 975000:
            return 'S+'
        elif score >= 970000:
            return 'S'
        elif score >= 960000:
            return 'AAA+'
        elif score >= 950000:
            return 'AAA'
        elif score >= 925000:
            return 'AA+'
        elif score >= 900000:
            return 'AA'
        elif score >= 825000:
            return 'A+'
        elif score >= 750000:
            return 'A'
        elif score >= 700000:
            return 'B'
        elif score >= 600000:
            return 'C'
        elif score >= 450000:
            return 'D'
        else:
            return 'F'
