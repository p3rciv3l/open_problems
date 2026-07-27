import unittest

from glider_synthesis_basis.corpus import (
    REWINDABLE_TWO_GLIDER_CORPUS,
    candidate_basis_report,
    certify_rewindable,
    corpus_population_spectrum,
)
from glider_synthesis_basis.embedding import (
    certify_noninteraction,
    independent_union,
)
from glider_synthesis_basis.life import translate
from glider_synthesis_basis.model import verify_move


class EmbeddingTests(unittest.TestCase):
    def test_distance_three_trace_certificate_proves_union(self):
        block_move = REWINDABLE_TWO_GLIDER_CORPUS[1]
        shifted = block_move.translated(8, 0)
        certificate = certify_noninteraction(
            block_move.initial_state,
            shifted.initial_state,
            block_move.duration,
        )
        self.assertEqual(certificate.minimum_separation, 3)
        combined = independent_union("two_independent_blocks", (block_move, shifted))
        self.assertTrue(verify_move(combined).valid)
        self.assertEqual(len(combined.output_context), 8)

    def test_too_close_traces_are_rejected(self):
        block_move = REWINDABLE_TWO_GLIDER_CORPUS[1]
        with self.assertRaisesRegex(ValueError, "separation"):
            certify_noninteraction(
                block_move.initial_state,
                translate(block_move.initial_state, 7, 0),
                block_move.duration,
            )

    def test_substantial_corpus_is_simulated_and_rewindable(self):
        self.assertEqual(len(REWINDABLE_TWO_GLIDER_CORPUS), 8)
        self.assertEqual(corpus_population_spectrum(), (0, 4, 6, 7, 8, 8, 16, 24))
        self.assertEqual(
            len({move.canonical_key() for move in REWINDABLE_TWO_GLIDER_CORPUS}),
            8,
        )
        for move in REWINDABLE_TWO_GLIDER_CORPUS:
            with self.subTest(move=move.name):
                self.assertTrue(verify_move(move).valid)
                certificate = certify_rewindable(move)
                self.assertEqual(certificate.cycles, 10)

    def test_b8_candidate_report_is_exactly_scoped(self):
        report = candidate_basis_report()
        self.assertEqual(report.reaction_classes, 8)
        self.assertEqual(report.exact_contexts_from_empty, 8)
        self.assertTrue(report.supports_certified_independent_embedding)
        self.assertFalse(report.universal_claim)


if __name__ == "__main__":
    unittest.main()
