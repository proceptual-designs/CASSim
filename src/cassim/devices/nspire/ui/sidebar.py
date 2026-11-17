"""The Computer view's page sorter and variable list (FR-DOC-001)."""

from collections.abc import Callable
from weakref import WeakKeyDictionary

import flet as ft

from cassim.app.theme import DARK, Theme
from cassim.core.results import VariableInfo
from cassim.devices.nspire.ui.state import AppState
from cassim.devices.nspire.ui.views import chip, icon_chip, label_text

LIST_BATCH = 50


class Sidebar:
    """The page sorter and the variable list of the current Problem (FR-DOC-001)."""

    def __init__(
        self,
        state: AppState,
        on_change: Callable[[], None],
        theme: Theme = DARK,
        on_menu: Callable[[], None] | None = None,
        on_delete: Callable[[tuple[VariableInfo, ...]], None] | None = None,
    ) -> None:
        self.state = state
        self.on_change = on_change
        self.theme = theme
        self.on_menu = on_menu  # the large Menu button above the page list
        self.on_delete = on_delete
        self.control = ft.Column(spacing=2, expand=True)
        self.page_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
        self.variable_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)
        self.height = 600.0
        self.pages_visible = True
        self.variables_visible = True
        self._document = state.document
        self._expanded: WeakKeyDictionary[object, dict[str, int]] = WeakKeyDictionary()
        self._collapsed_groups: WeakKeyDictionary[object, set[str]] = WeakKeyDictionary()
        self._collapsed_problems: WeakKeyDictionary[object, bool] = WeakKeyDictionary()

    def refresh(self) -> None:
        document = self.state.document
        if document is not self._document:
            self._document = document
            self._expanded.clear()
            self._collapsed_groups.clear()
            self._collapsed_problems.clear()
        theme = self.theme
        rows: list[ft.Control] = []
        if self.on_menu is not None:
            menu = self.on_menu
            rows.append(
                ft.Container(
                    label_text("Menu", size=16, color=theme.accent_text),
                    height=48,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=theme.accent,
                    border_radius=8,
                    ink=True,
                    on_click=lambda _: menu(),
                )
            )
        rows.append(self._heading("Pages", self.pages_visible, self._toggle_pages))
        self._pages()
        rows.append(self.page_list)
        rows.append(self._heading("Variables", self.variables_visible, self._toggle_variables))
        self._variables()
        rows.append(self.variable_list)
        self.control.controls = rows

    def _pages(self) -> None:
        document = self.state.document
        theme = self.theme
        here = (document.problem, document.page)
        pages: list[ft.Control] = []
        for problem, page, kind in document.sorter():
            problem_session = document.problems[problem].session
            collapsed = self._collapsed_problems.get(problem_session, False)
            if page and collapsed:
                continue
            text = f"{problem + 1}.{page + 1}  {self.state.page_name(kind)}"
            title = ft.Container(
                label_text(
                    text,
                    color=theme.panel_accent if (problem, page) == here else theme.panel_text,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                expand=True,
                tooltip=text,
                padding=ft.Padding.symmetric(vertical=2),
                on_click=lambda _, p=problem, q=page: self._go(p, q),
            )
            parts: list[ft.Control] = [title]
            if page == 0 and len(document.problems[problem].pages) > 1:
                parts.append(
                    icon_chip(
                        ft.Icons.MORE_HORIZ if collapsed else ft.Icons.EXPAND_LESS,
                        f"{'Expand' if collapsed else 'Collapse'} Problem {problem + 1}",
                        lambda s=problem_session: self._toggle_problem(s),
                        theme,
                        size=14,
                    )
                )
            pages.append(ft.Row(parts, spacing=2))
        self.page_list.controls = pages
        self.page_list.height = min(len(pages) * 27, max(27, self.height * 0.45))
        self.page_list.visible = self.pages_visible

    def _variables(self) -> None:
        document = self.state.document
        theme = self.theme
        session = document.problems[document.problem].session
        variables = session.variables()
        expanded = self._expanded.setdefault(session, {})
        collapsed_groups = self._collapsed_groups.setdefault(session, set())
        groups: dict[str, list[VariableInfo]] = {}
        on_delete = self.on_delete
        for row in variables:
            prefix, dot, suffix = row.name.partition(".")
            if dot and prefix and suffix:
                groups.setdefault(prefix, []).append(row)
        variable_rows: list[ft.Control] = []
        seen_groups: set[str] = set()
        for row in variables:
            prefix, dot, suffix = row.name.partition(".")
            if dot and prefix and suffix:
                if prefix not in seen_groups:
                    seen_groups.add(prefix)
                    collapsed = prefix in collapsed_groups
                    parts: list[ft.Control] = []
                    if on_delete is not None:
                        parts.append(
                            self._delete_button(
                                f"Delete {prefix} variables",
                                lambda rows=tuple(groups[prefix]): on_delete(rows),
                            )
                        )
                    variable_rows.append(
                        ft.Row(
                            [
                                *parts,
                                ft.Text(
                                    prefix,
                                    color=theme.panel_text,
                                    weight=ft.FontWeight.BOLD,
                                    size=12,
                                    expand=True,
                                ),
                                icon_chip(
                                    ft.Icons.MORE_HORIZ if collapsed else ft.Icons.EXPAND_LESS,
                                    f"{'Expand' if collapsed else 'Collapse'} {prefix} variables",
                                    lambda p=prefix: self._toggle_group(p, collapsed_groups),
                                    theme,
                                    size=14,
                                ),
                            ],
                            spacing=2,
                        )
                    )
                if prefix in collapsed_groups:
                    continue
                controls = self._variable(row, expanded, deletable=False)
                if on_delete is not None:
                    first = controls[0]
                    if isinstance(first, ft.Row):
                        first.controls.insert(
                            0, ft.Container(width=1, height=16, bgcolor=theme.key_label)
                        )
                        first.spacing = 8
                variable_rows.extend(controls)
                continue
            variable_rows.extend(self._variable(row, expanded, deletable=True))
        if not variable_rows:
            variable_rows.append(ft.Text("none", color=theme.panel_text, size=12))
        self.variable_list.controls = variable_rows
        self.variable_list.visible = self.variables_visible

    def _heading(self, title: str, visible: bool, toggle: Callable[[], None]) -> ft.Container:
        return ft.Container(
            ft.Row(
                [
                    ft.Text(title, weight=ft.FontWeight.BOLD, color=self.theme.panel_text),
                    ft.Icon(
                        ft.Icons.EXPAND_LESS if visible else ft.Icons.EXPAND_MORE,
                        color=self.theme.panel_text,
                        size=18,
                    ),
                ],
                spacing=4,
            ),
            tooltip=f"{'Hide' if visible else 'Show'} {title.lower()}",
            ink=True,
            on_click=lambda _: toggle(),
        )

    def _toggle_pages(self) -> None:
        self.pages_visible = not self.pages_visible
        self.on_change()

    def _toggle_problem(self, session: object) -> None:
        self._collapsed_problems[session] = not self._collapsed_problems.get(session, False)
        self.on_change()

    def _toggle_group(self, prefix: str, collapsed: set[str]) -> None:
        if prefix in collapsed:
            collapsed.remove(prefix)
        else:
            collapsed.add(prefix)
        self.on_change()

    def _variable(
        self, row: VariableInfo, expanded: dict[str, int], *, deletable: bool
    ) -> list[ft.Control]:
        theme = self.theme
        text = f"{row.name} = {row.text}" if not row.is_function else row.text
        label = ft.Text(
            text,
            size=12,
            color=theme.panel_text,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
            tooltip=text,
        )
        parts: list[ft.Control] = []
        on_delete = self.on_delete
        if deletable and on_delete is not None:
            parts.append(
                self._delete_button(
                    f"Delete variable {row.name}", lambda variable=row: on_delete((variable,))
                )
            )
        parts.append(label)
        if row.items is not None:
            is_expanded = row.name in expanded
            parts.append(
                icon_chip(
                    ft.Icons.EXPAND_LESS if is_expanded else ft.Icons.MORE_HORIZ,
                    f"{'Collapse' if is_expanded else 'Expand'} {row.name}",
                    lambda: self._toggle_list(row.name, expanded),
                    theme,
                    size=14,
                )
            )
        controls: list[ft.Control] = [ft.Row(parts, spacing=2)]
        if row.items is not None and row.name in expanded:
            limit = expanded[row.name]
            controls.extend(
                ft.Container(
                    ft.Text(
                        f"{index}: {item}",
                        size=12,
                        color=theme.panel_text,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        tooltip=item,
                    ),
                    padding=ft.Padding.only(left=8),
                )
                for index, item in enumerate(row.items[:limit], 1)
            )
            if limit < len(row.items):
                controls.append(
                    chip(
                        f"Show more ({len(row.items) - limit})",
                        lambda: self._show_more(row.name, expanded),
                        theme,
                    )
                )
        return controls

    def _delete_button(self, tooltip: str, action: Callable[[], None]) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icons.CLOSE,
            tooltip=tooltip,
            on_click=lambda _: action(),
            icon_color=self.theme.key_text,
            icon_size=12,
            width=20,
            height=20,
            padding=0,
        )

    def _toggle_variables(self) -> None:
        self.variables_visible = not self.variables_visible
        self.on_change()

    def _toggle_list(self, name: str, expanded: dict[str, int]) -> None:
        if name in expanded:
            del expanded[name]
        else:
            expanded[name] = LIST_BATCH
        self.on_change()

    def _show_more(self, name: str, expanded: dict[str, int]) -> None:
        expanded[name] += LIST_BATCH
        self.on_change()

    def _go(self, problem: int, page: int) -> None:
        self.state.document.go(problem, page)
        self.on_change()
