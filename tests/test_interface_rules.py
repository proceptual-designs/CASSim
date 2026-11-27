# Requirements traced here: FR-DEV-008, FR-THEME-001
"""SDD-15's interface rules, checked in the source so every app and every agent keeps them.

- Labels (menu items, buttons, dialog titles, switches) are in sentence case (SDD-15 section
  9.1). App and page names, acronyms, command names and single letters keep their capitals; a
  device menu keeps its words, order and numbering (FR-DEV-008). Labels made at run time are not
  seen: Data & Statistics' plot types show their stored values (`stats/plots.py`: Dot Plot).
- A dialog's confirming button comes last, after Cancel (section 9.2, Material).
- Colours come from the theme's tokens (section 7.2), not literal hex values.

Each rule has a frozen list of what does not follow it yet. The list may only shrink: a new
exception fails, and so does an entry that no longer applies (delete it, and the gap's row in
SDD-15 section 10 when that is closed). Run this file as a script to print the current lists.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "cassim"

# ---- sentence case ------------------------------------------------------------------------------

# Names that keep their capitals inside a label: apps and pages, products, people
PROPER = (
    "Lists & Spreadsheet",
    "Data & Statistics",
    "Vernier DataQuest",
    "Program Editor",
    "Press-to-Test",
    "Geometry",
    "Graphs",
    "Calculator",
    "Notes",
    "Question",
    "Python",
    "CASSim",
    "Nspire",
    "MathO",
    "Home",
    "Pseudocode",
    "Scientific",
    "Taylor",
    "Pdf",  # a distribution's density and cumulative functions, as abbreviations
    "Cdf",
)
_WORD = re.compile("[A-Za-z][A-Za-z'" + chr(0x2019) + "]*")  # with a curly apostrophe
_RESTART = ("▸", ":", "—", ".", "?", "!")  # a new phrase starts after these


def _keep(word: str) -> bool:
    camel = any(c.isupper() for c in word[1:])  # a command name: EndFunc, LinRegMx
    return len(word) == 1 or word.isupper() or camel or word in PROPER


def sentence(label: str) -> str:
    """`label` in sentence case: capitals after a phrase's first word are lowered, except
    names, acronyms, command names and single letters; One-Variable is One-variable."""
    protected = [
        (m.start(), m.end()) for name in PROPER for m in re.finditer(re.escape(name), label)
    ]

    def guarded(at: int) -> bool:
        return any(a <= at < b for a, b in protected)

    out = list(label)
    first = True
    for match in _WORD.finditer(label):
        start, word = match.start(), match.group()
        if first or label[:start].rstrip().endswith(_RESTART):
            first = False
            continue
        if not guarded(start) and not _keep(word) and word[0].isupper():
            out[start] = word[0].lower()
    text = "".join(out)
    return re.sub(
        r"(?<=[A-Za-z]-)([A-Z])(?=[a-z])",
        lambda m: m.group(1) if guarded(m.start()) else m.group(1).lower(),
        text,
    )


# Calls whose first argument (or label/title/content/text) is a label, including the device
# menus' helpers (`devices/nspire/menus.py`), and tables of menu labels (first item of a row)
LABEL_CALLS = frozenset(
    {
        "MenuItemButton",
        "SubmenuButton",
        "MenuItem",
        "Item",
        "TextButton",
        "FilledButton",
        "ElevatedButton",
        "OutlinedButton",
        "FilledTonalButton",
        "Switch",
        "Checkbox",
        "AlertDialog",
        "Wizard",
        "Tab",
        "Radio",
        "confirm",
        "notice",
        "todo",
        "tool",
        "fn",
        "cmd",
        "conv",
        "sub",
        "wiz",
        "todo_sub",
        "act",
        "_cell",
        "_sheet_formula",
        "add",
        "_dist",
        "_regression",
        "command_wizard",
        "_template_item",
        "_item",
        "_grey",
    }
)
LABEL_TABLES = frozenset({"_REGRESSIONS", "_DISTRIBUTIONS", "STAT_CALCULATIONS"})
LABEL_KEYWORDS = frozenset({"label", "title", "content", "text"})

# Labels not in sentence case yet, as (module, label)
TITLE_CASE_LEFT: frozenset[tuple[str, str]] = frozenset()


def _name(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else ""


def _literal(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and _name(node.func) == "Text" and node.args:
        return _literal(node.args[0])
    return None


def _ui_files() -> list[tuple[str, ast.Module]]:
    """Every module that can show something: all but the maths and the code runtimes."""
    files = []
    for path in sorted(SRC.rglob("*.py")):
        relative = path.relative_to(SRC).as_posix()
        if relative.startswith(("core/", "runtime/")):
            continue
        files.append((relative, ast.parse(path.read_text(encoding="utf-8"))))
    return files


def _labels(tree: ast.Module) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        table = isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple)
        if table and any(isinstance(t, ast.Name) and t.id in LABEL_TABLES for t in node.targets):
            for row in node.value.elts:
                if isinstance(row, ast.Tuple) and row.elts:
                    found += [label] if (label := _literal(row.elts[0])) else []
        if not isinstance(node, ast.Call) or _name(node.func) not in LABEL_CALLS:
            continue
        values = node.args[:1] + [k.value for k in node.keywords if k.arg in LABEL_KEYWORDS]
        found += [label for value in values if (label := _literal(value))]
    return found


def title_case_labels() -> set[tuple[str, str]]:
    return {
        (relative, label)
        for relative, tree in _ui_files()
        for label in _labels(tree)
        if sentence(label) != label
    }


# ---- dialog buttons -----------------------------------------------------------------------------

BUTTONS = frozenset({"TextButton", "FilledButton", "ElevatedButton", "OutlinedButton"})
CANCEL_LAST_LEFT: frozenset[tuple[str, int]] = frozenset()


def cancel_last() -> set[tuple[str, int]]:
    """Dialogs whose last button is Cancel: (module, line)."""
    return {(relative, line) for relative, tree in _ui_files() for line in _cancel_last_in(tree)}


def _cancel_last_in(tree: ast.Module) -> list[int]:
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _name(node.func) == "AlertDialog"):
            continue
        for keyword in node.keywords:
            if keyword.arg != "actions" or not isinstance(keyword.value, ast.List):
                continue
            labels = [
                _literal(b.args[0] if b.args else None)
                or next((_literal(k.value) for k in b.keywords if k.arg == "content"), None)
                for b in keyword.value.elts
                if isinstance(b, ast.Call) and _name(b.func) in BUTTONS
            ]
            if len(labels) > 1 and labels[-1] == "Cancel":
                found.append(node.lineno)
    return found


# ---- literal colours ----------------------------------------------------------------------------

_HEX = re.compile(r"""["']#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?["']""")
# Where literal colours belong: the theme's tokens, and the devices' own looks (skins and key
# colours copied from the hardware, which follow the device rather than the theme)
COLOUR_HOMES = frozenset(
    {"app/theme.py", "devices/scientific/ui/skins.py", "devices/scientific/layouts.py"}
)
# Literal colours elsewhere, by module, until they become tokens (SDD-15 section 10, gap 17)
COLOURS_LEFT: dict[str, int] = {
    "app/appearance.py": 24,  # the colour picker's swatches
    "app/math_canvas.py": 3,
    "app/scene_canvas.py": 13,  # the drawing palette the theme starts from
    "device/editor.py": 3,
    "devices/nspire/ui/app.py": 1,
    "devices/nspire/ui/graphs_view.py": 1,  # an all-but-invisible box that takes clicks
    "devices/nspire/ui/views.py": 8,
    "devices/pseudocode/ui/app.py": 1,
    "devices/scientific/ui/app.py": 4,  # key-legend contrast and the case's shadow
}


def literal_colours() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in sorted(SRC.rglob("*.py")):
        relative = path.relative_to(SRC).as_posix()
        if relative in COLOUR_HOMES:
            continue
        if found := len(_HEX.findall(path.read_text(encoding="utf-8"))):
            counts[relative] = found
    return dict(counts)


# ---- the tests ----------------------------------------------------------------------------------


def test_the_sentence_case_rule() -> None:
    assert sentence("Window Settings…") == "Window settings…"
    assert sentence("One-Variable Statistics") == "One-variable statistics"
    assert sentence("Add Lists & Spreadsheet") == "Add Lists & Spreadsheet"
    assert sentence("Func…EndFunc") == "Func…EndFunc"
    assert sentence("Normal Cdf") == "Normal Cdf"
    assert sentence("ANOVA 2-Way") == "ANOVA 2-way"
    assert sentence("Doc ▸ File ▸ Save as") == "Doc ▸ File ▸ Save as"
    assert sentence("Add X Variable") == "Add X variable"
    assert sentence("Press-to-Test") == "Press-to-Test"


def test_the_scans_find_what_they_look_for() -> None:
    """The checks below see a bad label, a Cancel-last dialog and a literal colour."""
    code = ast.parse(
        "\n".join(
            (
                'MenuItem("Plot Type", key="1")',
                'wiz("Finance Solver", "tvm")',
                '_REGRESSIONS = (("Cubic Regression", "CubicReg", "7"),)',
                'ft.AlertDialog(actions=[ft.TextButton("Save"), ft.TextButton("Cancel")])',
                'ft.AlertDialog(actions=[ft.TextButton("Cancel"), ft.TextButton(content="Save")])',
            )
        )
    )
    assert {label for label in _labels(code) if sentence(label) != label} == {
        "Plot Type",
        "Finance Solver",
        "Cubic Regression",
    }
    assert _cancel_last_in(code) == [4]
    colours = _HEX.findall('color="#ffd479", bgcolor="#30000000", text="#1"')
    assert colours == ['"#ffd479"', '"#30000000"']


def test_labels_are_in_sentence_case() -> None:
    """SDD-15 section 9.1: CASSim's labels and the device menus' labels."""
    found = title_case_labels()
    new = sorted(found - TITLE_CASE_LEFT)
    assert not new, f"labels not in sentence case (sentence() gives the fix): {new}"
    fixed = sorted(TITLE_CASE_LEFT - found)
    assert not fixed, f"now in sentence case: delete from TITLE_CASE_LEFT: {fixed}"


def test_a_dialog_confirms_last() -> None:
    """SDD-15 section 9.2: [Cancel] [Save], never [Save] [Cancel]."""
    found = cancel_last()
    assert not sorted(found - CANCEL_LAST_LEFT), f"Cancel is last in: {sorted(found)}"
    assert not sorted(CANCEL_LAST_LEFT - found), "fixed: delete from CANCEL_LAST_LEFT"


def test_colours_come_from_the_theme() -> None:
    """SDD-15 section 7.2: a new literal colour fails; use a token from `app/theme.py`."""
    found = literal_colours()
    grown = {f: n for f, n in found.items() if n > COLOURS_LEFT.get(f, 0)}
    assert not grown, f"new literal colours (use a theme token): {grown}"
    shrunk = {f: (n, found.get(f, 0)) for f, n in COLOURS_LEFT.items() if found.get(f, 0) < n}
    assert not shrunk, f"fewer literal colours now: lower COLOURS_LEFT to match: {shrunk}"


if __name__ == "__main__":
    print("TITLE_CASE_LEFT:", sorted(title_case_labels()))
    print("CANCEL_LAST_LEFT:", sorted(cancel_last()))
    print("COLOURS_LEFT:", literal_colours())
