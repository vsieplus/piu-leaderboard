# pumbility.py

import discord

from emojis import AVATAR_EMOJIS, RANKING_EMOJIS
from util import get_rank_suffix

PUMBILITY_LEADERBOARD_URL = 'https://piugame.com/leaderboard/pumbility_ranking.php'

class Pumbility():
    def __init__(self, player_id: str, pumbility: int, rank: int, tie_count: int, title: str, avatar_id: str, date: str):
        self.player_id = player_id
        self.pumbility = pumbility
        self.rank = rank
        self.tie_count = tie_count
        self.title = title
        self.avatar_id = avatar_id
        self.date = date

    async def embed(self, prev_pumbility: 'Pumbility', compare: bool) -> discord.Embed:
        embed_color = discord.Color.blue()
        avatar_emoji = f'{AVATAR_EMOJIS[self.avatar_id]} ' if self.avatar_id in AVATAR_EMOJIS else ''

        embed = discord.Embed(
            title=f'{avatar_emoji}{self.player_id}',
            description=await self.embed_description(prev_pumbility, compare),
            color=embed_color,
        )

        embed.set_author(name=self.title, url=PUMBILITY_LEADERBOARD_URL)
        embed.set_footer(text=f'Date • {self.date}')

        return embed

    async def embed_description(self, prev_pumbility: 'Pumbility', compare: bool) -> str:
        rank_emoji = f'{RANKING_EMOJIS[self.rank]} ' if self.rank in RANKING_EMOJIS else '<:graymedal:1196960956517982359> '

        rank_suffix = get_rank_suffix(self.rank)
        tied_text = f' ({self.tie_count}-way tie)' if self.tie_count > 1 else ''
        formatted_pumbility = format(self.pumbility, ',')

        if prev_pumbility is None:
            new_rank_text = ' (new)' if compare else ''
            return f'Rank: {rank_emoji}*{self.rank}{rank_suffix}*{new_rank_text}{tied_text}\n' \
                   f'Pumbility: *{formatted_pumbility}*'
        else:
            prev_rank_suffix = get_rank_suffix(prev_pumbility.rank)
            prev_formatted_pumbility = format(prev_pumbility.pumbility, ',')

            return f'Rank: {rank_emoji}*{prev_pumbility.rank}{prev_rank_suffix}* -> *{self.rank}{rank_suffix}*{tied_text}\n' \
                   f'Pumbility: *{prev_formatted_pumbility}* -> *{formatted_pumbility}*'
