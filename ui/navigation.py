"""
Kerangka navigasi aplikasi: NavigationRail untuk layar lebar,
NavigationBar untuk layar sempit (mobile), beserta logika switch-nya.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from theme import MOBILE_BREAKPOINT, PRIMARY_SOFT

NAV_ITEMS = [
    (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "Dashboard"),
    (ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG, "Transaksi"),
    (ft.Icons.PIE_CHART_OUTLINE, ft.Icons.PIE_CHART, "Anggaran"),
    (ft.Icons.CATEGORY_OUTLINED, ft.Icons.CATEGORY, "Kategori"),
]


def is_mobile(page: ft.Page) -> bool:
    return (page.width or 1200) < MOBILE_BREAKPOINT


def build_nav_rail(selected_index: int, on_change: Callable) -> ft.NavigationRail:
    return ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=90,
        bgcolor=ft.Colors.WHITE,
        indicator_color=PRIMARY_SOFT,
        destinations=[
            ft.NavigationRailDestination(icon=ic, selected_icon=sic, label=lbl)
            for ic, sic, lbl in NAV_ITEMS
        ],
        on_change=on_change,
    )


def build_nav_bar(selected_index: int, on_change: Callable) -> ft.NavigationBar:
    return ft.NavigationBar(
        selected_index=selected_index,
        bgcolor=ft.Colors.WHITE,
        indicator_color=PRIMARY_SOFT,
        destinations=[
            ft.NavigationBarDestination(icon=ic, selected_icon=sic, label=lbl)
            for ic, sic, lbl in NAV_ITEMS
        ],
        on_change=on_change,
    )


class AppShell:
    """
    Mengatur kerangka luar aplikasi (rail vs bottom-nav) dan beralih di antara
    keduanya saat lebar layar melewati MOBILE_BREAKPOINT, tanpa membongkar
    ulang konten di content_area yang tidak perlu berubah.
    """

    def __init__(self, page: ft.Page, state: dict, content_area: ft.Container, on_nav_change: Callable):
        self.page = page
        self.state = state
        self.content_area = content_area
        self.on_nav_change = on_nav_change
        self._is_mobile: bool | None = None

    def _nav_change(self, e: ft.ControlEvent):
        self.state["nav_index"] = e.control.selected_index
        self.on_nav_change(self.state["nav_index"])

    def apply(self):
        """Susun ulang kerangka aplikasi sesuai lebar layar saat ini."""
        mobile = is_mobile(self.page)
        self.content_area.padding = 16 if mobile else 24
        self.page.controls.clear()

        if mobile:
            self.page.navigation_bar = build_nav_bar(self.state["nav_index"], self._nav_change)
            self.page.add(self.content_area)
        else:
            self.page.navigation_bar = None
            self.page.add(
                ft.Row(
                    [
                        build_nav_rail(self.state["nav_index"], self._nav_change),
                        ft.VerticalDivider(width=1),
                        self.content_area,
                    ],
                    expand=True,
                    spacing=0,
                )
            )

        self._is_mobile = mobile
        self.page.update()

    def handle_resize(self, _e=None):
        """
        Hanya susun ulang kerangka saat berpindah antara mode mobile <-> desktop,
        agar tidak ada "kedipan" saat resize kecil. Konten di dalamnya (ResponsiveRow,
        dialog, form) sudah menyesuaikan diri sendiri terhadap lebar layar.
        """
        if is_mobile(self.page) != self._is_mobile:
            self.apply()
