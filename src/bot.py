# bot.py

import datetime
import logging
import os
import sys
from typing import List

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from bot_help import LeaderboardHelpCommand, CHANNEL_NAME
from guild_leaderboard import GuildLeaderboard
from leaderboard import Leaderboard
from leaderboard_dict import LeaderboardDict

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

INVALID_RANK_RANGE_MSG = 'Invalid rank parameter. Please ensure you are using the format `rank` or `rank-rank`'
INT_ERR_MSG  = '. One or more of the arguments could not be parsed as an integer'
LVL_NOT_FOUND_MSG = '`"{}"` was not found. Please ensure you are using the format `"Song title (S/D/Co-op)(Level)"`'
QUERY_ERR_MSG = 'An error occurred while querying the leaderboard. Please try again later'

leaderboards = LeaderboardDict(GuildLeaderboard)
leaderboard = Leaderboard()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} is connected to the following guilds:')

    for guild in bot.guilds:
        leaderboards[guild.id] = GuildLeaderboard(guild.id)
        logger.info(f'{guild.name}(id: {guild.id})')

    update_leaderboard.start()

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.errors.CommandError):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Command not found. Use `!help` to see a list of the available commands')
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

@bot.command(name='track', help='Begin tracking a player\'s scores')
async def track(ctx: commands.Context, player_id: str):
    if ctx.channel.name != CHANNEL_NAME:
        return

    if await leaderboards[ctx.guild.id].add_player(player_id):
        await ctx.send(f'Now tracking player {player_id}')
    else:
        await ctx.send(f'Player {player_id} is already being tracked')

@bot.command(name='untrack', help='Stop tracking a player\'s scores')
async def untrack(ctx: commands.Context, player_id: str):
    if ctx.channel.name != CHANNEL_NAME:
        return

    if await leaderboards[ctx.guild.id].remove_player(player_id):
        await ctx.send(f'No longer tracking player {player_id}')
    else:
        await ctx.send(f'Player {player_id} is not being tracked')

@bot.command(name='tracking', help='List all players being currently tracked')
async def tracking(ctx: commands.Context):
    if ctx.channel.name != CHANNEL_NAME:
        return

    if len(leaderboards[ctx.guild.id].players) == 0:
        await ctx.send('No players are currently being tracked')
    else:
        player_names = "\n".join(leaderboards[ctx.guild.id].players)
        player_names = discord.utils.escape_markdown(player_names)
        player_names = player_names.replace('\\#', '＃')
        await ctx.send(f'Currently tracking the following players: ```{player_names}```')

@bot.command(name='queryp', help='Query a player\'s rank on a level')
async def queryp(ctx: commands.Context, player_id: str, chart_id: str):
    if ctx.channel.name != CHANNEL_NAME:
        return

    async with ctx.typing():
        if (new_chart_id := await leaderboard.rescrape(bot, ctx, chart_id)):
            chart_id = new_chart_id
            scores = await leaderboard.query_score(player_id, chart_id)

            if scores is None:
                await ctx.send(QUERY_ERR_MSG)
            elif len(scores) == 0:
                await ctx.send(f'{player_id} is not on the leaderboard for {chart_id}')
            else:
                for score in scores:
                    await ctx.send(embed=score.embed(prev_score=None, compare=False))
        else:
            await ctx.send(LVL_NOT_FOUND_MSG.format(chart_id))


@bot.command(name='queryr', help='Query a specific rank on a level')
async def queryr(ctx: commands.Context, rank: str, chart_id: str):
    if ctx.channel.name != CHANNEL_NAME:
        return

    async with ctx.typing():
        if (new_chart_id := await leaderboard.rescrape(bot, ctx, chart_id)):
            chart_id = new_chart_id
            rank_range = await get_rank_range(ctx, rank)
            if rank_range and len(rank_range) >= 2:
                scores = []
                for i in range(rank_range[0], rank_range[1] + 1):
                    curr_scores = await leaderboard.query_rank(i, chart_id)
                    if curr_scores is None:
                        await ctx.send(QUERY_ERR_MSG)
                        return
                    else:
                        scores.extend(curr_scores)

                if len(scores) == 0:
                    await ctx.send(f'No scores with rank(s) {rank} on {chart_id}.')
                else:
                    for score in scores:
                        await ctx.send(embed=score.embed())
        else:
            await ctx.send(LVL_NOT_FOUND_MSG.format(chart_id))

async def get_rank_range(ctx: commands.Context, rank: str) -> List[int]:
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

@tasks.loop(minutes=90)
async def update_leaderboard():
    logger.info('Updating leaderboards')
    await leaderboard.update_all()
    logger.info('Leaderboards updated')

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await leaderboards[guild.id].get_leaderboard_updates(leaderboard, channel)

    logger.info('Leaderboard updates sent')

bot.help_command = LeaderboardHelpCommand()
bot.run(TOKEN)
