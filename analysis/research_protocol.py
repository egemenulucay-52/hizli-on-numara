"""Research Protocol v1 lock and split-manifest access helpers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL_PATH = REPOSITORY_ROOT / "protocols" / "research_protocol_v1.json"
DEFAULT_MANIFEST_PATH = REPOSITORY_ROOT / "artifacts" / "research_split_manifest.csv"

TRAINING_PHASE = "training_history"
DEVELOPMENT_PHASE = "historical_development"
VALIDATION_PHASE = "historical_validation"
LOCKED_PHASE = "retrospective_locked_candidate"
CONTAMINATED_PHASE = "historical_contaminated"
INELIGIBLE_PHASE = "ineligible_nonconsecutive"
UNLOCKED_RESEARCH_PHASES = (
    DEVELOPMENT_PHASE,
    VALIDATION_PHASE,
    CONTAMINATED_PHASE,
)


def canonical_json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def object_hash(value):
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_hash(path):
    content = Path(path).read_bytes()
    canonical_content = content.replace(b"\r\n", b"\n")
    return sha256(canonical_content).hexdigest()


def load_protocol(path=DEFAULT_PROTOCOL_PATH):
    with Path(path).open("r", encoding="utf-8") as stream:
        protocol = json.load(stream)
    supplied_hash = protocol.get("protocol_hash")
    unsigned = {key: value for key, value in protocol.items() if key != "protocol_hash"}
    expected_hash = object_hash(unsigned)
    if supplied_hash != expected_hash:
        raise ValueError("Research Protocol v1 hash doğrulaması başarısız.")
    return protocol


def load_split_manifest(
    protocol_path=DEFAULT_PROTOCOL_PATH, manifest_path=DEFAULT_MANIFEST_PATH
):
    protocol = load_protocol(protocol_path)
    expected_hash = protocol["data_lock"]["split_manifest_sha256"]
    if file_hash(manifest_path) != expected_hash:
        raise ValueError("Split manifest hash doğrulaması başarısız.")
    manifest = pd.read_csv(manifest_path, dtype={"DrawID": str, "PreviousDrawID": str})
    expected_rows = protocol["data_lock"]["standard_draw_count"]
    if len(manifest) != expected_rows:
        raise ValueError("Split manifest satır sayısı protokolle uyuşmuyor.")
    return manifest


def assert_phase_is_unlocked(phase):
    if phase == LOCKED_PHASE:
        raise PermissionError(
            "Retrospective locked candidate kapalıdır; standart araştırma komutu "
            "bu hedefleri değerlendiremez."
        )
    if phase not in UNLOCKED_RESEARCH_PHASES:
        raise ValueError(f"Araştırma sonucu üretilemeyen phase: {phase}")


def target_ids_for_phase(phase, manifest=None):
    assert_phase_is_unlocked(phase)
    manifest = manifest if manifest is not None else load_split_manifest()
    selected = manifest[
        manifest["EligibleTarget"].astype(bool) & manifest["Phase"].eq(phase)
    ]
    return selected["DrawID"].astype(str).tolist()


def assert_target_ids_do_not_include_locked(target_ids, manifest=None):
    manifest = manifest if manifest is not None else load_split_manifest()
    locked_ids = set(
        manifest.loc[manifest["Phase"].eq(LOCKED_PHASE), "DrawID"].astype(str)
    )
    overlap = sorted(locked_ids.intersection(map(str, target_ids)), key=int)
    if overlap:
        raise PermissionError(
            "Retrospective locked candidate hedefleri standart backtest ile "
            "değerlendirilemez: " + ", ".join(overlap[:5])
        )


def protocol_ledger_metadata(protocol=None):
    protocol = protocol or load_protocol()
    final_locked = protocol["model_lock"]["status"] == "final_model_locked"
    return {
        "research_protocol_version": protocol["protocol_version"],
        "research_protocol_hash": protocol["protocol_hash"],
        "evaluation_phase": (
            "prospective_live_confirmatory"
            if final_locked
            else "protocol_v1_observational_prelock"
        ),
    }
