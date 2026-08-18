from dataclasses import dataclass
from hashlib import sha256

import numpy as np
import pandas as pd

from analysis.backtest import chronological_standard_draws
from analysis.bayesian import m8_bayesian_conditional_score
from analysis.benchmark import expected_random_hits
from analysis.config import MODEL_NAMES
from analysis.ensemble import (
    rank_numbers,
    robust_percentile_rank,
    score_state,
)
from analysis.evaluation import SELECTION_SIZES, evaluate_ranking
from analysis.hypergraph import (
    context_triple_scores,
    regularized_relation_scores,
    triple_score_vector,
)
from analysis.joint_sets import (
    JointSetScorer,
    optimize_hypergraph_sets,
    optimize_joint_sets,
)
from analysis.m4_variants import calculate_m4_variants
from analysis.ml_training import OnlineLogisticRanker
from analysis.model_registry import M4_VARIANTS, RESEARCH_MODEL_NAMES
from analysis.research_config import ResearchConfig
from analysis.research_state import ResearchState
from veri_modeli import SAYI_KOLONLARI


M10_FEATURE_NAMES = (
    "M1",
    "M2",
    "M3",
    "M4-A",
    "M4-B",
    "M4-C",
    "M4-D",
    "M4-E",
    "M4-F",
    "M5",
    "M6",
    "Ensemble",
    "M8",
    "M9Context",
    "RecencyRank",
    "LatestMembership",
    "NumberPosition",
)


@dataclass
class ResearchBacktestResult:
    results: pd.DataFrame
    m10_state: dict
    final_state: ResearchState
    config: ResearchConfig
    data_fingerprint: str


def _data_fingerprint(draws):
    columns = ["CekilisNo", *SAYI_KOLONLARI]
    canonical = draws[columns].astype(str).agg("|".join, axis=1).str.cat(sep="\n")
    return sha256(canonical.encode("utf-8")).hexdigest()


def _model_features(state, normalized, ensemble, m4_normalized, m8, m9_context):
    latest_membership = np.zeros(80, dtype=float)
    latest_membership[state.latest_draw] = 1.0
    recency = 1.0 - robust_percentile_rank(state.baseline.gaps.astype(float))
    columns = [
        normalized["M1"],
        normalized["M2"],
        normalized["M3"],
        m4_normalized["M4-A"],
        m4_normalized["M4-B"],
        m4_normalized["M4-C"],
        m4_normalized["M4-D"],
        m4_normalized["M4-E"],
        m4_normalized["M4-F"],
        normalized["M5"],
        normalized["M6"],
        robust_percentile_rank(ensemble),
        m8,
        m9_context,
        recency,
        latest_membership,
        np.arange(80, dtype=float) / 79.0,
    ]
    return np.column_stack(columns)


def build_research_bundle(state, m10_model, include_set_components=False):
    _, normalized, ensemble, baseline_rankings = score_state(state.baseline)
    m4_raw = calculate_m4_variants(state)
    m4_normalized = {
        model: robust_percentile_rank(values) for model, values in m4_raw.items()
    }
    m8_raw = m8_bayesian_conditional_score(
        state.baseline.transition_counts,
        state.baseline.transition_exposure,
        state.latest_draw,
        state.config.bayesian_prior_strength,
        state.config.relation_clip,
    )
    m8 = robust_percentile_rank(m8_raw)

    pair_raw = regularized_relation_scores(
        state.baseline.pair_counts,
        state.draw_count,
        group_size=2,
        minimum_support=10,
        clip=state.config.relation_clip,
    )
    m9_context_raw = context_triple_scores(
        state.triple_counts,
        state.draw_count,
        state.latest_draw,
        minimum_support=state.config.triple_min_support,
        clip=state.config.relation_clip,
    )
    m9_context = robust_percentile_rank(m9_context_raw)
    features = _model_features(
        state, normalized, ensemble, m4_normalized, m8, m9_context
    )
    m10_probability = m10_model.predict_proba(features)
    m10 = robust_percentile_rank(m10_probability)
    candidate_score = (
        0.30 * robust_percentile_rank(ensemble)
        + 0.20 * m4_normalized["M4-C"]
        + 0.20 * m8
        + 0.15 * m9_context
        + 0.15 * m10
    )
    bundle = {
        "normalized": normalized,
        "ensemble": ensemble,
        "baseline_rankings": baseline_rankings,
        "m4": m4_normalized,
        "m8": m8,
        "m9_context": m9_context,
        "m10": m10,
        "features": features,
        "candidate_score": candidate_score,
        "pair_component": 0.5 + 0.5 * np.tanh(pair_raw / 2.0),
    }
    if include_set_components:
        triple_raw = triple_score_vector(
            state.triple_counts,
            state.draw_count,
            minimum_support=state.config.triple_min_support,
            clip=state.config.relation_clip,
        )
        bundle["triple_component"] = 0.5 + 0.5 * np.tanh(triple_raw / 2.0)
    return bundle


