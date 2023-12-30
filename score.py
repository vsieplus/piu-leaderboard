# score.py

import discord

class Score(dict):
    GRADE_EMOJIS = {
        'SSS+': '<:sss_p:1190380059832365210>',
        'SSS' : '<:sss:1190380075401629736>',
        'SS+' : '<:ss_p:1190380092950585475>',
        'SS'  : '<:ss:1190380105680293921>',
        'S+'  : '<:s_p:1190380119630565477>',
        'S'   : '<:s_:1190380139704492102>',
        'AAA+': '<:aaa_p:1190380156347490405>',
        'AAA' : '<:aaa:1190380168343203920>',
        'AA+' : '<:aa_p:1190380180003373135>',
        'AA'  : '<:aa:1190380192741474335>',
        'A+'  : '<:a_p:1190380204363882638>',
        'A'   : '<:a_:1190561764178403408>',
        'B'   : '<:b_:1190561778682318858>',
        'C'   : '<:c_:1190561792561270814>',
        'D'   : '<:d_:1190561804494061608>',
        'F'   : '<:f_:1190561817643200522>',
    }

    RANKING_EMOJIS = {
        1 : '<:goldmedal:1190379061567037470>',
        2 : '<:silvermedal:1190380034138058772>',
        3 : '<:bronzemedal:1190380046846787666>'
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

    def __init__(self, chart, player, score, rank, date):
        dict.__init__(self, chart=chart, player=player, score=score, rank=rank, date=date)

    def embed(self) -> discord.Embed:
        embed_color = self.MODE_COLORS[self.mode] if self.mode in self.MODE_COLORS else discord.Color.black()
        rank_emoji = f'{self.RANKING_EMOJIS[self.rank]} ' if self.rank in self.RANKING_EMOJIS else ''
        grade_emoji = f'{self.GRADE_EMOJIS[self.grade]} ' if self.grade in self.GRADE_EMOJIS else ''
        embed =  discord.Embed(
            title=f'{self.player}',
            description=f'{rank_emoji}self.rank\n{grade_emoji}self.grade\n{self.score}',
            color=embed_color,
        )

        icon_url = self.MODE_ICON_URLS[self.mode] if self.mode in self.MODE_ICON_URLS else None
        embed.set_author(name=self.chart.level_id, url=self.chart.get_leaderboard_url(), icon_url=icon_url)
        embed.set_thumbnail(url=self.chart.thumbnail_url)
        embed.set_footer(text=f'Date • {self.date}')

    @classmethod
    def calculate_grade(score) -> str:
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
        elif score >= 800000:
            return 'A+'
        elif score >= 700000:
            return 'A'
        elif score >= 600000:
            return 'B'
        elif score >= 500000:
            return 'C'
        elif score >= 400000:
            return 'D'
        else:
            return 'F'
