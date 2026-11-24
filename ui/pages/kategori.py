"""Halaman Kategori: kelola daftar kategori pemasukan & pengeluaran."""

from __future__ import annotations

import flet as ft

import db
from theme import CARD_SHADOW
from ui.components import card_container, empty_state, page_header

ERROR_COLOR = ft.Colors.RED_600


def _category_row(c: dict, on_delete) -> ft.Container:
    is_income = c["type"] == "income"
    return ft.Container(
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=8, height=8, border_radius=4,
                            bgcolor=ft.Colors.GREEN_400 if is_income else ft.Colors.RED_400,
                        ),
                        ft.Text(c["name"], overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=10,
                    expand=True,
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("Pemasukan" if is_income else "Pengeluaran", size=11,
                                             color=ft.Colors.GREY_700),
                            bgcolor=ft.Colors.GREEN_50 if is_income else ft.Colors.RED_50,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=20,
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=ft.Colors.RED_400,
                                      on_click=lambda e: on_delete(c)),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )


def build(page: ft.Page) -> ft.Column:
    """Bangun halaman Kelola Kategori: form tambah + daftar kategori yang bisa dihapus."""
    list_col = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    name_tf = ft.TextField(label="Nama kategori baru", expand=True)
    type_dd = ft.Dropdown(
        label="Jenis", width=160,
        options=[ft.dropdown.Option("expense", "Pengeluaran"), ft.dropdown.Option("income", "Pemasukan")],
        value="expense",
    )
    error_txt = ft.Text("", color=ERROR_COLOR, size=12)

    def refresh():
        cats = db.get_categories()
        list_col.controls.clear()
        if not cats:
            list_col.controls.append(empty_state("Belum ada kategori.", icon=ft.Icons.CATEGORY_OUTLINED))
        for c in cats:
            list_col.controls.append(_category_row(c, do_delete))
        page.update()

    def do_delete(c: dict):
        def confirmed(_e):
            try:
                db.delete_category(c["id"])
            except Exception:
                error_txt.value = "Tidak bisa menghapus: kategori masih dipakai transaksi/anggaran."
            page.pop_dialog()
            refresh()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hapus kategori?"),
            content=ft.Text(c["name"]),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Hapus", style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600), on_click=confirmed),
            ],
        )
        page.show_dialog(dlg)

    def add_category(_e):
        error_txt.value = ""
        if not name_tf.value or not name_tf.value.strip():
            error_txt.value = "Nama kategori tidak boleh kosong."
            page.update()
            return
        try:
            db.add_category(name_tf.value, type_dd.value)
        except Exception:
            error_txt.value = "Kategori dengan nama & jenis yang sama sudah ada."
            page.update()
            return
        name_tf.value = ""
        refresh()

    refresh()

    form_row = ft.ResponsiveRow(
        [
            ft.Container(name_tf, col={"xs": 12, "sm": 6}),
            ft.Container(type_dd, col={"xs": 7, "sm": 3}),
            ft.Container(
                ft.FilledButton("Tambah", icon=ft.Icons.ADD, on_click=add_category, width=float("inf")),
                col={"xs": 5, "sm": 3},
            ),
        ],
        spacing=12,
        run_spacing=12,
    )

    return ft.Column(
        [
            page_header("Kelola Kategori"),
            ft.Container(height=16),
            card_container(ft.Column([form_row, error_txt])),
            ft.Container(height=16),
            ft.Container(content=list_col, expand=True, bgcolor=ft.Colors.WHITE, border_radius=14,
                         shadow=CARD_SHADOW),
        ],
        expand=True,
    )
