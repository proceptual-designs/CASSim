import flet as ft


@ft.control("FletPing")
class FletPing(ft.LayoutControl):
    """Trivial extension: draws `value` in Dart and reports taps to Python."""

    value: str = ""
    on_ping: ft.ControlEventHandler[FletPing] | None = None
