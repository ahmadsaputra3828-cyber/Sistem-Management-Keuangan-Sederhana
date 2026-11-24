"""Halaman Anggaran (Budget): set anggaran per kategori & progress realisasi bulan berjalan."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import flet as ft

import db
from theme import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    PRIMARY,
    PRIMARY_DARK,
    PRIMARY_SOFT,
    format_rupiah,
)
from ui.components import card_container, empty_state, month_year_selector, page_header

# ---------------------------------------------------------------------------
# Warna & konstanta lokal
# ---------------------------------------------------------------------------
_COLOR_SAFE    = ft.Colors.GREEN_600
_COLOR_WARN    = ft.Colors.ORANGE_600
_COLOR_DANGER  = ft.Colors.RED_600
_COLOR_TRACK   = ft.Colors.GREY_200
_RADIUS_BAR    = ft.BorderRadius.all(8)


# ---------------------------------------------------------------------------
# Komponen: satu kartu progress anggaran
# ---------------------------------------------------------------------------

def _progress_card(r: dict, on_delete) -> ft.Container:
    """Kartu progress anggaran satu kategori."""
    budget_amt = Decimal(r["budget_amount"])
    spent_amt  = Decimal(r["spent_amount"])
    sisa_amt   = budget_amt - spent_amt
    ratio      = float(spent_amt / budget_amt) if budget_amt else 0
    over       = ratio > 1

    bar_color = (
        _COLOR_DANGER if over
        else _COLOR_WARN if ratio > 0.8
        else _COLOR_SAFE
    )

    # Label status di bawah progress bar
    if over:
        lebih = spent_amt - budget_amt
        status_label = ft.Text(
            f"⚠  Melebihi anggaran {format_rupiah(lebih)}",
            size=11,
            color=_COLOR_DANGER,
            weight=ft.FontWeight.W_600,
        )
    else:
        status_label = ft.Text(
            f"{ratio * 100:.0f}% terpakai  •  Sisa {format_rupiah(sisa_amt)}",
            size=11,
            color=bar_color,
        )

    return card_container(
        ft.Column(
            [
                # Baris atas: nama kategori + jumlah + tombol hapus
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    ft.Icon(ft.Icons.LABEL_OUTLINE, size=15, color=PRIMARY),
                                    margin=ft.Margin.only(right=6),
                                ),
                                ft.Text(
                                    r["category_name"],
                                    weight=ft.FontWeight.BOLD,
                                    size=14,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=1,
                                    expand=True,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    f"{format_rupiah(spent_amt)}",
                                    size=12,
                                    color=EXPENSE_COLOR,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(" / ", size=12, color=ft.Colors.GREY_500),
                                ft.Text(
                                    format_rupiah(budget_amt),
                                    size=12,
                                    color=ft.Colors.GREY_700,
                                ),
                                ft.Container(
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE,
                                        icon_size=16,
                                        icon_color=ft.Colors.RED_300,
                                        tooltip="Hapus anggaran ini",
                                        on_click=lambda e, bid=r["budget_id"]: on_delete(bid),
                                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                                    ),
                                    margin=ft.Margin.only(left=4),
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),

                # Progress bar
                ft.Container(
                    ft.ProgressBar(
                        value=min(ratio, 1.0),
                        color=bar_color,
                        bgcolor=_COLOR_TRACK,
                        border_radius=8,
                        height=8,
                    ),
                    margin=ft.Margin.symmetric(vertical=4),
                ),

                # Label status
                status_label,
            ],
            spacing=4,
        ),
        padding=16,
    )


# ---------------------------------------------------------------------------
# Komponen: ringkasan total anggaran bulan ini
# ---------------------------------------------------------------------------

def _summary_row(total_budget: Decimal, total_spent: Decimal) -> ft.Container:
    """Bar ringkasan total anggaran vs realisasi di bagian atas daftar."""
    sisa = total_budget - total_spent
    ratio = float(total_spent / total_budget) if total_budget else 0
    bar_color = (
        _COLOR_DANGER if ratio > 1
        else _COLOR_WARN if ratio > 0.8
        else _COLOR_SAFE
    )
    return ft.Container(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Total Anggaran", size=11, color=ft.Colors.GREY_600),
                        ft.Text(format_rupiah(total_budget), size=15,
                                weight=ft.FontWeight.BOLD, color=PRIMARY_DARK),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Column(
                    [
                        ft.Text("Total Terpakai", size=11, color=ft.Colors.GREY_600),
                        ft.Text(format_rupiah(total_spent), size=15,
                                weight=ft.FontWeight.BOLD, color=EXPENSE_COLOR),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Column(
                    [
                        ft.Text("Sisa", size=11, color=ft.Colors.GREY_600),
                        ft.Text(
                            format_rupiah(max(sisa, Decimal(0))),
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=_COLOR_SAFE if sisa >= 0 else _COLOR_DANGER,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        bgcolor=PRIMARY_SOFT,
        border_radius=10,
    )


# ---------------------------------------------------------------------------
# build() — entry point dipanggil dari main.py
# ---------------------------------------------------------------------------

def build(page: ft.Page, state: dict) -> ft.Column:
    """Bangun halaman Anggaran: form set anggaran + ringkasan + daftar progress per kategori."""

    # Widget utama
    summary_container = ft.Container()           # ringkasan total (diisi saat refresh)
    list_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # Form
    cat_dd = ft.Dropdown(
        label="Kategori Pengeluaran",
        expand=True,
        leading_icon=ft.Icons.CATEGORY_OUTLINED,
        border_color=ft.Colors.GREY_300,
        focused_border_color=PRIMARY,
    )
    amount_tf = ft.TextField(
        label="Jumlah Anggaran",
        hint_text="Contoh: 500000",
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icon(ft.Icons.PAYMENTS_OUTLINED),
        prefix=ft.Text("Rp "),
        border_color=ft.Colors.GREY_300,
        focused_border_color=PRIMARY,
    )
    error_txt = ft.Text("", color=_COLOR_DANGER, size=12)

    # -----------------------------------------------------------------------
    # Fungsi bantu
    # -----------------------------------------------------------------------

    def reload_cat_options():
        cats = db.get_categories("expense")
        cat_dd.options = [ft.dropdown.Option(str(c["id"]), c["name"]) for c in cats]
        cat_dd.value = cat_dd.options[0].key if cats else None
        page.update()

    def refresh_progress():
        rows = db.get_budget_progress(state["month"], state["year"])
        list_col.controls.clear()

        if not rows:
            summary_container.content = None
            list_col.controls.append(
                empty_state(
                    "Belum ada anggaran untuk bulan ini.\nKlik 'Set Anggaran' untuk mulai.",
                    icon=ft.Icons.PIE_CHART_OUTLINE,
                )
            )
            page.update()
            return

        # Hitung total untuk ringkasan
        total_budget = sum(Decimal(r["budget_amount"]) for r in rows)
        total_spent  = sum(Decimal(r["spent_amount"])  for r in rows)
        summary_container.content = _summary_row(total_budget, total_spent)

        for r in rows:
            list_col.controls.append(_progress_card(r, _do_delete_budget))
        page.update()

    def _do_delete_budget(budget_id: int):
        db.delete_budget(budget_id)
        refresh_progress()

    def _save_budget(_e):
        error_txt.value = ""
        if not cat_dd.value:
            error_txt.value = "⚠  Pilih kategori terlebih dahulu."
            page.update()
            return
        try:
            raw = (amount_tf.value or "").replace(",", ".").replace(" ", "")
            amount = Decimal(raw)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, AttributeError):
            error_txt.value = "⚠  Jumlah harus berupa angka lebih dari 0."
            page.update()
            return
        db.set_budget(int(cat_dd.value), state["month"], state["year"], amount)
        amount_tf.value = ""
        error_txt.value = ""
        refresh_progress()

    def _on_month_change():
        refresh_progress()
        page.update()

    # Muat data awal
    reload_cat_options()
    refresh_progress()

    # -----------------------------------------------------------------------
    # Form input
    # -----------------------------------------------------------------------
    form_row = ft.ResponsiveRow(
        [
            ft.Container(cat_dd,   col={"xs": 12, "sm": 5, "md": 5}),
            ft.Container(amount_tf, col={"xs": 12, "sm": 4, "md": 4}),
            ft.Container(
                ft.FilledButton(
                    "Set Anggaran",
                    icon=ft.Icons.SAVE_OUTLINED,
                    on_click=_save_budget,
                    width=float("inf"),
                    style=ft.ButtonStyle(
                        bgcolor=PRIMARY,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                col={"xs": 12, "sm": 3, "md": 3},
                alignment=ft.Alignment.CENTER,
            ),
        ],
        spacing=12,
        run_spacing=12,
    )

    form_card = card_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ADD_CHART, color=PRIMARY, size=18),
                        ft.Text("Tambah / Perbarui Anggaran",
                                weight=ft.FontWeight.W_600, size=13),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                form_row,
                error_txt,
            ],
            spacing=12,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
    )

    # -----------------------------------------------------------------------
    # Susun halaman
    # -----------------------------------------------------------------------
    return ft.Column(
        [
            page_header(
                "Anggaran Bulanan",
                selector=month_year_selector(state, _on_month_change),
            ),
            ft.Container(height=12),
            form_card,
            ft.Container(height=12),
            summary_container,
            ft.Container(height=8),
            list_col,
        ],
        expand=True,
    )
