import unittest

from glider_synthesis_basis.life import is_still_life, run, step, translate
from glider_synthesis_basis.reactions import BLOCK, G_SE


class LifeTests(unittest.TestCase):
    def test_block_is_still(self):
        self.assertTrue(is_still_life(BLOCK))
        self.assertEqual(step(BLOCK), BLOCK)

    def test_glider_translates_after_four_generations(self):
        self.assertEqual(run(G_SE, 4), translate(G_SE, 1, 1))

    def test_run_rejects_negative_generation(self):
        with self.assertRaises(ValueError):
            run(BLOCK, -1)


if __name__ == "__main__":
    unittest.main()
