import tempfile
import unittest
from pathlib import Path

from experiments.probe_experiment import build_results, render_svg, render_table, write_outputs


class ProbeExperimentTests(unittest.TestCase):
    def test_compares_both_tables_at_load_factors_point_one_to_point_nine(self):
        results = build_results(capacity=40)

        self.assertEqual(len(results), 9)
        self.assertEqual(results[0].alpha, 0.1)
        self.assertEqual(results[-1].alpha, 0.9)
        self.assertAlmostEqual(results[0].chaining_success_theory, 1.05)
        self.assertAlmostEqual(results[-1].chaining_failure_theory, 0.9)
        self.assertAlmostEqual(results[-1].linear_success_theory, 5.5)
        self.assertAlmostEqual(results[-1].linear_failure_theory, 50.5)
        self.assertTrue(
            all(
                result.linear_success_measured > 0
                and result.chaining_success_measured > 0
                for result in results
            )
        )

    def test_writes_table_svg_and_two_page_pdf(self):
        results = build_results(capacity=20)
        table = render_table(results)
        svg = render_svg(results)

        self.assertIn("| α | 체이닝 성공 실측 |", table)
        self.assertIn("| 0.9 |", table)
        self.assertIn("<svg ", svg)
        self.assertEqual(svg.count("<polyline "), 8)

        with tempfile.TemporaryDirectory() as temporary_directory:
            table_path, svg_path, pdf_path = write_outputs(
                results, temporary_directory, capacity=20
            )
            self.assertTrue(Path(table_path).is_file())
            self.assertTrue(Path(svg_path).is_file())
            pdf = Path(pdf_path).read_bytes()
            self.assertTrue(pdf.startswith(b"%PDF-1.4"))
            self.assertIn(b"/Count 2", pdf)
            self.assertEqual(pdf.count(b"/Type /Page "), 2)


if __name__ == "__main__":
    unittest.main()
