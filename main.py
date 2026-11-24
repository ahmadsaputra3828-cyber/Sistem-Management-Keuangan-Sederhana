
import datetime

import flet as ft

import db
from theme import BG_COLOR
from ui.navigation import AppShell
from ui.pages import anggaran, dashboard, kategori, transaksi


def build_db_error_view(error_message: str) -> ft.Container:
    """Tampilan fallback saat koneksi database gagal di awal startup."""
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=24,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=48),
                ft.Text("Gagal terhubung ke database MySQL", size=18, weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(error_message, color=ft.Colors.RED, selectable=True, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    "Periksa file .env (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME) "
                    "dan pastikan schema.sql sudah dijalankan.",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            width=420,
        ),
    )


def main(page: ft.Page):
    page.title = "Manajemen Keuangan Pribadi"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
    page.bgcolor = BG_COLOR
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 380
    page.window.min_height = 560

    ok, err = db.test_connection()
    if not ok:
        page.add(build_db_error_view(str(err)))
        return

    today = datetime.date.today()
    # State global dipakai bersama lintas halaman: bulan/tahun aktif (Dashboard & Anggaran)
    # dan indeks halaman nav aktif.
    state = {"month": today.month, "year": today.year, "nav_index": 0}

    content_area = ft.Container(expand=True)

    pages = {
        0: lambda: dashboard.build(page, state, content_area),
        1: lambda: transaksi.build(page, state),
        2: lambda: anggaran.build(page, state),
        3: lambda: kategori.build(page),
    }

    def show_page(index: int):
        content_area.content = pages[index]()
        page.update()

    shell = AppShell(page, state, content_area, on_nav_change=show_page)
    page.on_resize = shell.handle_resize

    show_page(state["nav_index"])
    shell.apply()


if __name__ == "__main__":
    ft.app(target=main)
