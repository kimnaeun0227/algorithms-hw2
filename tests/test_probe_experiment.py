import tempfile
import unittest
from pathlib import Path

from experiments.probe_experiment import build_results, render_svg, render_table, write_outputs


class ProbeExperimentTests(unittest.TestCase):
    def test_builds_load_factors_and_expected_costs(self):
        results = build_results(capacity=40)

        self.assertEqual(len(results), 16)
        self.assertEqual(results[0].alpha, 0.25)
        self.assertEqual(results[-1].alpha, 4.0)
        self.assertAlmostEqual(results[0].successful_theory, 1.125)
        self.assertAlmostEqual(results[-1].unsuccessful_theory, 4.0)
        self.assertTrue(all(result.successful_measured > 0 for result in results))

    def test_writes_markdown_table_and_svg(self):
        results = build_results(capacity=20)
        table = render_table(results)
        svg = render_svg(results)

        self.assertIn("| α | 성공 실측 |", table)
        self.assertIn("| 4.00 |", table)
        self.assertIn("<svg ", svg)
        self.assertIn("<polyline ", svg)

        with tempfile.TemporaryDirectory() as temporary_directory:
            table_path, svg_path = write_outputs(results, temporary_directory)
            self.assertTrue(Path(table_path).is_file())
            self.assertTrue(Path(svg_path).is_file())


if __name__ == "__main__":
    unittest.main()
