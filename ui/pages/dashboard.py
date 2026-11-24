"""Halaman Dashboard: ringkasan pemasukan/pengeluaran bulan berjalan + breakdown per kategori."""

from __future__ import annotations

from decimal import Decimal

import flet as ft

import db
from theme import EXPENSE_COLOR, INCOME_COLOR, PRIMARY, PRIMARY_SOFT, format_rupiah
from ui.components import card_container, empty_state, month_year_selector, page_header


def _summary_card(title: str, value, color: str, icon: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 4},
        content=card_container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(icon, color=color, size=20),
                                bgcolor=ft.Colors.with_opacity(0.12, color),
                                border_radius=10,
                                padding=8,
                            ),
                            ft.Text(title, size=13, color=ft.Colors.GREY_700),
                        ],
                        spacing=10,
                    ),
                    ft.Text(format_rupiah(value), size=22, weight=ft.FontWeight.BOLD, color=color),
                ],
                spacing=10,
            ),
        ),
    )


def _category_breakdown_rows(month: int, year: int) -> list[ft.Control]:
    """Baris progress bar pengeluaran per kategori, hanya kategori yang punya nominal > 0."""
    by_cat = [c for c in db.get_expense_by_category(month, year) if Decimal(c["total_spent"]) > 0]
    if not by_cat:
        return [empty_state("Belum ada pengeluaran bulan ini.")]

    max_spent = max((Decimal(c["total_spent"]) for c in by_cat), default=Decimal(1)) or Decimal(1)

    rows: list[ft.Control] = []
    for c in by_cat:
        spent = Decimal(c["total_spent"])
        ratio = float(spent / max_spent) if max_spent else 0
        rows.append(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(c["category_name"], size=13, expand=True,
                                     overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(format_rupiah(spent), size=13, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.ProgressBar(value=ratio, color=PRIMARY, bgcolor=PRIMARY_SOFT, border_radius=6),
                ],
                spacing=4,
            )
        )
    return rows


def build(page: ft.Page, state: dict, content_area: ft.Container) -> ft.Column:
    """Bangun halaman Dashboard. Dipanggil ulang setiap kali bulan/tahun berganti."""
    summary = db.get_summary(state["month"], state["year"])
    income = Decimal(summary["total_income"])
    expense = Decimal(summary["total_expense"])
    balance = income - expense

    cards = ft.ResponsiveRow(
        [
            _summary_card("Pemasukan", income, INCOME_COLOR, ft.Icons.ARROW_DOWNWARD),
            _summary_card("Pengeluaran", expense, EXPENSE_COLOR, ft.Icons.ARROW_UPWARD),
            _summary_card(
                "Saldo Bersih", balance,
                PRIMARY if balance >= 0 else EXPENSE_COLOR,
                ft.Icons.ACCOUNT_BALANCE_WALLET,
            ),
        ],
        spacing=16,
        run_spacing=16,
    )

    def refresh():
        content_area.content = build(page, state, content_area)
        page.update()

    return ft.Column(
        [
            page_header("Dashboard", selector=month_year_selector(state, refresh)),
            ft.Container(height=16),
            cards,
            ft.Container(height=20),
            ft.Text("Pengeluaran per Kategori", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=4),
            card_container(ft.Column(_category_breakdown_rows(state["month"], state["year"]), spacing=14)),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
