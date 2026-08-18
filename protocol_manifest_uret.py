"""Generate the approved Plan B target manifest without evaluating any model."""

from pathlib import Path

import pandas as pd

from analysis.research_backtest import _data_fingerprint
from analysis.research_protocol import (
    CONTAMINATED_PHASE,
    DEVELOPMENT_PHASE,
    INELIGIBLE_PHASE,
    LOCKED_PHASE,
    TRAINING_PHASE,
    VALIDATION_PHASE,
    file_hash,
)
from veri_modeli import veri_cercevesini_dogrula, veri_cercevesini_normalize_et


HISTORICAL_CUTOFF = 49859
MINIMUM_TRAINING_SIZE = 500
DEVELOPMENT_TARGET_COUNT = 5921
VALIDATION_TARGET_COUNT = 2960
LOCKED_TARGET_COUNT = 5922
CONTAMINATED_TARGET_COUNT = 1000


def generate_manifest(data):
    data = veri_cercevesini_normalize_et(data)
    veri_cercevesini_dogrula(data)
    standard = data[data["CekilisNo"].astype(str).str.fullmatch(r"\d{5,6}")].copy()
    standard["_id"] = pd.to_numeric(standard["CekilisNo"], errors="raise")
    standard = standard[standard["_id"] <= HISTORICAL_CUTOFF]
    standard = standard.sort_values("_id").reset_index(drop=True)
    if standard["_id"].duplicated().any():
        raise ValueError("Manifest için yinelenen standart ID bulundu.")

    ids = standard["_id"].astype(int).tolist()
    eligible_indices = [
        index
        for index in range(MINIMUM_TRAINING_SIZE, len(ids))
        if ids[index] == ids[index - 1] + 1
    ]
    expected_total = (
        DEVELOPMENT_TARGET_COUNT
        + VALIDATION_TARGET_COUNT
        + LOCKED_TARGET_COUNT
        + CONTAMINATED_TARGET_COUNT
    )
    if len(eligible_indices) != expected_total:
        raise ValueError(
            f"Beklenen {expected_total} eligible target yerine {len(eligible_indices)} bulundu."
        )

    phase_by_index = {}
    boundaries = (
        (DEVELOPMENT_PHASE, DEVELOPMENT_TARGET_COUNT),
        (VALIDATION_PHASE, VALIDATION_TARGET_COUNT),
        (LOCKED_PHASE, LOCKED_TARGET_COUNT),
        (CONTAMINATED_PHASE, CONTAMINATED_TARGET_COUNT),
    )
    cursor = 0
    for phase, count in boundaries:
        for index in eligible_indices[cursor : cursor + count]:
            phase_by_index[index] = phase
        cursor += count

    rows = []
    for index, draw_id in enumerate(ids):
        previous = "" if index == 0 else str(ids[index - 1])
        eligible = index in phase_by_index
        if index < MINIMUM_TRAINING_SIZE:
            phase = TRAINING_PHASE
        elif eligible:
            phase = phase_by_index[index]
        else:
            phase = INELIGIBLE_PHASE
        rows.append(
            {
                "ChronologicalIndex": index,
                "DrawID": str(draw_id),
                "PreviousDrawID": previous,
                "EligibleTarget": eligible,
                "Phase": phase,
                "OutcomeAccess": (
                    "LOCKED_DO_NOT_EVALUATE" if phase == LOCKED_PHASE else "ALLOWED"
                ),
            }
        )
    return pd.DataFrame(rows), standard.drop(columns="_id")


def write_outputs(
    input_path="hizli_on_numara.csv",
    manifest_path="artifacts/research_split_manifest.csv",
    fingerprint_path="artifacts/research_split_fingerprint.txt",
):
    data = pd.read_csv(input_path, dtype={"CekilisNo": str})
    manifest, frozen_draws = generate_manifest(data)
    Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    manifest_sha = file_hash(manifest_path)
    data_fingerprint = _data_fingerprint(frozen_draws)
    Path(fingerprint_path).write_text(
        f"data_fingerprint={data_fingerprint}\nmanifest_sha256={manifest_sha}\n",
        encoding="utf-8",
    )
    print(f"{len(manifest)} satır manifest yazıldı.")
    print(f"data_fingerprint={data_fingerprint}")
    print(f"manifest_sha256={manifest_sha}")


if __name__ == "__main__":
    write_outputs()
