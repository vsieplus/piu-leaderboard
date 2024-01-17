# bot.py

import os
from typing import List

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from bot_help import LeaderboardHelpCommand
from guild_leaderboard import GuildLeaderboard
from leaderboard import Leaderboard

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

CHANNEL_NAME = 'piu-leaderboard'
INVALID_RANK_RANGE_MSG = 'Invalid rank parameter. Please ensure you are using the format `rank` or `rank-rank`'
INT_ERR_MSG  = '. One or more of the arguments could not be parsed as an integer'

leaderboards = dict()
leaderboard = Leaderboard()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        leaderboards[guild.name] = GuildLeaderboard(guild.name)

        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

    #update_leaderboard.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Command not found. Use `!help` to see a list of the available commands')
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


@bot.command(name='track', help='Begin tracking a player\'s scores')
async def track(ctx, player_id: str):
    if await leaderboards[ctx.guild.name].add_player(player_id):
        await ctx.send(f'Now tracking player {player_id}')
    else:
        await ctx.send(f'Player {player_id} is already being tracked')

@bot.command(name='untrack', help='Stop tracking a player\'s scores')
async def untrack(ctx, player_id: str):
    if await leaderboards[ctx.guild.name].remove_player(player_id):
        await ctx.send(f'No longer tracking player {player_id}')
    else:
        await ctx.send(f'Player {player_id} is not being tracked')

@bot.command(name='tracking', help='List all players being currently tracked')
async def tracking(ctx):
    player_names = "\n".join(leaderboards[ctx.guild.name].players)
    player_names = discord.utils.escape_markdown(player_names)
    player_names = player_names.replace('\\#', '＃')
    await ctx.send(f'Currently tracking the following players: ```{player_names}```')

@bot.command(name='queryp', help='Query a player\'s rank on a level')
async def queryp(ctx, player_id: str, chart_id: str):
    async with ctx.typing():
        if await leaderboard.rescrape(chart_id):
            scores = await leaderboard.query_score(player_id, chart_id)

            if scores is None:
                await ctx.send(f'`"{chart_id}"` was not found. Please ensure you are using the format `"Song title (S/D/Co-op)(Level)"`')
            elif len(scores) == 0:
                await ctx.send(f'{player_id} is not on the leaderboard for {chart_id}')
            else:
                for score in scores:
                    await ctx.send(embed=score.embed())

@bot.command(name='queryr', help='Query a specific rank on a level')
async def queryr(ctx, rank: str, chart_id: str):
    async with ctx.typing():
        if await leaderboard.rescrape(chart_id):
            rank_range = await get_rank_range(ctx, rank)
            if rank_range and len(rank_range) >= 2:
                scores = []
                for i in range(rank_range[0], rank_range[1] + 1):
                    curr_scores = await leaderboard.query_rank(i, chart_id)
                    if curr_scores is None:
                        await ctx.send(f'`"{chart_id}"` was not found. Please ensure you are using the format `"Song title (S/D/Co-op)(Level)"`')
                        return
                    else:
                        scores.extend(curr_scores)

                if len(scores) == 0:
                    await ctx.send(f'No scores with rank(s) {rank} on {chart_id}.')
                else:
                    for score in scores:
                        await ctx.send(embed=score.embed())

async def get_rank_range(ctx, rank: str) -> List[int]:
    rank = rank.replace(' ', '')
    if '-' in rank:
        rank_range = rank.split('-')
        if len(rank_range) != 2:
            await ctx.send(INVALID_RANK_RANGE_MSG)
            return []

        try:
            rank_range = [int(rank_range[0]), int(rank_range[1])]
        except ValueError:
            await ctx.send(f'{INVALID_RANK_RANGE_MSG}{INT_ERR_MSG}')
            return []

        if rank_range[0] > rank_range[1]:
            await ctx.send(f'{INVALID_RANK_RANGE_MSG}. Invalid range provided')
            return []
    else:
        try:
            rank_range = [int(rank), int(rank)]
        except ValueError:
            await ctx.send(f'{INVALID_RANK_RANGE_MSG}{INT_ERR_MSG}')
            return []

    return rank_range

@tasks.loop(minutes=60)
async def update_leaderboard():
    await leaderboard.update()

    for guild in bot.guilds:
        # only send updates in the 'piu-leaderboard' channel
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await leaderboards[guild.name].get_leaderboard_updates(leaderboard, channel)

bot.help_command = LeaderboardHelpCommand()
bot.run(TOKEN)
