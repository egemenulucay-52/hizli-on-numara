"""Evaluate pending live predictions and create exactly one next-draw prediction."""

import argparse
import json
from pathlib import Path

import pandas as pd

from analysis.ml_training import OnlineLogisticRanker
from analysis.prediction_ledger import (
    append_events,
    compact_models,
    created_events,
    latest_m10_state,
    pending_predictions,
    prediction_created_payload,
    prediction_evaluated_payload,
    read_ledger,
)
from analysis.research_backtest import (
    M10_FEATURE_NAMES,
    current_research_predictions,
)
from analysis.research_config import ResearchConfig
from analysis.research_protocol import protocol_ledger_metadata
from veri_modeli import (
    SAYI_KOLONLARI,
    cekilisleri_sirala,
    veri_cercevesini_dogrula,
    veri_cercevesini_normalize_et,
)


def load_draws(path):
    data = pd.read_csv(path, dtype={"CekilisNo": str})
    data = veri_cercevesini_normalize_et(data)
    veri_cercevesini_dogrula(data)
    data[SAYI_KOLONLARI] = data[SAYI_KOLONLARI].apply(pd.to_numeric)
    return cekilisleri_sirala(data)


def empty_m10_state(config):
    return OnlineLogisticRanker(
        M10_FEATURE_NAMES,
        learning_rate=config.m10_learning_rate,
        l2=config.m10_l2,
    ).state_dict()


def load_historical_m10_state(path, metadata_path, config):
    with Path(metadata_path).open("r", encoding="utf-8") as stream:
        metadata = json.load(stream)
    if metadata.get("research_config_hash") != config.config_hash:
        return empty_m10_state(config)
    with Path(path).open("r", encoding="utf-8") as stream:
        stored = json.load(stream)
    return stored["M10"]


def rows_through(draws, draw_id):
    numeric_ids = pd.to_numeric(draws["CekilisNo"], errors="raise")
    selected = draws[numeric_ids <= int(draw_id)].copy()
    if selected.empty or str(selected.iloc[0]["CekilisNo"]) != str(draw_id):
        raise ValueError(f"{draw_id} eğitim sonu veride bulunamadı.")
    return selected


def update_live_ledger(draws, ledger_path, historical_state, config=None):
    config = config or ResearchConfig()
    events = read_ledger(ledger_path)
    new_payloads = []
    actual_by_id = {
        str(row["CekilisNo"]): row[SAYI_KOLONLARI].to_numpy(dtype=int)
        for _, row in draws.iterrows()
    }
    m10_state = latest_m10_state(
        events, historical_state, config_hash=config.config_hash
    )
    protocol_metadata = protocol_ledger_metadata()

    for created in sorted(
        pending_predictions(events), key=lambda event: int(event["target_draw"])
    ):
        target_draw = str(created["target_draw"])
        if target_draw not in actual_by_id:
            continue
        if created.get("config_hash") == config.config_hash:
            prediction_state = created["m10_state"]
            history = rows_through(draws, created["train_end_draw"])
            _, _, bundle = current_research_predictions(
                history, config=config, m10_state=prediction_state
            )
            ranker = OnlineLogisticRanker(
                M10_FEATURE_NAMES,
                learning_rate=config.m10_learning_rate,
                l2=config.m10_l2,
                state=prediction_state,
            )
            ranker.update(bundle["features"], actual_by_id[target_draw])
            m10_state = ranker.state_dict()
        new_payloads.append(
            prediction_evaluated_payload(
                created_event=created,
                actual_numbers=actual_by_id[target_draw],
                m10_state_after=m10_state,
            )
        )

    latest_draw = str(draws.iloc[0]["CekilisNo"])
    target_draw = str(int(latest_draw) + 1)
    known_created = created_events(events)
    if target_draw not in known_created:
        predictions, _, _ = current_research_predictions(
            draws, config=config, m10_state=m10_state
        )
        new_payloads.append(
            prediction_created_payload(
                target_draw=target_draw,
                train_end_draw=latest_draw,
                models=compact_models(predictions),
                research_version=config.research_version,
                config_hash=config.config_hash,
                m10_state=m10_state,
                protocol_metadata=protocol_metadata,
            )
        )

    appended = append_events(ledger_path, events, new_payloads)
    return appended


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="hizli_on_numara.csv")
    parser.add_argument("--ledger", default="artifacts/prediction_ledger.jsonl")
    parser.add_argument(
        "--model-state", default="artifacts/research_model_state.json"
    )
    parser.add_argument(
        "--research-metadata", default="artifacts/research_metadata.json"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = ResearchConfig()
    appended = update_live_ledger(
        load_draws(args.csv),
        args.ledger,
        load_historical_m10_state(args.model_state, args.research_metadata, config),
        config=config,
    )
    if appended:
        event_types = ", ".join(event["event_type"] for event in appended)
        print(f"{len(appended)} olay eklendi: {event_types}")
    else:
        print("Canlı tahmin günlüğü güncel; yeni olay yok.")


if __name__ == "__main__":
    main()
