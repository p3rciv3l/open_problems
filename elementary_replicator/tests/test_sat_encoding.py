import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from elementary_replicator.direct_search import search
from elementary_replicator.sat_clean_doubling import exclude_scope, main


class SatEncodingTests(unittest.TestCase):
    def test_selected_beyond_three_by_three_scopes_are_unsat(self):
        for width, height, time in ((4, 4, 2), (5, 3, 2), (6, 6, 3)):
            result = exclude_scope(width, height, time)
            self.assertGreater(result.offset_pairs, 0)
            self.assertFalse(result.satisfiable)

    def test_geometrically_impossible_scope_has_no_pairs(self):
        result = exclude_scope(4, 4, 1)
        self.assertEqual(result.offset_pairs, 0)
        self.assertFalse(result.satisfiable)

    def test_independent_explicit_state_scope_is_empty(self):
        result = search(max_side=3, max_time=2)
        self.assertEqual((result.seeds, result.cases), (365, 730))
        self.assertEqual(result.witnesses, ())

    def test_search_rejects_empty_bounds(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            search(max_side=0, max_time=2)

    def test_cli_rejects_empty_scope(self):
        for flag in ("--max-side", "--max-time"):
            with self.subTest(flag=flag):
                stderr = io.StringIO()
                with (
                    patch.object(sys, "argv", ["sat_clean_doubling", flag, "0"]),
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as raised,
                ):
                    main()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(f"{flag}: must be positive", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
