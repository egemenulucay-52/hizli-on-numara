from math import log

import numpy as np

from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW


class OnlineLogisticRanker:
    """Target görüldükten sonra tek adım güncellenen açıklanabilir M10 modeli."""

    def __init__(self, feature_names, learning_rate=0.12, l2=0.01, state=None):
        self.feature_names = tuple(feature_names)
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        self.weights = np.zeros(len(self.feature_names), dtype=float)
        self.bias = log((NUMBERS_PER_DRAW / NUMBER_COUNT) / (1 - NUMBERS_PER_DRAW / NUMBER_COUNT))
        self.step = 0
        if state is not None:
            self.load_state(state)

    @staticmethod
    def _sigmoid(values):
        values = np.clip(values, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(-values))

    def predict_proba(self, features):
        features = np.asarray(features, dtype=float)
        return self._sigmoid(features @ self.weights + self.bias)

    def update(self, features, actual_numbers):
        features = np.asarray(features, dtype=float)
        target = np.zeros(NUMBER_COUNT, dtype=float)
        target[np.asarray(actual_numbers, dtype=int) - 1] = 1.0
        predictions = self.predict_proba(features)
        error = predictions - target
        rate = self.learning_rate / np.sqrt(self.step + 1.0)
        gradient = features.T @ error / NUMBER_COUNT + self.l2 * self.weights
        self.weights -= rate * gradient
        self.bias -= rate * float(error.mean())
        self.step += 1

    def state_dict(self):
        return {
            "feature_names": list(self.feature_names),
            "learning_rate": self.learning_rate,
            "l2": self.l2,
            "weights": self.weights.tolist(),
            "bias": self.bias,
            "step": self.step,
        }

    def load_state(self, state):
        if tuple(state["feature_names"]) != self.feature_names:
            raise ValueError("M10 feature şeması model state ile uyuşmuyor.")
        self.weights = np.asarray(state["weights"], dtype=float)
        self.bias = float(state["bias"])
        self.step = int(state["step"])
