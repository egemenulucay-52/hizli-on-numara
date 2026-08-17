from collections import deque

import numpy as np

from analysis.config import AnalysisConfig
from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW


class IncrementalAnalysisState:
    """Walk-forward sırasında yalnız geçmişi tutan artımlı istatistik durumu."""

    def __init__(self, config=None):
        self.config = config or AnalysisConfig()
        self.draw_count = 0
        self.latest_draw = None
        self.latest_draw_id = None

        self.pair_counts = np.zeros((NUMBER_COUNT, NUMBER_COUNT), dtype=np.int64)
        self.transition_counts = np.zeros(
            (NUMBER_COUNT, NUMBER_COUNT), dtype=np.int64
        )
        self.transition_exposure = np.zeros(NUMBER_COUNT, dtype=np.int64)
        self.last_seen = np.full(NUMBER_COUNT, -1, dtype=np.int64)

        self._window_limits = {
            "short": self.config.short_window,
            "long": self.config.long_window,
            "deviation": self.config.deviation_window,
        }
        self._window_draws = {name: deque() for name in self._window_limits}
        self._window_counts = {
            name: np.zeros(NUMBER_COUNT, dtype=np.int64)
            for name in self._window_limits
        }

        self._structural_draws = deque()
        self.structural_block_counts = np.zeros(8, dtype=np.int64)
        self.structural_digit_counts = np.zeros(10, dtype=np.int64)

    @staticmethod
    def _validated_indices(numbers):
        values = np.asarray(numbers, dtype=int)
        if values.shape != (NUMBERS_PER_DRAW,):
            raise ValueError(f"Her çekilişte {NUMBERS_PER_DRAW} sayı bulunmalıdır.")
        if np.any((values < 1) | (values > NUMBER_COUNT)):
            raise ValueError("Çekiliş sayıları 1-80 aralığında olmalıdır.")
        if np.unique(values).size != NUMBERS_PER_DRAW:
            raise ValueError("Çekiliş sayıları benzersiz olmalıdır.")
        return np.sort(values) - 1

    def _update_number_window(self, name, indices):
        draws = self._window_draws[name]
        counts = self._window_counts[name]
        draws.append(indices.copy())
        counts[indices] += 1

        if len(draws) > self._window_limits[name]:
            outgoing = draws.popleft()
            counts[outgoing] -= 1

    def _update_structural_window(self, indices):
        self._structural_draws.append(indices.copy())
        self.structural_block_counts += np.bincount(
            indices // 10, minlength=8
        )
        self.structural_digit_counts += np.bincount(
            (indices + 1) % 10, minlength=10
        )

        if len(self._structural_draws) > self.config.structural_window:
            outgoing = self._structural_draws.popleft()
            self.structural_block_counts -= np.bincount(
                outgoing // 10, minlength=8
            )
            self.structural_digit_counts -= np.bincount(
                (outgoing + 1) % 10, minlength=10
            )

    def update(self, numbers, draw_id=None):
        """Yeni gerçekleşen çekilişi state'e ekler.

        Backtest motoru bu metodu hedef çekiliş değerlendirildikten sonra çağırır.
        """

        indices = self._validated_indices(numbers)

        is_consecutive = True
        if self.latest_draw_id is not None and draw_id is not None:
            try:
                is_consecutive = int(draw_id) == int(self.latest_draw_id) + 1
            except (TypeError, ValueError):
                is_consecutive = False

        if self.latest_draw is not None and is_consecutive:
            self.transition_exposure[self.latest_draw] += 1
            self.transition_counts[np.ix_(self.latest_draw, indices)] += 1

        self.pair_counts[np.ix_(indices, indices)] += 1
        self.pair_counts[indices, indices] -= 1

        for name in self._window_limits:
            self._update_number_window(name, indices)
        self._update_structural_window(indices)

        self.last_seen[indices] = self.draw_count
        self.draw_count += 1
        self.latest_draw = indices
        self.latest_draw_id = None if draw_id is None else str(draw_id)

    def window_counts(self, name):
        return self._window_counts[name]

    def window_size(self, name):
        return len(self._window_draws[name])

    @property
    def structural_window_size(self):
        return len(self._structural_draws)

    @property
    def gaps(self):
        if self.draw_count == 0:
            return np.zeros(NUMBER_COUNT, dtype=np.int64)
        return np.where(
            self.last_seen >= 0,
            self.draw_count - 1 - self.last_seen,
            self.draw_count,
        )
