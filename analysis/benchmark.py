from math import comb

from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW


def expected_random_hits(selection_size):
    if isinstance(selection_size, bool) or not isinstance(selection_size, int):
        raise ValueError("selection_size tam sayı olmalıdır.")
    if not 0 <= selection_size <= NUMBER_COUNT:
        raise ValueError("selection_size 0-80 aralığında olmalıdır.")
    return selection_size * NUMBERS_PER_DRAW / NUMBER_COUNT


def random_hit_probability(selection_size, hit_count):
    """Rastgele seçim için exact hipergeometrik Hit@N olasılığı."""

    expected_random_hits(selection_size)
    if isinstance(hit_count, bool) or not isinstance(hit_count, int):
        raise ValueError("hit_count tam sayı olmalıdır.")
    lower = max(0, selection_size - (NUMBER_COUNT - NUMBERS_PER_DRAW))
    upper = min(selection_size, NUMBERS_PER_DRAW)
    if not lower <= hit_count <= upper:
        return 0.0
    return (
        comb(NUMBERS_PER_DRAW, hit_count)
        * comb(NUMBER_COUNT - NUMBERS_PER_DRAW, selection_size - hit_count)
        / comb(NUMBER_COUNT, selection_size)
    )


def random_hit_distribution(selection_size):
    return {
        hit: random_hit_probability(selection_size, hit)
        for hit in range(0, min(selection_size, NUMBERS_PER_DRAW) + 1)
    }
