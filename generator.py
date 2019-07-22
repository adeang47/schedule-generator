from operator import itemgetter

from copy import copy
from datetime import date, timedelta

import numpy as np
import pandas as pd

REPOS = {
    'Site API - Algo',
    'Site API - Interface',
    'Site Portal',
    'Spy Glass',
    'Landing',
    'CMS',
    'Common Components',
    'SEO Pages',
    'Answer Predictor',
    'Buoy Deployment',
    'Med Tools',
    'BuoyBazaar',
    'buoy-shared-jenkins',
    'buoy-terraform',
    'buoy-flagr',
    'buoy-helm-charts',
}

MAX_VAL = 5
MIN_VAL = 1


def get_ideal_pair(dev):
    """ get the ideal pair value for each repo

    Args:
        dev(dict): developer dictionary containing the dev name,
            and dict of repos with the repo name and knowledge level

    Returns:
        (dict): dictionary of repos with the ideal pair value

    """
    ideal_pair = {}
    for repo, value in dev['repos'].items():
        pair_value = MAX_VAL - value + MIN_VAL
        ideal_pair[repo] = pair_value

    return ideal_pair


def get_ideal_dev_pairs(devs):
    """ get the ideal pair values for all devs

    Args:
        devs(list): list of developer dictionaries containing the dev name,
            and dict of repos with the repo name and knowledge level

    Returns
        (dict): dictionary of devs names with a dict of the ideal pair value for each repo

    """
    ideal_pairs = {}
    for dev in devs:
        ideal_pair = get_ideal_pair(dev)
        ideal_pairs[dev['name']] = ideal_pair

    return ideal_pairs


def get_dev_matches(devs, ideal_pairs):
    """ get a list of ideal matches for each developer

    Args:
        devs(list): list of developer dictionaries containing the dev name,
            and dict of repos with the repo name and knowledge level
        ideal_pairs(dict): dictionary of dev names with a dictionary of their ideal pairs for each repo

        Returns:
            (dict): dictionary of developer names with an ordered list of their pairings by diff

    """
    dev_matches = {}
    for dev in devs:
        match_pairs = ideal_pairs[dev['name']]
        top_matches = []
        for compare_dev in devs:
            if compare_dev['name'] != dev['name']:
                diff = diff_heuristic(match_pairs, compare_dev['repos'])
                compare_match = {'name': compare_dev['name'], 'diff': diff}
                top_matches.append(compare_match)
        top_matches = reorder_ranks(top_matches)
        dev_matches[dev['name']] = top_matches

    return dev_matches


def diff_heuristic(dev1, dev2):
    """ get the absolute summed difference between the ideal pair of repos and a particular dev

    Args:
        dev1(dict): dictionary containing the ideal pair values for each repo
        dev2(dict): dictionary containing the dev knowledge values for each repo

    Returns:
        (int): absolute summed value of pair differences

    """
    total_diff = 0
    for repo in dev1:
        repo1_val = dev1[repo]
        repo2_val = dev2[repo]
        total_diff += abs(repo1_val - repo2_val)

    return total_diff


def reorder_ranks(ranks, allowed_ranks=None):
    """ sort the items in the ranks list

    Args:
        ranks(list): list of dictionaries containing a dev name and their summed diff from the ideal pair
        allowed_ranks(int): the number of items to allow in the ranks list, None will allow all items

    Returns:
        (list): new sorted list of ranked matches

    """
    new_ranks = copy(ranks)

    new_ranks = sorted(new_ranks, key=itemgetter('diff'), reverse=False)
    if allowed_ranks is not None:
        new_ranks = new_ranks[:allowed_ranks]

    return new_ranks


def add_and_reorder_ranks(ranks, compare_rank, allowed_ranks=3):
    """ add a new match to the rank list if its summed diff is in the top number of allowed ranks

    Args:
        ranks(list): list of dictionaries containing a dev name and their summed diff from the ideal pair
        compare_rank(dict): a potential dev match containing the dev name and their summed diff from the ideal pair
        allowed_ranks(int): the number of items to allow in the ranks list

    Returns:
        (list): new sorted list of ranked matches

    """
    new_ranks = copy(ranks)
    new_ranks.append(compare_rank)
    new_ranks = sorted(new_ranks, key=itemgetter('diff'), reverse=False)
    new_ranks = new_ranks[:allowed_ranks]

    return new_ranks


