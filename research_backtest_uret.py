import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from analysis.evaluation import summarize_backtest, summarize_backtest_windows
from analysis.hypergraph import significant_triple_diagnostics
from analysis.model_registry import M4_VARIANTS, RESEARCH_MODEL_NAMES
from analysis.research_backtest import research_walk_forward_backtest
from analysis.research_config import ResearchConfig
from analysis.research_protocol import (
    CONTAMINATED_PHASE,
    DEVELOPMENT_PHASE,
    VALIDATION_PHASE,
    load_protocol,
    target_ids_for_phase,
)
from analysis.tail_metrics import summarize_tail_metrics
from veri_modeli import veri_cercevesini_normalize_et


def parse_args():
    parser = argparse.ArgumentParser(description="M1-M10 araştırma backtest üreticisi")
    parser.add_argument("--input", default="hizli_on_numara.csv")
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--split",
        choices=("development", "validation", "contaminated"),
        default="contaminated",
        help="Kilitli tarihsel bölüm bu komuttan bilinçli olarak çıkarılmıştır.",
    )
    parser.add_argument("--last", type=int)
    parser.add_argument("--candidate-pool", type=int, default=15)
    parser.add_argument("--beam-width", type=int, default=50)
    return parser.parse_args()


def main():
    args = parse_args()
    data = pd.read_csv(args.input, dtype={"CekilisNo": str})
    data = veri_cercevesini_normalize_et(data)
    phase_by_name = {
        "development": DEVELOPMENT_PHASE,
        "validation": VALIDATION_PHASE,
        "contaminated": CONTAMINATED_PHASE,
    }
    phase = phase_by_name[args.split]
    target_ids = target_ids_for_phase(phase)
    if args.last is not None and args.last < 1:
        raise ValueError("--last pozitif bir tam sayı olmalıdır.")
    evaluation_count = min(args.last or len(target_ids), len(target_ids))
    config = ResearchConfig(
        research_target_count=evaluation_count,
        candidate_pool_size=args.candidate_pool,
        beam_width=args.beam_width,
    )
    run = research_walk_forward_backtest(
        data, config=config, last=args.last, target_ids=target_ids
    )
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.split == "contaminated":
        output_dir = Path("artifacts")
    else:
        output_dir = Path("artifacts") / "protocol_v1" / args.split
    output_dir.mkdir(parents=True, exist_ok=True)
    run.results.to_csv(output_dir / "research_backtest_results.csv", index=False)
    summarize_backtest_windows(run.results, models=RESEARCH_MODEL_NAMES).to_csv(
        output_dir / "research_backtest_summary.csv", index=False
    )
    tail = summarize_tail_metrics(
        run.results,
        models=RESEARCH_MODEL_NAMES,
        windows=(None, 25, 50, 100, 250),
    )
    tail.to_csv(output_dir / "research_tail_summary.csv", index=False)
    summarize_backtest(run.results, models=M4_VARIANTS).to_csv(
        output_dir / "m4_ablation_results.csv", index=False
    )
    significant_triple_diagnostics(
        run.final_state.triple_counts,
        run.final_state.draw_count,
        minimum_support=config.triple_min_support,
    ).head(500).to_csv(output_dir / "hypergraph_fdr.csv", index=False)
    (output_dir / "research_model_state.json").write_text(
        json.dumps({"M10": run.m10_state}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    protocol = load_protocol()
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_fingerprint": run.data_fingerprint,
        "research_config": config.as_dict(),
        "research_config_hash": config.config_hash,
        "evaluation_count": len(run.results),
        "last_target": None if run.results.empty else str(run.results.iloc[-1]["Target Draw"]),
        "historical_only": True,
        "evaluation_phase": phase,
        "research_protocol_version": protocol["protocol_version"],
        "research_protocol_hash": protocol["protocol_hash"],
        "confirmatory_use": False,
        "ensemble_v2_enabled": False,
    }
    (output_dir / "research_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(run.results)} M1-M10 araştırma hedefi yazıldı.")


if __name__ == "__main__":
    main()
