"""Desktop check of the spike-6 editor: key sequences in, TI text out, evaluated by the engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "spike6_web" / "src"))
from editor import Editor  # noqa: E402

from cassim.core.session import Session  # noqa: E402


def run(seq: str) -> Editor:
    """Letters L R U D B are the arrow keys and Backspace; everything else is typed."""
    ed = Editor()
    for ch in seq:
        if ch == "L":
            ed.left()
        elif ch == "R":
            ed.right()
        elif ch == "U":
            ed.vertical(up=True)
        elif ch == "D":
            ed.vertical(up=False)
        elif ch == "B":
            ed.backspace()
        else:
            ed.insert(ch)
    return ed


# (keys, expected result of evaluating the linear text with x=2, or None)
CASES = [
    ("1/3R+1/4", "7/12"),
    ("1/(2/3R)", None),
    ("2^3R+1", "9"),
    ("√2R*√8", "4"),
    ("(1+2)/3", "1"),
    ("2x^2R+3x", "14"),
    ("1/2DB3", None),
    ("1/2LLLLB", None),
]

if __name__ == "__main__":
    s = Session()
    s.eval("x:=2")
    for seq, want in CASES:
        ed = run(seq)
        lin = ed.linear()
        res = s.eval(lin)
        ok = "" if want is None else ("OK" if res.text == want else f"WANT {want}")
        print(f"{seq:12} {lin:30} = {res.text or res.error:10} {ok}")
        print(f"{'':12} {ed.latex()}")