def total_dev_pairing_difficulty(dev_matches):
    """ get the total difference of pairings against all other devs for each dev

    Args:
        dev_matches(dict): dictionary of developer names with an ordered list of pairings by diff

    Returns(list):
        list sorted by devs that are most to least difficult to pair

    """
    dev_difficulty = []
    for dev, matches in dev_matches.items():
        difficulty = 0
        for match in matches:
            difficulty += match['diff']
        dev_difficulty.append({'name': dev, 'difficulty': difficulty})
    dev_difficulty = sorted(dev_difficulty, key=itemgetter('difficulty'), reverse=True)

    return dev_difficulty


def pair_devs(dev_matches, dev_difficulty, previous_pairs={}):
    """ pair two devs starting with the most difficult to pair to the least difficult

    Args:
        dev_matches(dict): dictionary of developer names with an ordered list of pairings by diff
        dev_difficulty(list): list sorted by devs that are most to least difficult to pair
        previous_pairs(dict): dictionary with the key being the dev name and the value being their pair

    Returns:
        (list): list of tuples for the dev pairs

    """
    dev_pairs = []
    used_devs = []
    for dev in dev_difficulty:
        if dev['name'] not in used_devs:
            for potential_dev in dev_matches[dev['name']]:
                if potential_dev['name'] not in used_devs:
                    if dev['name'] in previous_pairs and potential_dev['name'] in previous_pairs[dev['name']]:
                        continue
                    dev_pairs.append((dev['name'], potential_dev['name']))
                    used_devs.extend([dev['name'], potential_dev['name']])
                    break

    return dev_pairs


def build_pairs(devs, previous_pairs):
    """ build a schedule from a list of devs and their repo knowledge

    Args:
        devs(list): list of developer dictionaries containing the dev name,
            and dict of repos with the repo name and knowledge level
        previous_pairs(dict): dictionary with the key being the dev name and the value being their pair

    Returns:
        (list): list of tuples for the dev pairs

    """
    ideal_dev_pairs = get_ideal_dev_pairs(devs)
    dev_matches = get_dev_matches(devs, ideal_dev_pairs)
    dev_difficulty = total_dev_pairing_difficulty(dev_matches)
    dev_pairs = pair_devs(dev_matches, dev_difficulty, previous_pairs)

    return dev_pairs


def skip_weekend(dt):
    """ if the input date is a weekend skip to Monday

    Args:
        dt(date): date to potentially skip

    Returns:
        (date): the same date if it was not a weekend or Monday if it was a weekend

    """
    while dt.weekday() >= 5:
        dt = dt + timedelta(days=1)

    return dt


def check_can_schedule(pair, schedule_restrictions, schedule_date):
    """ check if the input pair can be scheduled for the given date

    Args:
        pair(tuple): dev pair names
        schedule_restrictions(dict): dev key with a list of the dates they cannot be scheduled
        schedule_date(date): the date the pair would be scheduled

    Return:
        (bool): whether or not the pair can be scheduled on that date

    """
    for member in pair:
        if member in schedule_restrictions and schedule_date in schedule_restrictions[member]:
            return False

    return True


def get_schedule_pair_idx(pairs, schedule_restrictions, schedule_date):
    """ return the index of the pair able to be scheduled for the given date
        a max of 10 attempts is tried for uniform random pairs
        if no pair is able to be scheduled the last pair that was tried will be scheduled

    Args:
        pairs(list): list of dev pair tuples
        schedule_restrictions(dict): dev key with a list of the dates they cannot be scheduled
        schedule_date(date): the date the pair would be scheduled

    Returns:
        (int): index of the pair that should be scheduled for the given date

    """
    can_schedule = False
    attempts = 0
    rand_pair_idx = 0
    while attempts < 10 and not can_schedule:
        rand_pair_idx = int(np.ceil(np.random.rand() * (len(pairs) - 1)))
        pair = pairs[rand_pair_idx]
        can_schedule = check_can_schedule(pair, schedule_restrictions, schedule_date)

    return rand_pair_idx


