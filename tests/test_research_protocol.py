import json
from pathlib import Path
import unittest

from analysis.config import AnalysisConfig
from analysis.research_config import ResearchConfig
from analysis.research_protocol import (
    CONTAMINATED_PHASE,
    DEVELOPMENT_PHASE,
    LOCKED_PHASE,
    VALIDATION_PHASE,
    assert_phase_is_unlocked,
    assert_target_ids_do_not_include_locked,
    load_protocol,
    load_protocol_amendment,
    load_split_manifest,
    protocol_ledger_metadata,
    target_ids_for_phase,
)


class ResearchProtocolTests(unittest.TestCase):
    def test_protocol_and_manifest_hashes_are_valid(self):
        protocol = load_protocol()
        manifest = load_split_manifest()
        self.assertEqual(protocol["protocol_version"], "1.0.0")
        self.assertEqual(len(manifest), 17552)

    def test_frequency_window_amendment_is_hash_chained_to_protocol(self):
        protocol = load_protocol()
        amendment = load_protocol_amendment(protocol=protocol)
        self.assertEqual(amendment["amendment_version"], "001")
        self.assertEqual(amendment["parent_protocol_hash"], protocol["protocol_hash"])
        self.assertEqual(amendment["changes"]["short_window"]["to"], 10)
        self.assertEqual(amendment["changes"]["long_window"]["to"], 50)
        self.assertEqual(amendment["changes"]["deviation_window"]["to"], 50)
        self.assertEqual(
            amendment["configuration"]["analysis_config_hash"],
            AnalysisConfig().config_hash,
        )
        self.assertEqual(
            amendment["configuration"]["research_config_hash"],
            ResearchConfig().config_hash,
        )
        metadata = protocol_ledger_metadata(protocol=protocol, amendment=amendment)
        self.assertEqual(metadata["research_protocol_amendment_version"], "001")
        self.assertEqual(
            metadata["research_protocol_amendment_hash"], amendment["amendment_hash"]
        )

    def test_approved_plan_b_counts_are_exact(self):
        manifest = load_split_manifest()
        self.assertEqual(len(target_ids_for_phase(DEVELOPMENT_PHASE, manifest)), 5921)
        self.assertEqual(len(target_ids_for_phase(VALIDATION_PHASE, manifest)), 2960)
        self.assertEqual(len(target_ids_for_phase(CONTAMINATED_PHASE, manifest)), 1000)
        locked = manifest[
            manifest["EligibleTarget"].astype(bool)
            & manifest["Phase"].eq(LOCKED_PHASE)
        ]
        self.assertEqual(len(locked), 5922)
        self.assertTrue(locked["OutcomeAccess"].eq("LOCKED_DO_NOT_EVALUATE").all())

    def test_standard_research_access_rejects_locked_phase(self):
        with self.assertRaisesRegex(PermissionError, "kapalıdır"):
            assert_phase_is_unlocked(LOCKED_PHASE)

    def test_standard_backtest_target_guard_rejects_locked_ids(self):
        with self.assertRaisesRegex(PermissionError, "standart backtest"):
            assert_target_ids_do_not_include_locked(("41815",))


if __name__ == "__main__":
    unittest.main()
