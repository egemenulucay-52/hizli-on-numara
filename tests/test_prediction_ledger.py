import json
from pathlib import Path
import tempfile
import unittest

from analysis.prediction_ledger import (
    GENESIS_HASH,
    append_events,
    compact_models,
    pending_predictions,
    prediction_created_payload,
    prediction_evaluated_payload,
    read_ledger,
    seal_event,
)


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


if __name__ == "__main__":
    unittest.main()
