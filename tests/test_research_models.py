import unittest

import numpy as np

from analysis.bayesian import m8_bayesian_conditional_score
from analysis.hypergraph import DRAW_TRIPLE_POSITIONS
from analysis.joint_sets import JointSetScorer, optimize_joint_sets
from analysis.m4_variants import calculate_m4_variants
from analysis.ml_training import OnlineLogisticRanker
from analysis.model_registry import RESEARCH_MODEL_NAMES
from analysis.nested_validation import (
    assert_no_temporal_leakage,
    expanding_temporal_folds,
)
from analysis.research_backtest import M10_FEATURE_NAMES, research_walk_forward_backtest
from analysis.research_config import ResearchConfig
from analysis.research_state import ResearchState
from tests.test_prediction_engine import generated_draw, generated_frame


class ResearchModelTests(unittest.TestCase):
    def config(self):
        return ResearchConfig(
            minimum_training_size=5,
            research_target_count=3,
            candidate_pool_size=8,
            beam_width=10,
            significant_min_support=2,
        )

    def state(self):
        state = ResearchState(self.config())
        for index in range(8):
            state.update(generated_draw(index), str(10000 + index))
        return state

    def test_research_state_tracks_lags_decay_and_triples(self):
        state = self.state()
        self.assertEqual(
            int(state.triple_counts.sum()), 8 * len(DRAW_TRIPLE_POSITIONS)
        )
        self.assertGreater(int(state.lag_exposure[0].sum()), 0)
        self.assertGreater(float(state.decayed_exposure.sum()), 0)

    def test_m4_variants_and_m8_are_finite(self):
        state = self.state()
        variants = calculate_m4_variants(state)
        self.assertEqual(set(variants), {"M4-A", "M4-B", "M4-C", "M4-D", "M4-E", "M4-F"})
        for values in variants.values():
            self.assertEqual(values.shape, (80,))
            self.assertTrue(np.isfinite(values).all())
        m8 = m8_bayesian_conditional_score(
            state.baseline.transition_counts,
            state.baseline.transition_exposure,
            state.latest_draw,
        )
        self.assertTrue(np.isfinite(m8).all())

    def test_joint_set_search_is_deterministic(self):
        scorer = JointSetScorer(
            individual=np.linspace(0, 1, 80),
            pair_matrix=np.full((80, 80), 0.5),
            triple_scores=np.full(82160, 0.5),
            conditional=np.linspace(0, 1, 80),
            structural=np.full(80, 0.5),
            bayesian=np.linspace(0, 1, 80),
            weights=self.config().weights,
        )
        first = optimize_joint_sets(range(1, 9), scorer, beam_width=10)
        second = optimize_joint_sets(range(1, 9), scorer, beam_width=10)
        self.assertEqual(first, second)
        self.assertEqual({size: len(values) for size, values in first.items()}, {4: 4, 5: 5, 6: 6})

    def test_online_logistic_updates_only_after_target(self):
        model = OnlineLogisticRanker(M10_FEATURE_NAMES)
        features = np.zeros((80, len(M10_FEATURE_NAMES)))
        features[:, 0] = np.linspace(0, 1, 80)
        before = model.predict_proba(features)
        model.update(features, generated_draw(0))
        after = model.predict_proba(features)
        self.assertFalse(np.allclose(before, after))
        self.assertEqual(model.step, 1)

    def test_temporal_folds_never_overlap(self):
        folds = expanding_temporal_folds(100, 40, 20, 10)
        self.assertGreater(len(folds), 0)
        for fold in folds:
            assert_no_temporal_leakage(fold)

    def test_small_research_walk_forward_contains_every_model(self):
        run = research_walk_forward_backtest(
            generated_frame(12), config=self.config(), last=3
        )
        self.assertEqual(len(run.results), 3)
        self.assertTrue(
            ((run.results["Target Draw"].astype(int) - run.results["Train End Draw"].astype(int)) == 1).all()
        )
        for model in RESEARCH_MODEL_NAMES:
            self.assertIn(f"{model} Hit@6", run.results.columns)
            self.assertIn(f"{model} Set@6", run.results.columns)

    def test_exact_target_ids_are_respected(self):
        frame = generated_frame(12)
        run = research_walk_forward_backtest(
            frame,
            config=self.config(),
            target_ids=("10007", "10009"),
        )
        self.assertEqual(run.results["Target Draw"].tolist(), ["10007", "10009"])

    def test_ineligible_target_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "uygun değil"):
            research_walk_forward_backtest(
                generated_frame(12),
                config=self.config(),
                target_ids=("10003",),
            )


if __name__ == "__main__":
    unittest.main()
