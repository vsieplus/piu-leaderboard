# util.py

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

def get_rank_suffix(rank) -> str:
    if rank >= 11 and rank <= 13:
        return 'th'

    return RANKING_SUFFIXES[rank % 10]
