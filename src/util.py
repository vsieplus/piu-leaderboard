# util.py

from typing import List

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

def get_rank_suffix(rank: int) -> str:
    if rank >= 11 and rank <= 13:
        return 'th'

    return RANKING_SUFFIXES[rank % 10]

def update_curr_tie_count(tie_count: int, rank: int, previous_rank: int, player_id: str, previous_player_id: str, curr_tied_players: List[str]) -> int:
    """Update the current tie count.
    @param tie_count: the current tie count
    @param rank: the current player's rank
    @param previous_rank: the previous player's rank
    @param player_id: the current player's ID
    @param previous_player_id: the previous player's ID
    @param curr_tied_players: the list of currently tied players
    @return: the updated tie count
    """
    if rank == previous_rank:
        if tie_count == 1:
            # make sure to count first tie
            curr_tied_players.append(previous_player_id)

        curr_tied_players.append(player_id)
        tie_count += 1

    return tie_count

def update_next_tie_count(tie_count: int, rank: int, previous_rank: int, i: int, player_id: str, result_dict: dict, ranking_list: List, curr_tied_players: List[str]) -> int:
    """Update the next tie count.
    @param tie_count: the current tie count
    @param rank: the current player's rank
    @param previous_rank: the previous player's rank
    @param i: the current index in the ranking list
    @param player_id: the current player's ID
    @param result_dict: the dict of { player_id : Result }
    @param ranking_list: the list of rankings
    @param curr_tied_players: the list of currently tied players
    @return: the updated tie count
    """
    is_last = i == len(ranking_list) - 1
    is_new_rank = rank != previous_rank and tie_count > 1

    if is_last or is_new_rank:
        # set the tie count for all tied players
        for tied_player_id in curr_tied_players:
            result_dict[tied_player_id].tie_count = tie_count

        # reset tie count for next rank
        if is_new_rank:
            result_dict[player_id].tie_count = 1

        # reset tie count
        tie_count = 1
        curr_tied_players.clear()

    return tie_count
