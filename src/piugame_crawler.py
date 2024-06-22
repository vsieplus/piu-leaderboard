# piugame_crawler.py
# Utility functions for crawling piugame.com leaderboards.

import re

class PIUGAME_CRAWLER:
    @staticmethod
    def parse_rank(ranking_info) -> int:
        """Parse the player's rank.
        @param ranking_info: the ranking info div
        @return: the player's rank
        """
        player_num = ranking_info.xpath('.//div[@class="num"]')
        rank = player_num.xpath('.//i[@class="tt"]/text()').get()
        if rank is None:
            rank_image_path = player_num.xpath('.//div[@class="img_wrap"]//span[@class="medal_wrap"]//i[@class="img"]//img/@src').get()

            if rank_image_path is not None:
                if 'goldmedal' in rank_image_path:
                    rank = 1
                elif 'silvermedal' in rank_image_path:
                    rank = 2
                elif 'bronzemedal' in rank_image_path:
                    rank = 3
                else:
                    rank = 0
            else:
                rank = 0
        else:
            try:
                rank = int(rank)
            except ValueError:
                rank = 0

        return rank

    @staticmethod
    def parse_title(ranking_info) -> str:
        """Parse the player's title.
        @param ranking_info: the ranking info div
        @return: the player's title
        """
        return ranking_info.xpath('.//div[@class="profile_title en col6"]/text()').get()

    @staticmethod
    def parse_player_id(ranking_info, pumbility: bool) -> str:
        """Parse the player's ID.
        @param ranking_info: the ranking info div
        @return: the player's ID
        """
        pn_suffix = ' pl0' if pumbility else ''

        name = ranking_info.xpath(f'.//div[@class="profile_name en{pn_suffix}"]/text()').get()
        tag = ranking_info.xpath('.//div[@class="profile_name st1 en"]/text()').get()
        player_id = f'{name}{tag}'

        return player_id

    @staticmethod
    def parse_score(ranking_info) -> int:
        """Parse the player's score.
        @param ranking_info: the ranking info div
        @return: the player's score, or 0 if the player has no score
        """
        score = ranking_info.xpath('.//div[@class="score"]//i[@class="tt en"]/text()').get()

        if score is None:
            return 0
        else:
            # remove commas from score
            return int(score.replace(',', ''))

    @staticmethod
    def parse_avatar_id(ranking) -> str:
        """ Parse the player's avatar ID.
        @param ranking: the ranking div
        @return: the player's avatar ID
        """
        profile_img = ranking.xpath('.//div[@class="profile_img"]//div[@class="resize"]//div[@class="re bgfix"]/@style').get()
        avatar_id =  re.search(r'(?<=background-image:url\(\'https://(phoenix\.)?piugame\.com/data/avatar_img/)[0-9a-z]+(?=\.png)', profile_img).group()

        return avatar_id

    def parse_date(ranking) -> str:
        """Parse the date the score was set.
        @param ranking: the ranking div
        @return: the date the score was set
        """
        return ranking.xpath('.//div[@class="date"]//i[@class="tt"]/text()').get()
