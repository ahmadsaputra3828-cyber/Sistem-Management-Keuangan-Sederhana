"""
Konstanta tampilan: palet warna, breakpoint, bayangan kartu, dan nama bulan.
Dipisah dari UI supaya mudah diganti tanpa menyentuh logika halaman.
"""

import flet as ft

BULAN_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# Lebar (px) di bawah ini dianggap layar sempit / mobile.
MOBILE_BREAKPOINT = 820

# Palet warna terpusat agar konsisten di seluruh aplikasi.
PRIMARY = ft.Colors.INDIGO_600
PRIMARY_DARK = ft.Colors.INDIGO_800
PRIMARY_SOFT = ft.Colors.INDIGO_50
INCOME_COLOR = ft.Colors.GREEN_700
EXPENSE_COLOR = ft.Colors.RED_600
BG_COLOR = ft.Colors.GREY_100

CARD_SHADOW = ft.BoxShadow(
    blur_radius=10,
    spread_radius=0,
    offset=ft.Offset(0, 2),
    color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
)


def format_rupiah(value) -> str:
    """Format angka menjadi string 'Rp 1.234.567'."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0
    return "Rp " + f"{value:,.0f}".replace(",", ".")
