from dataclasses import dataclass
from math import comb, sqrt


NUMBER_COUNT = 80
NUMBERS_PER_DRAW = 20
COMBINATION_SIZES = (2, 3, 4)


@dataclass(frozen=True)
class DistributionMoments:
    expected: float
    variance: float

    @property
    def standard_deviation(self):
        return sqrt(self.variance)


def _non_negative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} sıfır veya daha büyük bir tam sayı olmalıdır.")


def _bounded_integer(value, name, minimum, maximum):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} {minimum}-{maximum} arasında bir tam sayı olmalıdır.")


def combination_inclusion_probability(group_size):
    """Sabit bir k'lı grubun tek çekilişte birlikte bulunma olasılığı."""
    _bounded_integer(group_size, "group_size", 1, NUMBERS_PER_DRAW)
    return comb(NUMBER_COUNT - group_size, NUMBERS_PER_DRAW - group_size) / comb(
        NUMBER_COUNT, NUMBERS_PER_DRAW
    )


def combination_occurrence_moments(draw_count, group_size):
    """Bağımsız çekilişlerde sabit bir k'lı grubun tekrar sayısı momentleri."""
    _non_negative_integer(draw_count, "draw_count")
    probability = combination_inclusion_probability(group_size)
    return DistributionMoments(
        expected=draw_count * probability,
        variance=draw_count * probability * (1.0 - probability),
    )


def category_count_moments(draw_count, category_size):
    """Bir sayı kategorisinden seçilen toplam adet için hipergeometrik momentler.

    Kategori; onluk blok (10 sayı), son basamak grubu (8 sayı) veya 1-80
    tahtasındaki başka sabit bir alt küme olabilir.
    """
    _non_negative_integer(draw_count, "draw_count")
    _bounded_integer(category_size, "category_size", 1, NUMBER_COUNT)

    category_rate = category_size / NUMBER_COUNT
    expected_per_draw = NUMBERS_PER_DRAW * category_rate
    variance_per_draw = (
        NUMBERS_PER_DRAW
        * category_rate
        * (1.0 - category_rate)
        * ((NUMBER_COUNT - NUMBERS_PER_DRAW) / (NUMBER_COUNT - 1))
    )
    return DistributionMoments(
        expected=draw_count * expected_per_draw,
        variance=draw_count * variance_per_draw,
    )
