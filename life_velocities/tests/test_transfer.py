import json
import tempfile
import unittest
from pathlib import Path

from life_velocities.transfer import Background, TransferSearch, TransferSpec
from life_velocities.verify_transfer import verify_result


HERE = Path(__file__).parents[1]
BACKGROUND = HERE / "backgrounds" / "block_lattice_6x4.json"


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.background = Background.load(BACKGROUND)

    def test_stated_background_is_life_and_translation_compatible(self):
        search = TransferSearch(TransferSpec(), self.background)
        for phase in range(self.background.x_period):
            state = search.background_state(phase)
            self.assertTrue(
                search.valid_extension(state, search.background_column(phase + 1))
            )

    def test_last_timeslice_uses_displaced_column(self):
        search = TransferSearch(TransferSpec(max_column_deviations=0), self.background)
        state = search.background_state(0)
        damaged = list(state[1])
        damaged[0] ^= 1
        self.assertFalse(
            search.valid_extension(
                (state[0], tuple(damaged)),
                search.background_column(1),
            )
        )

    def test_zero_deviation_class_is_exactly_background_cycle(self):
        search = TransferSearch(TransferSpec(max_column_deviations=0), self.background)
        result = search.search()
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["reachable_states"], self.background.x_period)
        self.assertEqual(result["reachable_edges"], self.background.x_period)

    def test_compressed_expander_equals_raw_alphabet(self):
        search = TransferSearch(TransferSpec(max_column_deviations=2), self.background)
        for phase in range(self.background.x_period):
            state = search.background_state(phase)
            compressed = set(search.extension_columns(state))
            raw = {
                column
                for column in search.candidates(phase + 1)
                if search.valid_extension(state, column)
            }
            self.assertEqual(compressed, raw)

    def test_result_round_trips_as_json(self):
        result = TransferSearch(
            TransferSpec(max_column_deviations=0), self.background
        ).search()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps(result))
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(verify_result(path, BACKGROUND), [])

    def test_preserved_k1_absence_scope(self):
        result = json.loads(
            (HERE / "results" / "isolated_block6x4_k1.json").read_text()
        )
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["spec"]["period"], 10)
        self.assertEqual(result["spec"]["displacement"], 6)
        self.assertEqual(result["spec"]["max_column_deviations"], 1)
        self.assertEqual(result["state_class"]["candidate_columns_per_phase"], 41)
        self.assertEqual(result["reachable_states"], 8862)
        self.assertEqual(result["reachable_edges"], 8862)
        self.assertEqual(
            result["ordered_graph_sha256"],
            "68dc45920a04ca8186d7612407da0374a75628bbac77e11b49bea50fc446550e",
        )

    def test_preserved_k2_absence_scope(self):
        result = json.loads(
            (HERE / "results" / "isolated_block6x4_k2.json").read_text()
        )
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["spec"]["period"], 10)
        self.assertEqual(result["spec"]["displacement"], 6)
        self.assertEqual(result["spec"]["max_column_deviations"], 2)
        self.assertEqual(result["state_class"]["candidate_columns_per_phase"], 821)
        self.assertEqual(result["reachable_states"], 371885)
        self.assertEqual(result["reachable_edges"], 371885)
        self.assertEqual(
            result["ordered_graph_sha256"],
            "5ad188dfa4698aa8af22626475afd12bbb3a014c4b536b1d0f1545f9aa10f488",
        )

    def test_incompatible_static_background_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "divide the displacement"):
            TransferSearch(TransferSpec(displacement=5), self.background)


if __name__ == "__main__":
    unittest.main()
