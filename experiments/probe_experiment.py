"""Measure separate-chaining probe counts across several load factors."""

import random
from dataclasses import dataclass
from pathlib import Path

from src.hash_table import HashTable


@dataclass(frozen=True)
class ProbeResult:
    alpha: float
    successful_measured: float
    successful_theory: float
    unsuccessful_measured: float
    unsuccessful_theory: float


def build_results(capacity=100):
    if (
        not isinstance(capacity, int)
        or isinstance(capacity, bool)
        or capacity < 4
        or capacity % 4
    ):
        raise ValueError("capacity must be a positive multiple of four")

    generator = random.Random(2026)
    all_keys = [
        f"key-{value:08x}" for value in generator.sample(range(1 << 32), capacity * 4)
    ]
    missing_keys = [
        f"absent-{value:08x}" for value in generator.sample(range(1 << 32), capacity)
    ]
    results = []
    for step in range(1, 17):
        item_count = step * (capacity // 4)
        keys = all_keys[:item_count]
        table = HashTable(capacity)
        for index, key in enumerate(keys):
            table.set(key, index)

        successful_probes = 0
        for key in keys:
            found, _, probes = table.search(key)
            if not found:
                raise RuntimeError(f"inserted key was not found: {key}")
            successful_probes += probes

        unsuccessful_probes = 0
        for key in missing_keys:
            found, _, probes = table.search(key)
            if found:
                raise RuntimeError("an absent key unexpectedly matched")
            unsuccessful_probes += probes

        alpha = item_count / capacity
        results.append(
            ProbeResult(
                alpha=alpha,
                successful_measured=successful_probes / item_count,
                successful_theory=1 + alpha / 2,
                unsuccessful_measured=unsuccessful_probes / capacity,
                unsuccessful_theory=alpha,
            )
        )
    return results


def render_table(results):
    lines = [
        "| α | 성공 실측 | 성공 이론 (1 + α/2) | 실패 실측 | 실패 이론 (α) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.alpha:.2f} | {result.successful_measured:.3f} "
            f"| {result.successful_theory:.3f} | {result.unsuccessful_measured:.3f} "
            f"| {result.unsuccessful_theory:.3f} |"
        )
    return "\n".join(lines) + "\n"


def render_svg(results):
    width, height = 900, 560
    left, top, right, bottom = 78, 55, 35, 88
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_alpha, max_probes = 4.0, 5.0

    def x_position(alpha):
        return left + alpha / max_alpha * plot_width

    def y_position(probes):
        return top + (max_probes - probes) / max_probes * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        'viewBox="0 0 900 560" role="img" aria-labelledby="title description">',
        "<title id=\"title\">체이닝 해시 테이블 적재율별 탐색 비용</title>",
        '<desc id="description">성공 및 실패 탐색의 실측 비교 횟수와 이론값</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="28" text-anchor="middle" font-size="18">'
        "체이닝 해시 테이블 탐색 비용</text>",
    ]

    for tick in range(0, 6):
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
            'stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" '
            f'font-size="12">{tick}</text>'
        )
    for tick in range(0, 9):
        alpha = tick / 2
        x = x_position(alpha)
        parts.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" '
            'stroke="#eeeeee"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" '
            f'font-size="12">{alpha:.1f}</text>'
        )

    parts.extend(
        [
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" '
            f'y2="{height-bottom}" stroke="#333"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" '
            'stroke="#333"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-18}" '
            'text-anchor="middle" font-size="14">적재율 α</text>',
            f'<text x="20" y="{top + plot_height/2:.1f}" '
            'transform="rotate(-90 20 250)" text-anchor="middle" font-size="14">'
            "평균 비교 노드 수</text>",
        ]
    )

    series = (
        ("successful_measured", "#1f77b4", "성공 실측"),
        ("successful_theory", "#1f77b4", "성공 이론"),
        ("unsuccessful_measured", "#d62728", "실패 실측"),
        ("unsuccessful_theory", "#d62728", "실패 이론"),
    )
    for attribute, color, label in series:
        points = " ".join(
            f"{x_position(result.alpha):.1f},{y_position(getattr(result, attribute)):.1f}"
            for result in results
        )
        dash = ' stroke-dasharray="7 5"' if label.endswith("이론") else ""
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2.5"{dash}/>'
        )

    for index, (attribute, color, label) in enumerate(series):
        x, y = left + index * 190, height - 48
        dash = ' stroke-dasharray="7 5"' if label.endswith("이론") else ""
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x+28}" y2="{y}" stroke="{color}" '
            f'stroke-width="2.5"{dash}/>'
        )
        parts.append(
            f'<text x="{x+34}" y="{y+4}" font-size="12">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_outputs(results, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "probe_results.md"
    svg_path = output_dir / "probe_results.svg"
    table_path.write_text(
        "# 체이닝 탐색 비용 실험\n\n"
        "성공 탐색은 저장된 모든 키를, 실패 탐색은 용량만큼의 없는 키를 조회해 "
        "평균 비교 노드 수를 측정했다. 이론식은 균등 분포 가정의 "
        "`성공: 1 + α/2`, `실패: α`다.\n\n"
        + render_table(results),
        encoding="utf-8",
    )
    svg_path.write_text(render_svg(results), encoding="utf-8")
    return table_path, svg_path


def main():
    results = build_results()
    print(render_table(results), end="")
    table_path, svg_path = write_outputs(results, Path(__file__).parent)
    print(f"표 저장: {table_path}")
    print(f"그래프 저장: {svg_path}")


if __name__ == "__main__":
    main()
