# bot_help.py

from discord.ext import commands

class LeaderboardHelpCommand(commands.HelpCommand):
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
        pages.append('\tchart_id   "Song title (S/D/Co-op)(Level)"  | must be enclosed in quotes; for Co-op chart levels, use x2, x3, etc...\n'
                     '\tplayer_id  name[#tag]                       | if #tag is not specified, all scores with a matching name will be returned\n'
                     '\trank       rank[-rank]                      | ranks must be between 1 and 100; can optionally specify a range of ranks to query\n')

        await self.get_destination().send('```' + '\n'.join(pages) + '```')
