import flet as ft
from flet_ping import FletPing


def main(page: ft.Page):
    count = 0

    def ping(e):
        nonlocal count
        count += 1
        print(f"SPIKE9: ping {count}")
        page.add(ft.Text(f"python got ping {count}"))

    page.add(FletPing(value="Dart says hello", on_ping=ping))
    print("SPIKE9: python ready")


ft.run(main)
