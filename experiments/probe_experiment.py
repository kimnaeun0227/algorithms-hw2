"""Compare chaining and linear-probing costs across load factors."""

import random
from dataclasses import dataclass
from pathlib import Path

from src.base62 import encode
from src.hash_table import HashTable, LinearProbingHashTable

DEFAULT_CAPACITY = 10000


@dataclass(frozen=True)
class ProbeResult:
    alpha: float
    chaining_success_measured: float
    chaining_success_theory: float
    chaining_failure_measured: float
    chaining_failure_theory: float
    linear_success_measured: float
    linear_success_theory: float
    linear_failure_measured: float
    linear_failure_theory: float


def build_results(capacity=DEFAULT_CAPACITY):
    if (
        not isinstance(capacity, int)
        or isinstance(capacity, bool)
        or capacity < 10
        or capacity % 10
    ):
        raise ValueError("capacity must be a positive multiple of ten")

    generator = random.Random(2026)
    all_keys = [
        encode(value).rjust(8, "0")
        for value in generator.sample(range(62**8), capacity * 9 // 10)
    ]
    missing_keys = [
        f"m{encode(value).rjust(8, '0')}"
        for value in generator.sample(range(62**8), capacity)
    ]
    results = []

    for step in range(1, 10):
        item_count = step * (capacity // 10)
        keys = all_keys[:item_count]
        chaining = HashTable(capacity)
        linear = LinearProbingHashTable(capacity)
        for index, key in enumerate(keys):
            chaining.set(key, index)
            linear.set(key, index)

        chaining_success = _average_probes(chaining, keys, expected_found=True)
        chaining_failure = _average_probes(
            chaining, missing_keys, expected_found=False
        )
        linear_success = _average_probes(linear, keys, expected_found=True)
        linear_failure = _average_probes(linear, missing_keys, expected_found=False)
        alpha = item_count / capacity
        results.append(
            ProbeResult(
                alpha=alpha,
                chaining_success_measured=chaining_success,
                chaining_success_theory=1 + alpha / 2,
                chaining_failure_measured=chaining_failure,
                chaining_failure_theory=alpha,
                linear_success_measured=linear_success,
                linear_success_theory=0.5 * (1 + 1 / (1 - alpha)),
                linear_failure_measured=linear_failure,
                linear_failure_theory=0.5 * (1 + 1 / (1 - alpha) ** 2),
            )
        )
    return results


def _average_probes(table, keys, expected_found):
    total = 0
    for key in keys:
        found, _, probes = table.search(key)
        if found is not expected_found:
            raise RuntimeError(f"unexpected lookup result for {key!r}")
        total += probes
    return total / len(keys)


def render_table(results):
    lines = [
        "| α | 체이닝 성공 실측 | 이론 | 체이닝 실패 실측 | 이론 "
        "| 선형 성공 실측 | 근사 이론 | 선형 실패 실측 | 근사 이론 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.alpha:.1f} | {result.chaining_success_measured:.3f} "
            f"| {result.chaining_success_theory:.3f} "
            f"| {result.chaining_failure_measured:.3f} "
            f"| {result.chaining_failure_theory:.3f} "
            f"| {result.linear_success_measured:.3f} "
            f"| {result.linear_success_theory:.3f} "
            f"| {result.linear_failure_measured:.3f} "
            f"| {result.linear_failure_theory:.3f} |"
        )
    return "\n".join(lines) + "\n"


def render_svg(results):
    width, height = 1000, 820
    left, right = 90, 45
    plot_width = width - left - right
    panel_height = 260
    max_alpha = 0.9
    panels = (
        (
            60,
            6.0,
            "성공 탐색 (평균 슬롯/노드 방문 수)",
            "chaining_success_measured",
            "chaining_success_theory",
            "linear_success_measured",
            "linear_success_theory",
        ),
        (
            430,
            60.0,
            "실패 탐색 (평균 슬롯/노드 방문 수)",
            "chaining_failure_measured",
            "chaining_failure_theory",
            "linear_failure_measured",
            "linear_failure_theory",
        ),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        "<title id=\"title\">체이닝과 선형 탐지 비교</title>",
        '<desc id="description">적재율별 성공 및 실패 탐색의 실측값과 이론값</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    colors = ("#1f77b4", "#d62728")

    for panel_index, panel in enumerate(panels):
        top, max_probes, title, *attributes = panel
        graph_top = top + 36
        graph_bottom = graph_top + panel_height

        def x_position(alpha):
            return left + (alpha - 0.1) / (max_alpha - 0.1) * plot_width

        def y_position(probes):
            return graph_bottom - probes / max_probes * panel_height

        parts.append(
            f'<text x="{left}" y="{top+18}" font-size="17">{title}</text>'
        )
        tick_count = 6
        for tick in range(tick_count + 1):
            value = max_probes * tick / tick_count
            y = y_position(value)
            parts.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
                'stroke="#dddddd"/>'
            )
            parts.append(
                f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
                f'font-size="11">{value:g}</text>'
            )
        for tick in range(1, 10):
            alpha = tick / 10
            x = x_position(alpha)
            parts.append(
                f'<line x1="{x:.1f}" y1="{graph_top}" x2="{x:.1f}" '
                f'y2="{graph_bottom}" stroke="#eeeeee"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{graph_bottom+18}" text-anchor="middle" '
                f'font-size="11">{alpha:.1f}</text>'
            )
        parts.extend(
            [
                f'<line x1="{left}" y1="{graph_bottom}" x2="{width-right}" '
                f'y2="{graph_bottom}" stroke="#333"/>',
                f'<line x1="{left}" y1="{graph_top}" x2="{left}" '
                f'y2="{graph_bottom}" stroke="#333"/>',
                f'<text x="{left+plot_width/2:.1f}" y="{graph_bottom+34}" '
                'text-anchor="middle" font-size="12">적재율 α</text>',
            ]
        )

        series = (
            (attributes[0], colors[0], "체이닝 실측", False),
            (attributes[1], colors[0], "체이닝 이론", True),
            (attributes[2], colors[1], "선형 실측", False),
            (attributes[3], colors[1], "선형 근사", True),
        )
        for attribute, color, label, theoretical in series:
            points = " ".join(
                f"{x_position(result.alpha):.1f},"
                f"{y_position(getattr(result, attribute)):.1f}"
                for result in results
            )
            dash = ' stroke-dasharray="7 5"' if theoretical else ""
            parts.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" '
                f'stroke-width="2.5"{dash}/>'
            )
        legend_y = graph_bottom + 58
        for index, (_, color, label, theoretical) in enumerate(series):
            x = left + index * 205
            dash = ' stroke-dasharray="7 5"' if theoretical else ""
            parts.append(
                f'<line x1="{x}" y1="{legend_y}" x2="{x+25}" y2="{legend_y}" '
                f'stroke="{color}" stroke-width="2.5"{dash}/>'
            )
            parts.append(
                f'<text x="{x+31}" y="{legend_y+4}" font-size="11">{label}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text(x, y, size, text):
    ascii_text = text.encode("ascii", "replace").decode("ascii")
    return (
        f"BT /F1 {size} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm "
        f"({_pdf_escape(ascii_text)}) Tj ET\n"
    )


def _report_page_one(results, capacity):
    commands = []
    commands.append(_pdf_text(50, 748, 18, "Hash Table Probe Cost Comparison"))
    commands.append(
        _pdf_text(
            50,
            720,
            10,
            f"Method: same seeded keys, capacity {capacity}, load factors 0.1 through 0.9.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            703,
            9,
            "Chaining: success 1+alpha/2; failure alpha. Linear formulas are approximations.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            686,
            9,
            "Linear: success 0.5*(1+1/(1-alpha)); failure 0.5*(1+1/(1-alpha)^2).",
        )
    )
    commands.append(_pdf_text(50, 650, 11, "Measured probes and theoretical estimates"))
    commands.append(
        _pdf_text(
            50,
            630,
            8,
            "alpha | chain success M/T | chain fail M/T | linear success M/T | linear fail M/T",
        )
    )
    y = 614
    for result in results:
        row = (
            f"{result.alpha:.1f} | "
            f"{result.chaining_success_measured:.2f}/{result.chaining_success_theory:.2f} | "
            f"{result.chaining_failure_measured:.2f}/{result.chaining_failure_theory:.2f} | "
            f"{result.linear_success_measured:.2f}/{result.linear_success_theory:.2f} | "
            f"{result.linear_failure_measured:.2f}/{result.linear_failure_theory:.2f}"
        )
        commands.append(_pdf_text(50, y, 8, row))
        y -= 13

    highest_load = results[-1]
    commands.append(_pdf_text(50, 475, 11, "Interpretation"))
    commands.append(
        _pdf_text(
            50,
            457,
            9,
            "Chaining grows gradually with alpha; its measurements stay near the uniform-hashing model.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            440,
            9,
            "Linear probing rises faster as primary clustering creates long runs of occupied slots.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            423,
            9,
            f"At alpha 0.9, linear failure measured {highest_load.linear_failure_measured:.2f} "
            f"versus approximate 50.50 probes.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            406,
            9,
            "Finite deterministic keys and the approximate model explain residual differences.",
        )
    )
    commands.append(
        _pdf_text(
            50,
            389,
            9,
            "A linear-table probe counts each inspected slot, including the terminating empty slot.",
        )
    )
    return "".join(commands).encode("ascii")


def _pdf_chart(commands, results, top, max_probes, title, measured_names, theory_names):
    left, width, height = 72, 475, 205
    bottom = top - height
    commands.append(_pdf_text(left, top + 20, 12, title))

    for tick in range(5):
        value = max_probes * tick / 4
        y = bottom + value / max_probes * height
        commands.append("0.82 G 0.5 w\n")
        commands.append(f"{left} {y:.1f} m {left+width} {y:.1f} l S\n")
        commands.append("0 G\n")
        commands.append(_pdf_text(left - 30, y - 3, 8, f"{value:g}"))
    for tick in range(1, 10):
        alpha = tick / 10
        x = left + (alpha - 0.1) / 0.8 * width
        commands.append(_pdf_text(x - 7, bottom - 15, 8, f"{alpha:.1f}"))
    commands.append(f"0 G 1 w {left} {bottom} m {left+width} {bottom} l S\n")
    commands.append(f"0 G 1 w {left} {bottom} m {left} {top} l S\n")
    commands.append(_pdf_text(left + 200, bottom - 30, 9, "Load factor alpha"))

    series = (
        (measured_names[0], (0.1, 0.35, 0.7), False, "Chaining measured"),
        (theory_names[0], (0.1, 0.35, 0.7), True, "Chaining theory"),
        (measured_names[1], (0.8, 0.15, 0.15), False, "Linear measured"),
        (theory_names[1], (0.8, 0.15, 0.15), True, "Linear theory"),
    )
    for attribute, color, dashed, _ in series:
        commands.append(f"{color[0]} {color[1]} {color[2]} RG 1.5 w\n")
        commands.append("[4 3] 0 d\n" if dashed else "[] 0 d\n")
        for index, result in enumerate(results):
            x = left + (result.alpha - 0.1) / 0.8 * width
            y = bottom + getattr(result, attribute) / max_probes * height
            commands.append(f"{x:.1f} {y:.1f} {'m' if index == 0 else 'l'}\n")
        commands.append("S [] 0 d\n")

    legend_y = bottom - 48
    legend_positions = (left, left + 245, left, left + 245)
    legend_rows = (legend_y, legend_y, legend_y - 15, legend_y - 15)
    for index, (_, color, dashed, label) in enumerate(series):
        x, y = legend_positions[index], legend_rows[index]
        commands.append(f"{color[0]} {color[1]} {color[2]} RG 1.5 w\n")
        commands.append("[4 3] 0 d\n" if dashed else "[] 0 d\n")
        commands.append(f"{x} {y} m {x+22} {y} l S [] 0 d\n")
        commands.append(_pdf_text(x + 28, y - 3, 8, label))


def _report_page_two(results):
    commands = [
        _pdf_text(50, 760, 16, "Probe Cost Curves"),
        _pdf_text(50, 742, 9, "Solid lines are measurements; dashed lines are theoretical estimates."),
    ]
    _pdf_chart(
        commands,
        results,
        690,
        6.0,
        "Successful search",
        ("chaining_success_measured", "linear_success_measured"),
        ("chaining_success_theory", "linear_success_theory"),
    )
    _pdf_chart(
        commands,
        results,
        380,
        60.0,
        "Unsuccessful search",
        ("chaining_failure_measured", "linear_failure_measured"),
        ("chaining_failure_theory", "linear_failure_theory"),
    )
    return "".join(commands).encode("ascii")


def render_pdf_report(results, capacity=DEFAULT_CAPACITY):
    pages = (
        _report_page_one(results, capacity),
        _report_page_two(results),
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R >> >> /Contents 4 0 R >>",
        None,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 7 0 R >> >> /Contents 6 0 R >>",
        None,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for index, page in enumerate(pages):
        object_number = 4 if index == 0 else 6
        objects[object_number - 1] = (
            f"<< /Length {len(page)} >>\nstream\n".encode("ascii")
            + page
            + b"endstream"
        )

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, content in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(content)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def write_outputs(results, output_dir, capacity=DEFAULT_CAPACITY):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "probe_results.md"
    svg_path = output_dir / "probe_results.svg"
    pdf_path = output_dir / "linear_probe_report.pdf"
    table_path.write_text(
        "# 해시 테이블 탐색 비용 비교\n\n"
        f"용량 {capacity}, 동일한 결정적 키·질의 집합으로 각 적재율에서 측정했다. "
        "체이닝 이론값은 성공 `1 + α/2`, 실패 `α`; 선형 탐지 근사값은 성공 "
        "`½(1 + 1/(1-α))`, 실패 `½(1 + 1/(1-α)^2)`이다. 선형 탐지의 실패 "
        "측정은 종료 빈 슬롯도 방문 횟수에 포함한다.\n\n"
        + render_table(results),
        encoding="utf-8",
    )
    svg_path.write_text(render_svg(results), encoding="utf-8")
    pdf_path.write_bytes(render_pdf_report(results, capacity))
    return table_path, svg_path, pdf_path


def main():
    results = build_results()
    print(render_table(results), end="")
    table_path, svg_path, pdf_path = write_outputs(
        results, Path(__file__).parent, DEFAULT_CAPACITY
    )
    print(f"표 저장: {table_path}")
    print(f"그래프 저장: {svg_path}")
    print(f"보고서 저장: {pdf_path}")


if __name__ == "__main__":
    main()