def predictions_from_bundle(state, bundle, include_set_models=True):
    predictions = {}
    baseline_rankings = bundle["baseline_rankings"]
    for model in ("M1", "M2", "M3", "M5", "M6"):
        predictions[model] = {
            size: tuple(map(int, baseline_rankings[model][:size]))
            for size in SELECTION_SIZES
        }
    predictions["Ensemble"] = {
        size: tuple(map(int, baseline_rankings["Ensemble"][:size]))
        for size in SELECTION_SIZES
    }
    for model in M4_VARIANTS:
        ranking = rank_numbers(bundle["m4"][model])
        predictions[model] = {
            size: tuple(map(int, ranking[:size])) for size in SELECTION_SIZES
        }
    for model, scores in (("M8", bundle["m8"]), ("M10", bundle["m10"])):
        ranking = rank_numbers(scores)
        predictions[model] = {
            size: tuple(map(int, ranking[:size])) for size in SELECTION_SIZES
        }

    if include_set_models:
        candidate_ranking = rank_numbers(bundle["candidate_score"])
        candidates = candidate_ranking[: state.config.candidate_pool_size]
        joint_scorer = JointSetScorer(
            individual=bundle["candidate_score"],
            pair_matrix=bundle["pair_component"],
            triple_scores=bundle["triple_component"],
            conditional=bundle["m4"]["M4-C"],
            structural=bundle["normalized"]["M6"],
            bayesian=bundle["m8"],
            weights=state.config.weights,
        )
        predictions["M7"] = optimize_joint_sets(
            candidates, joint_scorer, beam_width=state.config.beam_width
        )
        predictions["M9"] = optimize_hypergraph_sets(
            candidates,
            bundle["pair_component"],
            bundle["triple_component"],
            beam_width=state.config.beam_width,
        )
    return predictions


def _new_m10(config, state=None):
    return OnlineLogisticRanker(
        M10_FEATURE_NAMES,
        learning_rate=config.m10_learning_rate,
        l2=config.m10_l2,
        state=state,
    )


def research_walk_forward_backtest(df, config=None, last=None):
    config = config or ResearchConfig()
    draws = chronological_standard_draws(df)
    numeric_ids = draws["CekilisNo"].astype(int).to_numpy()
    eligible = [
        index
        for index in range(config.minimum_training_size, len(draws))
        if numeric_ids[index] == numeric_ids[index - 1] + 1
    ]
    if not eligible:
        raise ValueError("Araştırma backtesti için ardışık hedef yok.")
    selected = set(eligible[-(last or config.research_target_count) :])

    state = ResearchState(config)
    for index in range(config.minimum_training_size):
        row = draws.iloc[index]
        state.update(row[SAYI_KOLONLARI].to_numpy(dtype=int), row["CekilisNo"])
    m10 = _new_m10(config)
    records = []
    eligible_counter = 0

    for target_index in range(config.minimum_training_size, len(draws)):
        target = draws.iloc[target_index]
        actual = target[SAYI_KOLONLARI].to_numpy(dtype=int)
        is_consecutive = numeric_ids[target_index] == numeric_ids[target_index - 1] + 1
        if is_consecutive:
            if state.latest_draw_id != str(draws.iloc[target_index - 1]["CekilisNo"]):
                raise AssertionError("Research look-ahead koruması ihlal edildi.")
            should_record = target_index in selected
            should_update_m10 = eligible_counter % config.m10_update_interval == 0
            bundle = None
            if should_record or should_update_m10:
                bundle = build_research_bundle(
                    state, m10, include_set_components=should_record
                )
            if should_record:
                predictions = predictions_from_bundle(state, bundle, include_set_models=True)
                record = {
                    "Train End Draw": state.latest_draw_id,
                    "Target Draw": str(target["CekilisNo"]),
                    "Training Size": state.draw_count,
                    "Research Version": config.research_version,
                    "Research Config Hash": config.config_hash,
                }
                for model in RESEARCH_MODEL_NAMES:
                    model_predictions = predictions[model]
                    for size in SELECTION_SIZES:
                        selected_set = model_predictions[size]
                        record[f"{model} Set@{size}"] = " ".join(map(str, selected_set))
                        record[f"{model} Hit@{size}"] = len(set(selected_set) & set(actual))
                for size in SELECTION_SIZES:
                    record[f"Random Expected Hit@{size}"] = expected_random_hits(size)
                records.append(record)
            if should_update_m10:
                m10.update(bundle["features"], actual)
            eligible_counter += 1
        state.update(actual, target["CekilisNo"])

    return ResearchBacktestResult(
        results=pd.DataFrame(records),
        m10_state=m10.state_dict(),
        final_state=state,
        config=config,
        data_fingerprint=_data_fingerprint(draws),
    )


def current_research_predictions(df, config=None, m10_state=None):
    config = config or ResearchConfig()
    draws = chronological_standard_draws(df)
    state = ResearchState(config)
    for _, row in draws.iterrows():
        state.update(row[SAYI_KOLONLARI].to_numpy(dtype=int), row["CekilisNo"])
    m10 = _new_m10(config, state=m10_state)
    bundle = build_research_bundle(state, m10, include_set_components=True)
    return predictions_from_bundle(state, bundle, include_set_models=True), state, bundle
