"""Compare chaining and linear-probing costs across load factors."""

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from src.base62 import encode
from src.hash_table import HashTable, LinearProbingHashTable

DEFAULT_CAPACITY = 10000
CHAINING_CAPACITY = 4093
CHAINING_LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
REPORT_REPOSITORY_URL = "https://github.com/kimnaeun0227/algorithms-hw2"


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


@dataclass(frozen=True)
class ChainingProbeResult:
    target_alpha: float
    alpha: float
    item_count: int
    success_measured: float
    success_theory: float
    failure_measured: float
    failure_theory: float


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


def build_chaining_results(capacity=CHAINING_CAPACITY):
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 4:
        raise ValueError("capacity must be an integer of at least four")

    generator = random.Random(2026)
    urls = [
        f"https://{generator.getrandbits(64):016x}.example/item/{index}"
        for index in range(capacity * 4)
    ]
    missing_urls = [
        f"https://{generator.getrandbits(64):016x}.example/missing/{index}"
        for index in range(capacity)
    ]
    results = []

    for target_alpha in CHAINING_LOAD_FACTORS:
        item_count = round(capacity * target_alpha)
        keys = urls[:item_count]
        table = HashTable(capacity=capacity)
        for index, key in enumerate(keys):
            table.set(key, index)

        alpha = item_count / capacity
        success_measured = _average_probes(table, keys, expected_found=True)
        failure_measured = _average_probes(
            table, missing_urls, expected_found=False
        )
        results.append(
            ChainingProbeResult(
                target_alpha=target_alpha,
                alpha=alpha,
                item_count=item_count,
                success_measured=success_measured,
                success_theory=1 + alpha / 2,
                failure_measured=failure_measured,
                failure_theory=alpha,
            )
        )
    return results


def render_chaining_svg(results, capacity=CHAINING_CAPACITY):
    width, height = 1000, 700
    left, right = 95, 50
    plot_width = width - left - right
    panel_height = 210
    min_alpha, max_alpha = CHAINING_LOAD_FACTORS[0], CHAINING_LOAD_FACTORS[-1]
    panels = (
        (55, 3.5, "성공 탐색 평균 비교", "success_measured", "success_theory"),
        (365, 4.5, "실패 탐색 평균 비교", "failure_measured", "failure_theory"),
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        "<title id=\"title\">체이닝 탐색 비용: 실측과 이론</title>",
        f'<desc id="description">용량 {capacity}, 적재율 0.25부터 4까지의 '
        "성공·실패 비교 노드 수</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="28" font-size="13">버킷 수: {capacity}</text>',
    ]
    colors = {"measured": "#1f77b4", "theory": "#d62728"}

    for top, max_probes, title, measured_name, theory_name in panels:
        graph_top = top + 32
        graph_bottom = graph_top + panel_height

        def x_position(alpha):
            return left + (alpha - min_alpha) / (max_alpha - min_alpha) * plot_width

        def y_position(probes):
            return graph_bottom - probes / max_probes * panel_height

        parts.append(f'<text x="{left}" y="{top+18}" font-size="17">{title}</text>')
        tick_count = int(max_probes * 2)
        for tick in range(tick_count + 1):
            value = tick / 2
            y = y_position(value)
            parts.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
                'stroke="#dddddd"/>'
            )
            parts.append(
                f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
                f'font-size="11">{value:g}</text>'
            )

        for alpha in (0.25, 1, 2, 3, 4):
            x = x_position(alpha)
            parts.append(
                f'<line x1="{x:.1f}" y1="{graph_top}" x2="{x:.1f}" '
                f'y2="{graph_bottom}" stroke="#eeeeee"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{graph_bottom+18}" text-anchor="middle" '
                f'font-size="11">{alpha:g}</text>'
            )

        parts.extend(
            [
                f'<line x1="{left}" y1="{graph_bottom}" x2="{width-right}" '
                f'y2="{graph_bottom}" stroke="#333"/>',
                f'<line x1="{left}" y1="{graph_top}" x2="{left}" '
                f'y2="{graph_bottom}" stroke="#333"/>',
                f'<text x="{left+plot_width/2:.1f}" y="{graph_bottom+35}" '
                'text-anchor="middle" font-size="12">적재율 α</text>',
            ]
        )

        for attribute, kind, label, dashed in (
            (measured_name, "measured", "실측", False),
            (theory_name, "theory", "이론", True),
        ):
            points = " ".join(
                f"{x_position(result.alpha):.1f},"
                f"{y_position(getattr(result, attribute)):.1f}"
                for result in results
            )
            dash = ' stroke-dasharray="7 5"' if dashed else ""
            parts.append(
                f'<polyline points="{points}" fill="none" '
                f'stroke="{colors[kind]}" stroke-width="2.5"{dash}/>'
            )

        legend_y = graph_bottom + 58
        for index, (kind, label, dashed) in enumerate(
            (("measured", "실측", False), ("theory", "이론", True))
        ):
            x = left + index * 150
            dash = ' stroke-dasharray="7 5"' if dashed else ""
            parts.append(
                f'<line x1="{x}" y1="{legend_y}" x2="{x+25}" y2="{legend_y}" '
                f'stroke="{colors[kind]}" stroke-width="2.5"{dash}/>'
            )
            parts.append(
                f'<text x="{x+31}" y="{legend_y+4}" font-size="11">{label}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_chaining_outputs(results, output_dir, capacity=CHAINING_CAPACITY):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "results.csv"
    svg_path = output_dir / "results.svg"
    with csv_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "target_alpha",
                "alpha",
                "item_count",
                "capacity",
                "success_measured_nodes",
                "success_theory_nodes",
                "failure_measured_nodes",
                "failure_theory_nodes",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result.target_alpha:.2f}",
                    f"{result.alpha:.6f}",
                    result.item_count,
                    capacity,
                    f"{result.success_measured:.6f}",
                    f"{result.success_theory:.6f}",
                    f"{result.failure_measured:.6f}",
                    f"{result.failure_theory:.6f}",
                )
            )
    svg_path.write_text(
        render_chaining_svg(results, capacity), encoding="utf-8"
    )
    return csv_path, svg_path


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


