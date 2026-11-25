"""Host-side: turn the test expressions into editor trees and write `app/src/cases.json`.

The web demo cannot import `cassim.device` (it pulls in the core parser), so the trees, the name
styles each row would get (`name_styles`, `at_constants`, `constant_style`) and the current LaTeX
drawing are computed here with the real code and shipped as data.

    uv run python spikes/math_render_a/make_cases.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "app" / "src"))

from cassim.device.editor import Editor, Kind, Template  # noqa: E402
from cassim.device.editor_ast import row_from_text  # noqa: E402

import treeio  # noqa: E402

CASES = [
    "x=-((1+√(2))^(1/3))/2+1/(2*(1+√(2))^(1/3))+ⅈ*(√(3)/(2*(1+√(2))^(1/3))+√(3)*(1+√(2))^(1/3)/2)",
    "∫(x^2*sin(x),x,0,π)+Σ(1/n^2,n,1,10)",
    "[1/2,x^2;√(3),abs(x-1)]*{1,2,3}",
]


def _t(kind: Kind, *slots: str, cols: int = 0) -> Template:
    return Template(kind, [row_from_text(s) if s else [] for s in slots], cols)


def gallery() -> list[list]:
    """Rows for the kinds the three test expressions do not use (`row_from_text` has no reading
    for limit, piecewise, system, dms or the list template, so these are built by hand)."""
    a = row_from_text("root(x,3)+log(x,2)+derivative(x^2,x)+derivative(f(x),x,2)+∫(1/x,x)+Π(k,k,1,n)")
    b = [
        _t(Kind.LIMIT, "x", "0", "+", "1/x"), "+",
        _t(Kind.PIECEWISE, "x", "x>0", "-x", "x≤0", cols=2), "+",
        _t(Kind.SYSTEM, "x+y=1", "x-y=2", cols=1), "+",
        _t(Kind.DMS, "30", "15", "10"), "+", _t(Kind.LIST, "1", "", "x^2"),
    ]
    c = [*row_from_text("[1;2;3;4]"), "+", _t(Kind.ABS, "1/(1+1/(1+1/(1+1/x)))"), "+",
         _t(Kind.DERIVATIVE_N, "3", "t", "")]
    return [a, b, c]


def main() -> None:
    out = []
    rows = [(text, row_from_text(text)) for text in CASES]
    rows += [("gallery", r) for r in gallery()]
    for text, row in rows:
        templates = sum(isinstance(n, Template) for n in row)
        editor = Editor()
        editor.root = row
        out.append(
            {
                "text": text,
                "linear_paste": templates == 0,
                "tree": treeio.dump_row(row),
                "styles": treeio.styles_for(row),
                "latex": editor.latex(cursor=False),
            }
        )
        print(text, "-> templates at top level:", templates, file=sys.stderr)
    path = HERE / "app" / "src" / "cases.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
