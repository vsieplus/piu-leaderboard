# bot.py

import os
import random

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from leaderboard import GuildLeaderboard, Leaderboard

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot_channel_id = None

leaderboards = dict()
leaderboard = Leaderboard()

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
        await ctx.send('Command not found.')
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

@bot.command(name='track', help='Begin tracking a player\'s scores')
async def track(ctx, player_id: str):
    if await leaderboards[ctx.guild.name].add_player(player_id):
        await ctx.send(f'Now tracking player {player_id}.')
    else:
        await ctx.send(f'Player {player_id} is already being tracked.')

@bot.command(name='untrack', help='Stop tracking a player\'s scores')
async def untrack(ctx, player_id: str):
    if await leaderboards[ctx.guild.name].remove_player(player_id):
        await ctx.send(f'No longer tracking player {player_id}.')
    else:
        await ctx.send(f'Player {player_id} is not being tracked.')

@bot.command(name='query', help='Query a player\'s rank on a level')
async def query(ctx, player_id: str, level_id: str):
    scores = await leaderboard.query_score(player_id, level_id)
    if scores is None or len(scores) == 0:
        await ctx.send(f'{player_id} is not on the leaderboard for {level_id}.')
    else:
        for score in scores:
            await ctx.send(embed=score.embed())

@tasks.loop(minutes=60)
async def update_leaderboard():
    await leaderboard.update()

    for guild in bot.guilds:
        # only send updates in the 'piu-scores' channel
        for channel in guild.text_channels:
            if channel.name == 'piu-scores':
                await leaderboards[guild.name].get_leaderboard_updates(channel)

bot.run(TOKEN)
