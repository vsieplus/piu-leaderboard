# guild_leaderboard.py

import os
import discord
from leaderboard import Leaderboard, SAVE_DIR

class GuildLeaderboard:
    PLAYERS_SAVE_FILE = 'players.txt'

    def __init__(self, guild_id: str):
        """ Initialize the guild's leaderboard.
        @param guild_id: the guild's name
        """
        self.players = set()
        self.players_file = os.path.join(SAVE_DIR, f'{guild_id}_{self.PLAYERS_SAVE_FILE}')
        if os.path.isfile(self.players_file):
            with open(self.players_file, 'r') as f:
                for line in f:
                    self.players.add(line.strip().upper())

    async def add_player(self, player_id: str) -> bool:
        """ Add a player to the guild's leaderboard. If the player is already being tracked, do nothing.
        Players that are being tracked will have their leaderboard updates automatically sent to the guild's 'piu-leaderboard' channel.
        @param player_id: the player's ID, in the format of name#tag
        @return: True if the player was added, False otherwise
        """
        player_id = player_id.upper()
        added = player_id not in self.players
        if added:
            self.players.add(player_id)

        await self.save()
        return added

    async def remove_player(self, player_id: str) -> bool:
        """ Remove a player from the guild's leaderboard. If the player is not being tracked, do nothing.
        If #tag is not provided, all players with the same name will be removed.
        @param player_id: the player's ID, in the format of name[#tag]
        @return: True if the player was removed, False otherwise
        """
        player_id = player_id.upper()

        removed = False

        for player in self.players.copy():
            if player.startswith(player_id):
                self.players.remove(player)
                removed = True

        await self.save()
        return removed

    async def get_leaderboard_updates(self, leaderboard: Leaderboard, channel: discord.TextChannel):
        """ Get the leaderboard updates for all the players being tracked in the guild.
        @param channel: the channel to send the updates to
        @return: None
        """
        for (new_score, prev_score) in await leaderboard.get_score_updates(self.players):
            embed, f = await new_score.embed(prev_score=prev_score, compare=True)
            await channel.send(embed=embed, file=f)

    async def get_pumbility_updates(self, leaderboard: Leaderboard, channel: discord.TextChannel):
        """ Get the pumbility updates for all the players being tracked in the guild.
        @param channel: the channel to send the updates to
        @return: None
        """
        for (new_pumbility, prev_pumbility) in await leaderboard.get_pumbility_updates(self.players):
            await channel.send(embed=await new_pumbility.embed(prev_pumbility=prev_pumbility, compare=True))

    async def save(self):
        with open(self.players_file, 'w', encoding='utf-8') as f:
            for player in self.players:
                f.write(f'{player}\n')
