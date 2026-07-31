#!/usr/bin/env python3
"""Generate PDF export of retry-pay / change-pmi test cases."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_allure_csv import (  # noqa: E402
    EPIC,
    FEATURE,
    PRIORITY_MAP,
    STORY_BT,
    TEST_CASES,
)

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUTPUT_NAME = "retry-pay-change-pmi-test-cases.pdf"


class TestCasesPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font("DejaVu", "", FONT_REGULAR)
        self.add_font("DejaVu", "B", FONT_BOLD)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Стр. {self.page_no()}/{{nb}}", align="C")

    def section_title(self, text: str) -> None:
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 8, text)
        self.ln(2)

    def label_value(self, label: str, value: str) -> None:
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(60, 60, 60)
        self.cell(32, 5, label + ":", ln=0)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 5, value)
        self.ln(1)

    def draw_test_case(self, index: int, tc) -> None:
        if self.get_y() > 250:
            self.add_page()

        self.set_fill_color(240, 244, 248)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(15, 76, 129)
        title = f"{index}. [{tc.external_id}] {tc.name}"
        self.multi_cell(0, 7, title, fill=True)
        self.ln(2)

        self.label_value("Приоритет", f"{tc.priority} ({PRIORITY_MAP[tc.priority]})")
        self.label_value("Слой", tc.layer)
        self.label_value("Теги", ", ".join(tc.tags))
        self.label_value("Предусловия", tc.precondition)

        self.ln(1)
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(60, 60, 60)
        self.cell(0, 5, "Шаги:", ln=1)

        col_w = [10, 88, 88]
        self.set_fill_color(220, 228, 236)
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(20, 20, 20)
        self.cell(col_w[0], 6, "№", border=1, fill=True, align="C")
        self.cell(col_w[1], 6, "Действие", border=1, fill=True, align="C")
        self.cell(col_w[2], 6, "Ожидаемый результат", border=1, fill=True, align="C", ln=1)

        self.set_font("DejaVu", "", 8)
        for step_idx, (action, expected) in enumerate(tc.steps, start=1):
            y_start = self.get_y()
            x_start = self.get_x()

            self.cell(col_w[0], 6, str(step_idx), border="LTR", align="C")
            x_action = self.get_x()
            y_action = self.get_y()
            self.multi_cell(col_w[1], 5, action, border="LTR")
            h_action = self.get_y() - y_action

            self.set_xy(x_action + col_w[1], y_action)
            self.multi_cell(col_w[2], 5, expected, border="LTR")
            h_expected = self.get_y() - y_action

            row_h = max(h_action, h_expected, 6)
            self.rect(x_start, y_start, sum(col_w), row_h)
            self.line(x_start + col_w[0], y_start, x_start + col_w[0], y_start + row_h)
            self.line(x_start + col_w[0] + col_w[1], y_start, x_start + col_w[0] + col_w[1], y_start + row_h)
            self.set_xy(x_start, y_start + row_h)

        self.ln(4)


def build_pdf() -> FPDF:
    pdf = TestCasesPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(15, 76, 129)
    pdf.multi_cell(0, 10, "Тест-кейсы: смена способа оплаты\nпри недостатке средств")
    pdf.ln(2)

    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(
        0,
        6,
        f"Бизнес-требование: {STORY_BT}\n"
        f"Epic: {EPIC}\n"
        f"Feature: {FEATURE}\n"
        f"Дата выгрузки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"Всего тест-кейсов: {len(TEST_CASES)}",
    )
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 7, "Сводка по приоритетам", ln=1)
    pdf.set_font("DejaVu", "", 9)
    for prio in ("P1", "P2", "P3", "P4"):
        count = sum(1 for tc in TEST_CASES if tc.priority == prio)
        pdf.cell(0, 5, f"  {prio} ({PRIORITY_MAP[prio]}): {count} кейсов", ln=1)
    pdf.ln(2)

    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, "Сводка по слоям", ln=1)
    pdf.set_font("DejaVu", "", 9)
    layers: dict[str, int] = {}
    for tc in TEST_CASES:
        layers[tc.layer] = layers.get(tc.layer, 0) + 1
    for layer, count in sorted(layers.items()):
        pdf.cell(0, 5, f"  {layer}: {count} кейсов", ln=1)

    pdf.add_page()
    pdf.section_title("Тест-кейсы (по убыванию важности)")

    for index, tc in enumerate(TEST_CASES, start=1):
        pdf.draw_test_case(index, tc)

    return pdf


def main() -> Path:
    pdf = build_pdf()
    workspace_out = SCRIPT_DIR / OUTPUT_NAME
    artifacts_dir = Path("/opt/cursor/artifacts")
    artifacts_out = artifacts_dir / OUTPUT_NAME

    pdf.output(str(workspace_out))
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    pdf.output(str(artifacts_out))

    print(f"PDF saved to: {workspace_out}")
    print(f"PDF saved to: {artifacts_out}")
    return artifacts_out


if __name__ == "__main__":
    main()
