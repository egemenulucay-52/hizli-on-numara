from dataclasses import dataclass
from hashlib import sha256
import json


MODEL_NAMES = ("M1", "M2", "M3", "M4", "M5", "M6")
DEFAULT_MODEL_WEIGHTS = (
    ("M1", 0.20),
    ("M2", 0.20),
    ("M3", 0.20),
    ("M4", 0.20),
    ("M5", 0.10),
    ("M6", 0.10),
)


@dataclass(frozen=True)
class AnalysisConfig:
    """Tahmin deneyinin sürümlenebilir ve değiştirilemez ayarları."""

    strategy_version: str = "1.0.0"
    config_version: str = "1.0.0"
    minimum_training_size: int = 500
    short_window: int = 15
    long_window: int = 150
    deviation_window: int = 150
    structural_window: int = 50
    z_clip: float = 4.0
    model_weights: tuple[tuple[str, float], ...] = DEFAULT_MODEL_WEIGHTS

    def __post_init__(self):
        integer_fields = (
            "minimum_training_size",
            "short_window",
            "long_window",
            "deviation_window",
            "structural_window",
        )
        for field_name in integer_fields:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{field_name} pozitif bir tam sayı olmalıdır.")

        if self.short_window > self.long_window:
            raise ValueError("short_window, long_window değerinden büyük olamaz.")
        if self.z_clip <= 0:
            raise ValueError("z_clip sıfırdan büyük olmalıdır.")

        names = tuple(name for name, _ in self.model_weights)
        if names != MODEL_NAMES:
            raise ValueError(f"Model ağırlıkları şu sırada olmalıdır: {MODEL_NAMES}")
        if any(weight < 0 for _, weight in self.model_weights):
            raise ValueError("Model ağırlıkları negatif olamaz.")
        if abs(sum(weight for _, weight in self.model_weights) - 1.0) > 1e-12:
            raise ValueError("Model ağırlıklarının toplamı 1 olmalıdır.")

    @property
    def weights(self):
        return dict(self.model_weights)

    def as_dict(self):
        return {
            "strategy_version": self.strategy_version,
            "config_version": self.config_version,
            "minimum_training_size": self.minimum_training_size,
            "short_window": self.short_window,
            "long_window": self.long_window,
            "deviation_window": self.deviation_window,
            "structural_window": self.structural_window,
            "z_clip": self.z_clip,
            "model_weights": self.weights,
        }

    @property
    def config_hash(self):
        canonical = json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return sha256(canonical.encode("utf-8")).hexdigest()
