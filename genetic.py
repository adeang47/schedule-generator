from copy import deepcopy
import math
import random

TEST_DATA = [
    {
        'name': 'dev1',
        'repos': {
            'repo1': 2,
            'repo2': 4,
            'repo3': 5
        }
    },
    {
        'name': 'dev2',
        'repos': {
            'repo1': 5,
            'repo2': 2,
            'repo3': 1
        }
    },
    {
        'name': 'dev3',
        'repos': {
            'repo1': 3,
            'repo2': 3,
            'repo3': 1
        }
    },
    {
        'name': 'dev4',
        'repos': {
            'repo1': 1,
            'repo2': 1,
            'repo3': 1
        }
    },
    {
        'name': 'dev5',
        'repos': {
            'repo1': 2,
            'repo2': 3,
            'repo3': 1
        }
    },
    {
        'name': 'dev6',
        'repos': {
            'repo1': 4,
            'repo2': 4,
            'repo3': 5
        }
    },
    {
        'name': 'dev7',
        'repos': {
            'repo1': 5,
            'repo2': 5,
            'repo3': 5
        }
    },
]

MAX_VAL = 5
MIN_VAL = 1


def get_pair_fitness(pair):
    """Returns a fitness score for the pairing

    Args:
        pair (tuple): a pairing of devs

    Returns
        (int): fitness score
    """
    dev_1, dev_2 = pair
    num_repos = len(dev_1['repos'])

    fitness = 0
    for repo in dev_1['repos'].keys():
        dev_1_score = dev_1['repos'][repo]
        dev_2_score = dev_2['repos'][repo]
        fitness += max(dev_1_score, dev_2_score)

    return fitness


def get_schedule_fitness(schedule):
    """Returns a fitness score for the entire schedule

    Args:
        schedule (list): list of pairs of devs

    Returns
        (int): fitness score
    """
    fitness = 0
    for pair in schedule:
        fitness += get_pair_fitness(pair)
    return fitness


def random_schedule(devs, total_shifts=5):
    """Generates a random schedule.

    A schedule is just a list of pairs

    Args:
        devs (list): devs with their knowledge of repos
        total_shifts (int): the total number of shifts in the schedule
    """
    
    # maximum number of shifts any dev should have
    max_shifts = math.ceil((total_shifts * 2) / len(devs))

    # track the number of shifts so you don't exceed max
    num_shifts = [0 for x in range(len(devs))]
    
    schedule = []

    while len(schedule) < total_shifts:
        dev_1 = random.randint(0, len(devs) - 1)
        dev_2 = random.randint(0, len(devs) - 1)

        if (dev_1 != dev_2 
                and not (devs[dev_1], devs[dev_2]) in schedule
                and num_shifts[dev_1] < max_shifts 
                and num_shifts[dev_2] < max_shifts):
            
            schedule.append((devs[dev_1], devs[dev_2]))
            num_shifts[dev_1] += 1
            num_shifts[dev_2] += 1

    return schedule


def generate_schedule(num_trials):
    best_schedule = None
    best_schedule_fitness = 0
    for x in range(num_trials):
        schedule = random_schedule(TEST_DATA)
        if get_schedule_fitness(schedule) > best_schedule_fitness:
            best_schedule = schedule
            best_schedule_fitness = get_schedule_fitness(schedule)
    return best_schedule


def pretty_print_schedule(schedule):
    print('SCHEDULE')
    print('')
    for pair in schedule:
        print(pair[0]['name'])
        print(pair[1]['name'])
        print('')
    
    print('Fitness: {}'.format(get_schedule_fitness(schedule)))


pretty_print_schedule(generate_schedule(100))
