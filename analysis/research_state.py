from collections import deque
from math import log

import numpy as np

from analysis.config import AnalysisConfig
from analysis.hypergraph import draw_triple_indices, TRIPLE_COMBINATIONS
from analysis.model import NUMBER_COUNT
from analysis.research_config import ResearchConfig
from analysis.state import IncrementalAnalysisState


class ResearchState:
    """Baseline state'i M4 lag/decay ve M9 triple sayaçlarıyla genişletir."""

    def __init__(self, config=None):
        self.config = config or ResearchConfig()
        baseline_config = AnalysisConfig(
            minimum_training_size=self.config.minimum_training_size,
            short_window=self.config.short_window,
            long_window=self.config.long_window,
            deviation_window=self.config.deviation_window,
            structural_window=self.config.structural_window,
        )
        self.baseline = IncrementalAnalysisState(baseline_config)
        lag_count = len(self.config.multi_lag_weights)
        self.lag_counts = np.zeros((lag_count, NUMBER_COUNT, NUMBER_COUNT), dtype=np.int64)
        self.lag_exposure = np.zeros((lag_count, NUMBER_COUNT), dtype=np.int64)
        self.decayed_counts = np.zeros((NUMBER_COUNT, NUMBER_COUNT), dtype=float)
        self.decayed_exposure = np.zeros(NUMBER_COUNT, dtype=float)
        self.decayed_exposure_sq = np.zeros(NUMBER_COUNT, dtype=float)
        self.triple_counts = np.zeros(len(TRIPLE_COMBINATIONS), dtype=np.int32)
        self.history = deque(maxlen=lag_count)

    @property
    def draw_count(self):
        return self.baseline.draw_count

    @property
    def latest_draw(self):
        return self.baseline.latest_draw

    @property
    def latest_draw_id(self):
        return self.baseline.latest_draw_id

    def update(self, numbers, draw_id=None):
        indices = self.baseline._validated_indices(numbers)
        current_id = int(draw_id) if draw_id is not None else None
        previous_id = int(self.latest_draw_id) if self.latest_draw_id is not None else None
        gap = 1 if current_id is None or previous_id is None else max(1, current_id - previous_id)
        decay = np.exp(-log(2.0) * gap / self.config.decay_half_life)
        self.decayed_counts *= decay
        self.decayed_exposure *= decay
        self.decayed_exposure_sq *= decay * decay

        if self.latest_draw is not None and (current_id is None or current_id == previous_id + 1):
            previous = self.latest_draw
            self.decayed_counts[np.ix_(previous, indices)] += 1.0
            self.decayed_exposure[previous] += 1.0
            self.decayed_exposure_sq[previous] += 1.0

        for lag_index in range(min(len(self.history), len(self.config.multi_lag_weights))):
            historical_id, historical_draw = self.history[-(lag_index + 1)]
            lag = lag_index + 1
            if current_id is None or historical_id is None or current_id == historical_id + lag:
                self.lag_counts[lag_index][np.ix_(historical_draw, indices)] += 1
                self.lag_exposure[lag_index][historical_draw] += 1

        self.triple_counts[draw_triple_indices(indices)] += 1
        self.baseline.update(indices + 1, draw_id)
        self.history.append((current_id, indices.copy()))
