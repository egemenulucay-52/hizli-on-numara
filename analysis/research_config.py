from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class ResearchConfig:
    research_version: str = "2.0.0"
    minimum_training_size: int = 500
    decay_half_life: float = 100.0
    bayesian_prior_strength: float = 40.0
    significant_min_support: int = 30
    significant_z_threshold: float = 3.5
    multi_lag_weights: tuple[float, ...] = (1.0, 0.60, 0.35)
    candidate_pool_size: int = 15
    beam_width: int = 50
    triple_min_support: int = 3
    relation_clip: float = 4.0
    m10_learning_rate: float = 0.12
    m10_l2: float = 0.01
    m10_update_interval: int = 10
    research_target_count: int = 1000
    joint_weights: tuple[tuple[str, float], ...] = (
        ("individual", 0.25),
        ("pair", 0.15),
        ("triple", 0.15),
        ("conditional", 0.15),
        ("structural", 0.10),
        ("bayesian", 0.20),
    )

    def __post_init__(self):
        if self.minimum_training_size < 1 or self.research_target_count < 1:
            raise ValueError("Eğitim ve araştırma hedef sayıları pozitif olmalıdır.")
        if self.decay_half_life <= 0 or self.bayesian_prior_strength <= 0:
            raise ValueError("Decay ve Bayesian prior değerleri pozitif olmalıdır.")
        if not 6 <= self.candidate_pool_size <= 30:
            raise ValueError("Candidate pool 6-30 aralığında olmalıdır.")
        if self.beam_width < 1:
            raise ValueError("Beam width pozitif olmalıdır.")
        if self.m10_update_interval < 1:
            raise ValueError("M10 update interval pozitif olmalıdır.")
        if abs(sum(weight for _, weight in self.joint_weights) - 1.0) > 1e-12:
            raise ValueError("Joint objective ağırlıkları toplamı 1 olmalıdır.")

    @property
    def weights(self):
        return dict(self.joint_weights)

    def as_dict(self):
        return {
            "research_version": self.research_version,
            "minimum_training_size": self.minimum_training_size,
            "decay_half_life": self.decay_half_life,
            "bayesian_prior_strength": self.bayesian_prior_strength,
            "significant_min_support": self.significant_min_support,
            "significant_z_threshold": self.significant_z_threshold,
            "multi_lag_weights": list(self.multi_lag_weights),
            "candidate_pool_size": self.candidate_pool_size,
            "beam_width": self.beam_width,
            "triple_min_support": self.triple_min_support,
            "relation_clip": self.relation_clip,
            "m10_learning_rate": self.m10_learning_rate,
            "m10_l2": self.m10_l2,
            "m10_update_interval": self.m10_update_interval,
            "research_target_count": self.research_target_count,
            "joint_weights": self.weights,
        }

    @property
    def config_hash(self):
        canonical = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()
