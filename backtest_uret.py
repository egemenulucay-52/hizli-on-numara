import argparse
from pathlib import Path

import pandas as pd

from analysis.backtest import walk_forward_backtest
from analysis.config import AnalysisConfig
from analysis.evaluation import summarize_backtest_windows
from veri_modeli import veri_cercevesini_normalize_et


def parse_args():
    parser = argparse.ArgumentParser(
        description="Hızlı On Numara tarihsel walk-forward backtest üreticisi"
    )
    parser.add_argument("--input", default="hizli_on_numara.csv")
    parser.add_argument("--output", default="artifacts/backtest_results.csv")
    parser.add_argument("--summary", default="artifacts/backtest_summary.csv")
    parser.add_argument(
        "--last",
        type=int,
        default=500,
        help="Değerlendirilecek en son hedef sayısı; tüm tarih için 0",
    )
    parser.add_argument("--minimum-training", type=int, default=500)
    return parser.parse_args()


def main():
    args = parse_args()
    data = pd.read_csv(args.input, dtype={"CekilisNo": str})
    data = veri_cercevesini_normalize_et(data)
    config = AnalysisConfig(minimum_training_size=args.minimum_training)
    results = walk_forward_backtest(
        data,
        config=config,
        last=None if args.last == 0 else args.last,
    )

    output_path = Path(args.output)
    summary_path = Path(args.summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)
    summarize_backtest_windows(results).to_csv(summary_path, index=False)
    print(f"{len(results)} walk-forward değerlendirmesi yazıldı: {output_path}")


if __name__ == "__main__":
    main()
