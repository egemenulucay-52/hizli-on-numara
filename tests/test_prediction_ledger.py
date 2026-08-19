import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from analysis.prediction_ledger import (
    GENESIS_HASH,
    append_events,
    compact_models,
    latest_m10_state,
    pending_predictions,
    prediction_created_payload,
    prediction_evaluated_payload,
    read_ledger,
    seal_event,
)
from analysis.research_config import ResearchConfig
from tahmin_guncelle import load_historical_m10_state


class PredictionLedgerTests(unittest.TestCase):
    def prediction_payload(self):
        predictions = {
            "M1": {4: (1, 2, 3, 4), 5: (1, 2, 3, 4, 5), 6: (1, 2, 3, 4, 5, 6)}
        }
        return prediction_created_payload(
            target_draw="10001",
            train_end_draw="10000",
            models=compact_models(predictions),
            research_version="test",
            config_hash="abc",
            m10_state={"weights": [0.0], "bias": 0.0},
            created_at="2026-01-01T00:00:00Z",
        )

    def test_roundtrip_is_hash_chained_and_append_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            first = append_events(path, [], [self.prediction_payload()])
            loaded = read_ledger(path)
            evaluated = prediction_evaluated_payload(
                created_event=first[0],
                actual_numbers=range(1, 21),
                m10_state_after={"weights": [0.1], "bias": -1.0},
                evaluated_at="2026-01-01T00:15:00Z",
            )
            append_events(path, loaded, [evaluated])
            final = read_ledger(path)
            self.assertEqual(len(final), 2)
            self.assertEqual(final[0]["previous_hash"], GENESIS_HASH)
            self.assertEqual(final[1]["previous_hash"], final[0]["event_hash"])
            self.assertEqual(pending_predictions(final), [])
            self.assertTrue(final[1]["results"]["M1"]["exact_6"])

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            append_events(path, [], [self.prediction_payload()])
            event = json.loads(path.read_text(encoding="utf-8"))
            event["target_draw"] = "99999"
            path.write_text(json.dumps(event) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "doğrulanamadı"):
                read_ledger(path)

    def test_hash_is_deterministic_for_same_payload(self):
        payload = self.prediction_payload()
        self.assertEqual(
            seal_event(payload, GENESIS_HASH), seal_event(payload, GENESIS_HASH)
        )

    def test_protocol_metadata_is_preserved(self):
        payload = prediction_created_payload(
            target_draw="10001",
            train_end_draw="10000",
            models={},
            research_version="test",
            config_hash="abc",
            m10_state={},
            protocol_metadata={
                "research_protocol_version": "1.0.0",
                "research_protocol_hash": "protocol-hash",
                "research_protocol_amendment_version": "001",
                "research_protocol_amendment_hash": "amendment-hash",
                "evaluation_phase": "protocol_v1_observational_prelock",
            },
        )
        self.assertEqual(
            payload["evaluation_phase"], "protocol_v1_observational_prelock"
        )
        self.assertEqual(payload["research_protocol_hash"], "protocol-hash")
        self.assertEqual(
            payload["research_protocol_amendment_hash"], "amendment-hash"
        )

    def test_latest_m10_state_is_scoped_to_config_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            created = append_events(path, [], [self.prediction_payload()])
            evaluated = prediction_evaluated_payload(
                created_event=created[0],
                actual_numbers=range(1, 21),
                m10_state_after={"weights": [0.1], "bias": -1.0},
            )
            append_events(path, created, [evaluated])
            events = read_ledger(path)
            fallback = {"weights": [0.0], "bias": 0.0}
            self.assertEqual(
                latest_m10_state(events, fallback, config_hash="abc")["bias"],
                -1.0,
            )
            self.assertEqual(
                latest_m10_state(events, fallback, config_hash="new-config"),
                fallback,
            )

    def test_legacy_m10_artifact_is_reset_for_new_config(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            metadata_path = Path(directory) / "metadata.json"
            state_path.write_text(
                json.dumps({"M10": {"weights": [99.0], "bias": 99.0}}),
                encoding="utf-8",
            )
            metadata_path.write_text(
                json.dumps({"research_config_hash": "legacy-config"}),
                encoding="utf-8",
            )
            config = ResearchConfig()
            state = load_historical_m10_state(state_path, metadata_path, config)
            self.assertEqual(state["step"], 0)
            self.assertAlmostEqual(state["bias"], -1.0986122886681098)
            self.assertTrue(all(weight == 0.0 for weight in state["weights"]))

    def test_live_entrypoint_imports_without_scipy(self):
        root = Path(__file__).resolve().parents[1]
        guard = (
            "import builtins; original=builtins.__import__; "
            "builtins.__import__=lambda name,*a,**k: "
            "(_ for _ in ()).throw(ModuleNotFoundError(name)) "
            "if name.startswith('scipy') else original(name,*a,**k); "
            "import tahmin_guncelle"
        )
        completed = subprocess.run(
            [sys.executable, "-c", guard],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
