import numpy as np
import pandas as pd

from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW, category_count_moments


def _window_size(df, requested):
    if isinstance(requested, bool) or not isinstance(requested, int) or requested < 1:
        raise ValueError("Pencere uzunluğu pozitif bir tam sayı olmalıdır.")
    if df.empty:
        raise ValueError("Analiz için en az bir çekiliş gerekir.")
    return min(requested, len(df))


def number_frequency_summary(df, number_columns, short_window=15, long_window=150):
    """Kısa ve uzun dönem sayı frekanslarını tahmin yorumu eklemeden özetler."""
    short_size = _window_size(df, short_window)
    long_size = _window_size(df, long_window)

    short_values = df.head(short_size)[number_columns].to_numpy(dtype=int).ravel()
    long_values = df.head(long_size)[number_columns].to_numpy(dtype=int).ravel()
    short_counts = np.bincount(short_values, minlength=NUMBER_COUNT + 1)[1:]
    long_counts = np.bincount(long_values, minlength=NUMBER_COUNT + 1)[1:]

    short_expected = short_size * NUMBERS_PER_DRAW / NUMBER_COUNT
    long_expected = long_size * NUMBERS_PER_DRAW / NUMBER_COUNT
    short_rates = short_counts / short_size
    long_rates = long_counts / long_size

    return pd.DataFrame(
        {
            "Number": np.arange(1, NUMBER_COUNT + 1),
            "Short Observed": short_counts,
            "Short Expected": short_expected,
            "Short Rate": short_rates,
            "Long Observed": long_counts,
            "Long Expected": long_expected,
            "Long Rate": long_rates,
            "Frequency Momentum": short_rates - long_rates,
        }
    )


def _category_summary(df, number_columns, groups, window):
    window_size = _window_size(df, window)
    values = df.head(window_size)[number_columns].to_numpy(dtype=int)
    rows = []
    for label, numbers in groups:
        number_set = np.asarray(tuple(numbers), dtype=int)
        observed = int(np.isin(values, number_set).sum())
        moments = category_count_moments(window_size, len(number_set))
        rows.append(
            {
                "Group": label,
                "Observed": observed,
                "Expected": moments.expected,
                "Deviation": observed - moments.expected,
                "Observed per Draw": observed / window_size,
                "Expected per Draw": moments.expected / window_size,
            }
        )
    return pd.DataFrame(rows)


def block_summary(df, number_columns, window=20):
    groups = [
        (f"{start}-{start + 9}", range(start, start + 10))
        for start in range(1, NUMBER_COUNT + 1, 10)
    ]
    return _category_summary(df, number_columns, groups, window)


def ending_digit_summary(df, number_columns, window=20):
    groups = [
        (f"Sonu {digit}", (number for number in range(1, NUMBER_COUNT + 1) if number % 10 == digit))
        for digit in range(10)
    ]
    return _category_summary(df, number_columns, groups, window)
