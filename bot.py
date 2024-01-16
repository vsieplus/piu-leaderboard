# bot.py

import os
import random

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from leaderboard import GuildLeaderboard, Leaderboard

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        # Create a list to hold the pages
        pages = []

        # Add a page for each cog and its commands
        for category, commands in mapping.items():
            if category is None:
                category = 'No Category'
            pages.append(f'{category}:')

            max_cmd_width = max(len(command.qualified_name) for command in commands)
            max_sig_width = max(len(self.get_command_signature(command)) for command in commands)

            # sort commands alphabetically
            commands = sorted(commands, key=lambda command: command.qualified_name)

            for command in commands:
                cmd_spaces_to_add = max_cmd_width - len(command.qualified_name) + 2
                cmd_spaces = ' ' * cmd_spaces_to_add

                sig_spaces_to_add = max_sig_width - len(self.get_command_signature(command)) + 2
                sig_spaces = ' ' * sig_spaces_to_add

                pages.append(f'\t{command.qualified_name}{cmd_spaces}{self.get_command_signature(command)}{sig_spaces}{command.help}')

        pages.append('\nParameters (case-insensitive): ')
        pages.append('\tplayer_id  name[#tag]                       | if #tag is not specified, all scores with a matching name will be returned\n'
                     '\tlevel_id   "Song title (S/D/Co-op)(Level)"  | must be enclosed in quotes; for Co-op chart levels, use x2, x3, etc...')

        await self.get_destination().send('```' + '\n'.join(pages) + '```')


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_NAME = 'piu-leaderboard'

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

@bot.command(name='queryp', help='Query a player\'s rank on a level')
async def queryp(ctx, player_id: str, level_id: str):
    async with ctx.typing():
        scores = await leaderboard.query_score(player_id, level_id)

        if scores is None:
            await ctx.send(f'`"{level_id}"` was not found. Please ensure you are using the format `"Song title (S/D/Co-op)(Level)"`')
        elif len(scores) == 0:
            await ctx.send(f'{player_id} is not on the leaderboard for {level_id}.')
        else:
            for score in scores:
                await ctx.send(embed=score.embed())

@bot.command(name='queryr', help='Query a specific rank on a level')
async def queryr(ctx, rank: int, level_id: str):
    async with ctx.typing():
        scores = await leaderboard.query_rank(rank, level_id)

        if scores is None:
            await ctx.send(f'`"{level_id}"` was not found. Please ensure you are using the format `"Song title (S/D/Co-op)(Level)"`')
        elif len(scores) == 0:
            await ctx.send(f'No scores with rank {rank} on {level_id}.')
        else:
            for score in scores:
                await ctx.send(embed=score.embed())

@tasks.loop(minutes=60)
async def update_leaderboard():
    await leaderboard.update()

    for guild in bot.guilds:
        # only send updates in the 'piu-leaderboard' channel
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await leaderboards[guild.name].get_leaderboard_updates(channel)

bot.help_command = CustomHelpCommand()
bot.run(TOKEN)
