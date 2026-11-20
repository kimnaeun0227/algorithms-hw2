import tempfile
import unittest
from pathlib import Path

from experiments.probe_experiment import (
    build_chaining_results,
    build_results,
    render_svg,
    render_table,
    write_chaining_outputs,
    write_outputs,
)


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
            repository_url = "https://github.com/kimnaeun0227/algorithms-hw2"
            repository_url_hex = repository_url.encode("utf-16-be").hex().upper().encode(
                "ascii"
            )
            title_hex = "해시 테이블 탐색 비용 비교".encode("utf-16-be").hex().upper().encode(
                "ascii"
            )
            self.assertLess(pdf.index(repository_url_hex), pdf.index(title_hex))
            self.assertIn("에이전트 오류".encode("utf-16-be").hex().upper().encode("ascii"), pdf)

    def test_chaining_experiment_covers_requested_loads_and_writes_csv_svg(self):
        results = build_chaining_results(capacity=40)

        self.assertEqual(
            [result.target_alpha for result in results],
            [step / 4 for step in range(1, 17)],
        )
        self.assertEqual(results[0].item_count, 10)
        self.assertEqual(results[-1].item_count, 160)
        self.assertTrue(all(result.success_measured >= 1 for result in results))
        for result in results:
            self.assertAlmostEqual(result.success_theory, 1 + result.alpha / 2)
            self.assertAlmostEqual(result.failure_theory, result.alpha)

        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path, svg_path = write_chaining_outputs(
                results, temporary_directory, capacity=40
            )
            csv_lines = Path(csv_path).read_text(encoding="utf-8").splitlines()
            svg = Path(svg_path).read_text(encoding="utf-8")

        self.assertEqual(Path(csv_path).name, "results.csv")
        self.assertEqual(len(csv_lines), 17)
        self.assertIn("target_alpha,alpha,item_count", csv_lines[0])
        self.assertTrue(svg.startswith("<svg "))
        self.assertEqual(svg.count("<polyline "), 4)


if __name__ == "__main__":
    unittest.main()