def _pdf_text(x, y, size, text):
    encoded_text = text.encode("utf-16-be").hex().upper()
    return (
        f"BT /F1 {size} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm "
        f"<{encoded_text}> Tj ET\n"
    )


def _report_page_one(results, capacity):
    commands = [
        _pdf_text(42, 774, 8, REPORT_REPOSITORY_URL),
        _pdf_text(42, 751, 16, "해시 테이블 탐색 비용 비교"),
        _pdf_text(42, 733, 8, "개별 체이닝과 선형 탐지의 성공·실패 탐색을 적재율별로 비교했다."),
        _pdf_text(42, 713, 10, "구현 방식"),
        _pdf_text(42, 699, 8, "체이닝은 버킷별 연결 리스트에 (URL, 코드)를 저장해 충돌 항목을 같은 칸에 둔다."),
        _pdf_text(42, 687, 8, "선형 탐지는 충돌 시 다음 슬롯을 조사하고, 삭제 표식과 끝에서 0번으로의 순환을 유지한다."),
        _pdf_text(42, 675, 8, "두 방식은 Horner 해시 h=(31h+ord(c)) mod M을 사용해 URL↔코드 테이블을 구성한다."),
        _pdf_text(42, 655, 10, "실험 조건"),
        _pdf_text(42, 641, 8, f"용량 M={capacity:,}, 난수 시드 2026, 동일 키·부재 질의 집합, 적재율 alpha=0.1~0.9."),
        _pdf_text(42, 629, 8, "성공은 저장 키 전체를, 실패는 고정된 부재 키 집합을 조회했다. 값은 평균 방문 횟수다."),
        _pdf_text(42, 617, 8, "체이닝은 비교 노드, 선형 탐지는 방문 슬롯을 세며 실패 시 종료 빈 슬롯도 포함한다."),
        _pdf_text(42, 605, 8, "기대값: 체이닝 성공 1+alpha/2, 실패 alpha."),
        _pdf_text(42, 593, 8, "선형 근사: 성공 0.5*(1+1/(1-alpha)), 실패 0.5*(1+1/(1-alpha)^2)."),
        _pdf_text(42, 573, 10, "평균 방문 횟수 (실측 / 이론·근사)"),
        _pdf_text(42, 555, 7, "적재율"),
        _pdf_text(104, 555, 7, "체이닝 성공"),
        _pdf_text(210, 555, 7, "체이닝 실패"),
        _pdf_text(318, 555, 7, "선형 성공"),
        _pdf_text(426, 555, 7, "선형 실패"),
    ]
    y = 541
    for result in results:
        values = (
            (42, f"{result.alpha:.1f}"),
            (
                104,
                f"{result.chaining_success_measured:.3f}/{result.chaining_success_theory:.3f}",
            ),
            (
                210,
                f"{result.chaining_failure_measured:.3f}/{result.chaining_failure_theory:.3f}",
            ),
            (
                318,
                f"{result.linear_success_measured:.3f}/{result.linear_success_theory:.3f}",
            ),
            (
                426,
                f"{result.linear_failure_measured:.3f}/{result.linear_failure_theory:.3f}",
            ),
        )
        commands.extend(_pdf_text(x, y, 7, value) for x, value in values)
        y -= 12

    highest_load = results[-1]
    commands.extend(
        [
            _pdf_text(42, 423, 10, "결과 해석"),
            _pdf_text(42, 409, 8, "체이닝 실측은 alpha=0.1~0.9에서 성공 1.045→1.443회, 실패 0.101→0.913회로 완만히 늘었다."),
            _pdf_text(42, 397, 8, "선형 탐지는 충돌한 키들이 연속 슬롯을 차지하는 군집 때문에 빈 슬롯까지 긴 탐색이 필요하다."),
            _pdf_text(
                42,
                385,
                8,
                f"alpha=0.9의 실패 탐지는 {highest_load.linear_failure_measured:.3f}회로 "
                f"체이닝 {highest_load.chaining_failure_measured:.3f}회의 약 "
                f"{highest_load.linear_failure_measured / highest_load.chaining_failure_measured:.1f}배다.",
            ),
            _pdf_text(
                42,
                373,
                8,
                f"선형 실패 근사값 {highest_load.linear_failure_theory:.3f}회와의 차이는 "
                f"{highest_load.linear_failure_theory - highest_load.linear_failure_measured:.3f}회다.",
            ),
            _pdf_text(42, 361, 8, "근사식은 이상적 분포의 기대값이며, 실측은 고정 시드의 유한한 키 집합 하나에 대한 결과다."),
            _pdf_text(42, 341, 10, "에이전트 오류"),
            _pdf_text(42, 327, 8, "처음에는 웹 테이블 용량을 1024로 두어 빈 슬롯 1023개가 보였다. 사용자가 화면을 확인해 지적했다."),
            _pdf_text(42, 315, 8, "기본 서버를 8칸으로 줄이고 충돌 URL 3개를 넣은 뒤, 8행과 선형 탐지 경로 6→7→0을 테스트·HTTP로 확인했다."),
            _pdf_text(42, 293, 10, "느낀 점"),
            _pdf_text(42, 279, 8, "이번 실험에서 가장 인상 깊었던 점은 적재율 0.9에서 선형 탐지의 실패 탐색이 평균"),
            _pdf_text(42, 267, 8, "44.704회까지 늘어난 것이다. 같은 상황의 체이닝은 0.913회라서, 충돌 처리 방식이 조회"),
            _pdf_text(42, 255, 8, "비용을 크게 바꾼다는 것을 알 수 있었다. 웹 테이블에서 충돌 URL의 방문 슬롯을 확인하니"),
            _pdf_text(42, 243, 8, "군집이 생기는 과정이 더 잘 이해됐다. 다음에는 다른 키 집합에서도 실험해 결과가 얼마나"),
            _pdf_text(42, 231, 8, "달라지는지 확인해 보고 싶다."),
        ]
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
    commands.append(_pdf_text(left + 200, bottom - 30, 9, "적재율 alpha"))

    series = (
        (measured_names[0], (0.1, 0.35, 0.7), False, "체이닝 실측"),
        (theory_names[0], (0.1, 0.35, 0.7), True, "체이닝 이론"),
        (measured_names[1], (0.8, 0.15, 0.15), False, "선형 탐지 실측"),
        (theory_names[1], (0.8, 0.15, 0.15), True, "선형 탐지 근사"),
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
        _pdf_text(50, 760, 16, "적재율별 탐색 비용"),
        _pdf_text(50, 742, 9, "실선은 실측, 점선은 이론·근사값이다. 세로축은 평균 방문 횟수다."),
    ]
    _pdf_chart(
        commands,
        results,
        690,
        6.0,
        "성공 탐색",
        ("chaining_success_measured", "linear_success_measured"),
        ("chaining_success_theory", "linear_success_theory"),
    )
    _pdf_chart(
        commands,
        results,
        380,
        60.0,
        "실패 탐색",
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
        b"<< /Type /Font /Subtype /Type0 /BaseFont /HYGoThic-Medium "
        b"/Encoding /UniKS-UCS2-H /DescendantFonts [8 0 R] /ToUnicode 9 0 R >>",
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /HYGoThic-Medium "
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Korea1) /Supplement 1 >> "
        b"/FontDescriptor 10 0 R /DW 1000 >>",
        (
            b"<< /Length 345 >>\nstream\n"
            b"/CIDInit /ProcSet findresource begin\n"
            b"12 dict begin\n"
            b"begincmap\n"
            b"/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
            b"/CMapName /Adobe-Korea1-UCS def\n"
            b"/CMapType 2 def\n"
            b"1 begincodespacerange\n"
            b"<0000> <FFFF>\n"
            b"endcodespacerange\n"
            b"1 beginbfrange\n"
            b"<0000> <FFFF> <0000>\n"
            b"endbfrange\n"
            b"endcmap\n"
            b"CMapName currentdict /CMap defineresource pop\n"
            b"end\n"
            b"end\n"
            b"endstream"
        ),
        b"<< /Type /FontDescriptor /FontName /HYGoThic-Medium /Flags 4 "
        b"/FontBBox [-250 -350 1000 1000] /ItalicAngle 0 /Ascent 880 "
        b"/Descent -120 /CapHeight 700 /StemV 80 >>",
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
    chaining_results = build_chaining_results()
    csv_path, chaining_svg_path = write_chaining_outputs(
        chaining_results, Path(__file__).parent, CHAINING_CAPACITY
    )
    print(f"표 저장: {table_path}")
    print(f"그래프 저장: {svg_path}")
    print(f"보고서 저장: {pdf_path}")
    print(f"체이닝 실험 CSV 저장: {csv_path}")
    print(f"체이닝 실험 그래프 저장: {chaining_svg_path}")


if __name__ == "__main__":
    main()
