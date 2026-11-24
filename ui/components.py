"""
Komponen UI yang dipakai berulang di beberapa halaman:
kartu putih, state kosong, header halaman, dan pemilih bulan/tahun.
"""

from __future__ import annotations

import datetime
from typing import Callable

import flet as ft

from theme import BULAN_ID, CARD_SHADOW

TODAY = datetime.date.today()


def card_container(content: ft.Control, padding: int = 18, expand: bool = False) -> ft.Container:
    """Wrapper kartu putih dengan sudut membulat & bayangan tipis, dipakai di semua halaman."""
    return ft.Container(
        content=content,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        padding=padding,
        expand=expand,
        shadow=CARD_SHADOW,
    )


def empty_state(message: str, icon: str = ft.Icons.INBOX_OUTLINED) -> ft.Container:
    """Placeholder yang tampil saat sebuah daftar masih kosong."""
    return ft.Container(
        padding=30,
        content=ft.Column(
            [
                ft.Icon(icon, size=36, color=ft.Colors.GREY_400),
                ft.Text(message, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )


def page_header(
    title: str,
    selector: ft.Control | None = None,
    action: ft.Control | None = None,
) -> ft.Row:
    """Header halaman (judul + kontrol opsional) yang melipat ke bawah di layar sempit."""
    right_items = [item for item in (selector, action) if item is not None]

    return ft.Row(
        [
            ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
            ft.Row(right_items, spacing=12, wrap=True) if right_items else ft.Container(),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        spacing=12,
    )


def month_year_selector(state: dict, on_change: Callable[[], None]) -> ft.Row:
    """
    Dropdown bulan + tahun yang mengubah `state["month"]` / `state["year"]`
    lalu memanggil `on_change()` setiap kali salah satunya diganti.
    """
    month_dd = ft.Dropdown(
        width=150,
        dense=True,
        value=str(state["month"]),
        options=[ft.dropdown.Option(str(i), BULAN_ID[i - 1]) for i in range(1, 13)],
    )
    year_dd = ft.Dropdown(
        width=100,
        dense=True,
        value=str(state["year"]),
        options=[ft.dropdown.Option(str(y)) for y in range(TODAY.year - 5, TODAY.year + 2)],
    )

    def changed(_e):
        state["month"] = int(month_dd.value)
        state["year"] = int(year_dd.value)
        on_change()

    month_dd.on_change = changed
    year_dd.on_change = changed
    return ft.Row([month_dd, year_dd], spacing=8, wrap=True)
