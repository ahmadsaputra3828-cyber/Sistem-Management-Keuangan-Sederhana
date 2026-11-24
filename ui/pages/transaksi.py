"""Halaman Transaksi: daftar transaksi bulan berjalan + form tambah/edit/hapus."""

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation

import flet as ft

import db
from theme import CARD_SHADOW, EXPENSE_COLOR, INCOME_COLOR, format_rupiah
from ui.components import TODAY, empty_state, month_year_selector, page_header

ERROR_COLOR = ft.Colors.RED_600


def _dialog_width(page: ft.Page) -> float:
    """Lebar dialog menyesuaikan lebar layar, dengan batas atas 380px."""
    w = (page.width or 1200) - 48
    return max(260.0, min(380.0, w))


def _transaction_row(r: dict, on_edit, on_delete) -> ft.Container:
    is_income = r["type"] == "income"
    color = INCOME_COLOR if is_income else EXPENSE_COLOR
    sign = "+" if is_income else "-"
    subtitle = str(r["transaction_date"])
    if r["description"]:
        subtitle += f' • {r["description"]}'

    return ft.Container(
        padding=ft.Padding.symmetric(vertical=10, horizontal=16),
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.ARROW_DOWNWARD if is_income else ft.Icons.ARROW_UPWARD,
                        color=color, size=16,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                    border_radius=8,
                    padding=8,
                ),
                ft.Column(
                    [
                        ft.Text(r["category_name"], size=14, weight=ft.FontWeight.W_500,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600,
                                overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Text(f"{sign} {format_rupiah(r['amount'])}", color=color,
                        weight=ft.FontWeight.BOLD, size=13),
                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, on_click=lambda e: on_edit(r)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=ft.Colors.RED_400,
                              on_click=lambda e: on_delete(r)),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )


def build(page: ft.Page, state: dict) -> ft.Column:
    """Bangun halaman Transaksi (daftar + dialog form, dikelola lewat closure)."""
    trx_list_view = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # ---- Form tambah/edit transaksi ----
    type_rg = ft.RadioGroup(
        content=ft.Row(
            [ft.Radio(value="expense", label="Pengeluaran"), ft.Radio(value="income", label="Pemasukan")],
            wrap=True,
        ),
        value="expense",
    )
    category_dd = ft.Dropdown(label="Kategori", expand=True)
    amount_tf = ft.TextField(label="Jumlah (Rp)", expand=True, keyboard_type=ft.KeyboardType.NUMBER,
                             prefix_icon=ft.Icon(ft.Icons.PAYMENTS))
    desc_tf = ft.TextField(label="Keterangan (opsional)", expand=True)
    date_tf = ft.TextField(label="Tanggal (YYYY-MM-DD)", expand=True, value=str(TODAY))
    form_error = ft.Text("", color=ERROR_COLOR, size=12)
    editing_id = {"value": None}

    def refresh_list():
        rows = db.get_transactions(state["month"], state["year"])
        trx_list_view.controls.clear()
        if not rows:
            trx_list_view.controls.append(
                empty_state("Belum ada transaksi bulan ini.", icon=ft.Icons.RECEIPT_LONG_OUTLINED)
            )
        for r in rows:
            trx_list_view.controls.append(_transaction_row(r, open_form, confirm_delete))
        page.update()

    def confirm_delete(r: dict):
        def do_delete(_e):
            db.delete_transaction(r["id"])
            page.pop_dialog()
            refresh_list()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hapus transaksi?"),
            content=ft.Text(f'{r["category_name"]} - {format_rupiah(r["amount"])}'),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Hapus", style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600), on_click=do_delete),
            ],
        )
        page.show_dialog(dlg)

    def reload_categories(_e=None):
        cats = db.get_categories(type_rg.value)
        category_dd.options = [ft.dropdown.Option(str(c["id"]), c["name"]) for c in cats]
        category_dd.value = category_dd.options[0].key if category_dd.options else None
        page.update()

    type_rg.on_change = reload_categories

    def open_form(existing: dict | None = None):
        form_error.value = ""
        if existing:
            editing_id["value"] = existing["id"]
            type_rg.value = existing["type"]
            reload_categories()
            category_dd.value = str(existing["category_id"])
            amount_tf.value = str(existing["amount"])
            desc_tf.value = existing["description"] or ""
            date_tf.value = str(existing["transaction_date"])
        else:
            editing_id["value"] = None
            type_rg.value = "expense"
            reload_categories()
            amount_tf.value = ""
            desc_tf.value = ""
            date_tf.value = str(TODAY)
        form_dialog.content.width = _dialog_width(page)
        page.show_dialog(form_dialog)

    def save_form(_e):
        form_error.value = ""
        if not category_dd.value:
            form_error.value = "Pilih kategori terlebih dahulu."
            page.update()
            return
        try:
            amount = Decimal(amount_tf.value.replace(",", "."))
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, AttributeError):
            form_error.value = "Jumlah harus berupa angka lebih dari 0."
            page.update()
            return
        try:
            trx_date = datetime.date.fromisoformat(date_tf.value.strip())
        except ValueError:
            form_error.value = "Format tanggal salah. Gunakan YYYY-MM-DD."
            page.update()
            return

        if editing_id["value"]:
            db.update_transaction(editing_id["value"], int(category_dd.value), type_rg.value,
                                   amount, desc_tf.value.strip(), trx_date)
        else:
            db.add_transaction(int(category_dd.value), type_rg.value, amount,
                                desc_tf.value.strip(), trx_date)
        page.pop_dialog()
        refresh_list()

    form_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Transaksi"),
        content=ft.Column(
            [type_rg, category_dd, amount_tf, date_tf, desc_tf, form_error],
            tight=True, spacing=14, width=_dialog_width(page),
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Simpan", on_click=save_form),
        ],
    )

    reload_categories()
    refresh_list()

    def on_month_change():
        refresh_list()
        page.update()

    add_button = ft.FilledButton("Tambah Transaksi", icon=ft.Icons.ADD, on_click=lambda e: open_form())

    return ft.Column(
        [
            page_header("Transaksi", selector=month_year_selector(state, on_month_change), action=add_button),
            ft.Container(height=16),
            ft.Container(
                content=trx_list_view,
                bgcolor=ft.Colors.WHITE,
                border_radius=14,
                expand=True,
                shadow=CARD_SHADOW,
            ),
        ],
        expand=True,
    )