def build_schedule_order(dev_pairs, schedule_restrictions, start_date=date.today(), days=None):
    """ build the order of the schedule from the input dev pairs
        restrictions will prevent a dev pairing from being scheduled on their restricted dates
        the schedule will start at the input start date
        if the input start date is a weekend the start date will be moved to Monday of the following week

    Args:
        dev_pairs(list): list of dev pair tuples
        schedule_restrictions(dict): dictionary of each devs with a set of dates they cannot be scheduled
        start_date(date): the desired start date for the schedule

    Returns:
        (list): a list of dictionaries that contain the date and pair

    """
    # 0 Monday - 6 Sunday
    pairs = copy(dev_pairs)
    days = len(dev_pairs) if days is None else days
    schedule = []
    # if the entered date is a weekend skip to Monday
    start_date = skip_weekend(start_date)
    current_date = start_date
    for day in range(days):
        current_date = skip_weekend(current_date)
        # rand for uniform distribution
        pair_idx = get_schedule_pair_idx(pairs, schedule_restrictions, current_date)
        pair = pairs[pair_idx]
        del pairs[pair_idx]
        schedule.append({'pair': pair, 'date': current_date})
        current_date = current_date + timedelta(days=1)

    return schedule


def load_devs(dev_ooo):
    """ load developers and their repository knowledge from the repo_knowledge csv file

    Args:
        dev_ooo(set): do not include devs that will be out of office for the schedule time

    Returns:
        (list): list dicts for each developer with their name,
            and all repositories with their corresponding level of knowledge/familiarity

    """
    devs = []
    df = pd.DataFrame.from_csv('repo_knowledge.csv')
    for row in df.iterrows():
        if row[1]['Username'] not in dev_ooo:
            dev = {'name': row[1]['Username'], 'repos': {}}
            for repo in REPOS:
                dev['repos'][repo] = row[1][
                    'Rate your knowledge/familiarity of the following repositories. [{}]'.format(repo)]
            devs.append(dev)

    return devs


def build_previous_pairs_from_schedule(schedule):
    previous_pairs = {}
    for schedule_date in schedule:
        pair = schedule_date['pair']
        previous_pairs[pair[0]] = [pair[1]]
        previous_pairs[pair[1]] = [pair[0]]

    return previous_pairs


def print_schedule(schedule):
    for schedule_date in schedule:
        pair = schedule_date['pair']
        print(f'{schedule_date["date"]} - {pair[0]} & {pair[1]}')


def build_schedule(start_date=date.today(), days=5, previous_pairs=None):
    dev_ooo = set()
    if not previous_pairs:
        previous_pairs = {
            'adeangelis@buoyhealth.com': [],
            'andrew.dumit@buoyhealth.com': [],
            'jacob@buoyhealth.com': [],
            'eddie@buoyhealth.com': [],
            'mijail@buoyhealth.com': [],
            'jimmy@buoyhealth.com': [],
            'julia@buoyhealth.com': [],
            'brett@buoyhealth.com': [],
            'harry@buoyhealth.com': [],
            'kunhua@buoyhealth.com': [],
            'nick@buoyhealth.com': [],
        }
    devs = load_devs(dev_ooo)
    pairs = build_pairs(devs, previous_pairs)
    schedule = build_schedule_order(pairs, {}, start_date)

    return schedule


def build_multi_week_schedule(week_start=date.today(), weeks=2, previous_pairs=None):
    for i in range(weeks):
        schedule = build_schedule(start_date=week_start, days=5, previous_pairs=previous_pairs)
        print_schedule(schedule)
        previous_pairs = build_previous_pairs_from_schedule(schedule)
        week_start = week_start + timedelta(days=7)
