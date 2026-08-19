"""Append-only, hash-chained live prediction journal helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile


GENESIS_HASH = "0" * 64
LEDGER_VERSION = "1.0.0"


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def content_hash(value):
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def seal_event(payload, previous_hash):
    event = dict(payload)
    event["ledger_version"] = LEDGER_VERSION
    event["previous_hash"] = previous_hash
    event["event_hash"] = content_hash(event)
    return event


def verify_events(events):
    previous_hash = GENESIS_HASH
    seen_hashes = set()
    for position, event in enumerate(events, start=1):
        if event.get("previous_hash") != previous_hash:
            raise ValueError(f"Ledger zinciri {position}. olayda koptu.")
        supplied_hash = event.get("event_hash")
        unsigned = {key: value for key, value in event.items() if key != "event_hash"}
        expected_hash = content_hash(unsigned)
        if supplied_hash != expected_hash:
            raise ValueError(f"Ledger özeti {position}. olayda doğrulanamadı.")
        if supplied_hash in seen_hashes:
            raise ValueError("Ledger içinde yinelenen olay özeti var.")
        seen_hashes.add(supplied_hash)
        previous_hash = supplied_hash
    return previous_hash


def read_ledger(path):
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    events = []
    with ledger_path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Ledger {line_number}. satırı geçerli JSON değil."
                ) from error
    verify_events(events)
    return events


def append_events(path, events, payloads):
    """Payload'ları zincirleyip dosyayı tek atomik değişimle günceller."""

    verified_tail = verify_events(events)
    sealed = []
    previous_hash = verified_tail
    for payload in payloads:
        event = seal_event(payload, previous_hash)
        sealed.append(event)
        previous_hash = event["event_hash"]
    if not sealed:
        return []

    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{ledger_path.name}.", suffix=".tmp", dir=ledger_path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            for event in [*events, *sealed]:
                stream.write(canonical_json(event))
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, ledger_path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return sealed


def created_events(events):
    return {
        str(event["target_draw"]): event
        for event in events
        if event.get("event_type") == "prediction_created"
    }


def evaluated_targets(events):
    return {
        str(event["target_draw"])
        for event in events
        if event.get("event_type") == "prediction_evaluated"
    }


def pending_predictions(events):
    evaluated = evaluated_targets(events)
    return [
        event
        for event in events
        if event.get("event_type") == "prediction_created"
        and str(event["target_draw"]) not in evaluated
    ]


def latest_m10_state(events, fallback_state, config_hash=None):
    created_by_hash = {
        event.get("event_hash"): event
        for event in events
        if event.get("event_type") == "prediction_created"
    }
    for event in reversed(events):
        state = event.get("m10_state_after")
        if event.get("event_type") != "prediction_evaluated" or not state:
            continue
        if config_hash is not None:
            created = created_by_hash.get(event.get("created_event_hash"))
            if created is None or created.get("config_hash") != config_hash:
                continue
        return state
    return fallback_state


def prediction_created_payload(
    *, target_draw, train_end_draw, models, research_version, config_hash, m10_state,
    created_at=None, protocol_metadata=None,
):
    payload = {
        "event_type": "prediction_created",
        "created_at": created_at or utc_now(),
        "target_draw": str(target_draw),
        "train_end_draw": str(train_end_draw),
        "research_version": research_version,
        "config_hash": config_hash,
        "m10_state": m10_state,
        "models": models,
    }
    if protocol_metadata:
        payload.update(protocol_metadata)
    return payload


def prediction_evaluated_payload(
    *, created_event, actual_numbers, m10_state_after, evaluated_at=None,
):
    actual = {int(number) for number in actual_numbers}
    results = {}
    for model, selections in created_event["models"].items():
        model_result = {}
        for size in (4, 5, 6):
            selected = {int(number) for number in selections[f"set_at_{size}"]}
            hits = len(selected & actual)
            model_result[f"hit_at_{size}"] = hits
            model_result[f"exact_{size}"] = hits == size
            model_result[f"nearperfect_{size}"] = hits >= size - 1
        results[model] = model_result
    return {
        "event_type": "prediction_evaluated",
        "evaluated_at": evaluated_at or utc_now(),
        "target_draw": str(created_event["target_draw"]),
        "created_event_hash": created_event.get("event_hash"),
        "actual_numbers": sorted(actual),
        "results": results,
        "m10_state_after": m10_state_after,
    }


def compact_models(predictions):
    return {
        model: {
            f"set_at_{size}": [int(number) for number in selections[size]]
            for size in (4, 5, 6)
        }
        for model, selections in predictions.items()
    }
