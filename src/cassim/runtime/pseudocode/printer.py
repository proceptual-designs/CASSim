"""The printer: a program tree written back out in a syntax file's style (FR-SYN-005, FR-SYN-007).

The `emit` section of a syntax file decides the look (keyword case, indent, terminator spellings,
whether `then` and `do` are written, the assignment, multiplication and division symbols). Whatever
the file asks for, the printer only writes spellings the same syntax accepts, so that parsing the
output with that syntax gives the tree back (up to `shape`). It never writes comments: the tree has
none, and the code pane shows the user's own text (FR-SYN-006).
"""

from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any

from cassim.runtime.pseudocode.lexer import SUPERSCRIPT
from cassim.runtime.pseudocode.syntax import DEFAULT, Syntax
from cassim.runtime.pseudocode.tree import (
    Append,
    Assign,
    Binary,
    Break,
    Call,
    Compare,
    Define,
    Expr,
    ExprStmt,
    For,
    ForEach,
    FuncAssign,
    If,
    Index,
    Input,
    ListLit,
    Name,
    Num,
    Param,
    Paren,
    Print,
    Program,
    RepeatTimes,
    RepeatUntil,
    Return,
    Stmt,
    Str,
    Unary,
    While,
)

_SUP_DIGITS = {v: k for k, v in SUPERSCRIPT.items()}
_LINE_FIELDS = frozenset({"line", "else_line", "until_line"})

# Binding strength, loosest first. A child needs brackets when it binds more loosely than its slot.
_OR, _AND, _NOT, _CMP, _ADD, _MUL, _UNARY, _POW, _POSTFIX = range(9)
_ATOM = _POSTFIX + 1
_COMPARE_ASCII = {"≤": "<=", "≥": ">=", "≠": "!="}
_ASSIGN_CANDIDATES = ("←", "<-", ":=", "=")
_TIMES_CANDIDATES = ("×", "*", "·")
_DIVIDE_CANDIDATES = ("÷", "/")


class PrintError(ValueError):
    """The tree has something this syntax cannot write (and read back)."""


# --------------------------------------------------------------------------- comparing trees


def shape(node: object, *, parens: bool = True) -> object:
    """A tree as plain nested tuples without line numbers, for comparing two trees.

    `/` and `÷` are one operator. With `parens=False`, grouping brackets are dropped as well,
    which is the right comparison for a tree that was built, not parsed (the printer adds brackets
    where precedence needs them).
    """
    if isinstance(node, list | tuple):
        return tuple(shape(n, parens=parens) for n in node)
    if not is_dataclass(node) or isinstance(node, type):
        return node
    if isinstance(node, Paren) and not parens:
        return shape(node.inner, parens=parens)
    items: list[object] = [type(node).__name__]
    for f in fields(node):
        if f.name in _LINE_FIELDS:
            continue
        value = getattr(node, f.name)
        if f.name == "branches":  # (condition, body, line)
            value = [(c, b) for c, b, _ in value]
        if f.name == "op" and value == "/":
            value = "÷"
        items.append(shape(value, parens=parens))
    return tuple(items)


# --------------------------------------------------------------------------- the printer


def print_program(program: Program | list[Stmt], syntax: Syntax = DEFAULT) -> str:
    """The program written in `syntax`'s style, one statement per line, ending in a newline."""
    body = program.body if isinstance(program, Program) else program
    out = Printer(syntax)
    out.block(body, 0)
    return "".join(f"{line}\n" for line in out.lines)


def print_expr(expr: Expr, syntax: Syntax = DEFAULT) -> str:
    """One expression written in `syntax`'s style."""
    return Printer(syntax).expr(expr)


class Printer:
    def __init__(self, syntax: Syntax = DEFAULT) -> None:
        self.syn = syntax
        self.emit: dict[str, Any] = syntax.data["emit"]
        self.lines: list[str] = []
        self.unicode = self.emit["symbols"] != "ascii"
        # In a case-sensitive syntax only the lower-case spellings in its tables are keywords.
        self.case: str = self.emit["keyword_case"] if syntax.case_insensitive else "lower"

    # ------------------------------------------------------------------ small helpers

    def word(self, text: str) -> str:
        """A keyword in the emit case."""
        if self.case == "UPPER":
            return text.upper()
        if self.case == "Capitalised":
            return text.capitalize()
        return text.lower()

    def words(self, text: str) -> str:
        return " ".join(w if w == "<variable>" else self.word(w) for w in text.split())

    def op_mode(self, spelling: str) -> str:
        if spelling == "=":
            return self.syn.eq_assign
        return self.syn.op_modes.get(spelling, "ok")

    def pick(self, preferred: str, candidates: tuple[str, ...], what: str) -> str:
        """`preferred` if the syntax accepts it, else the first candidate it accepts quietly."""
        order = [preferred, *candidates]
        for wanted in ("ok", "warn"):
            for spelling in order:
                if self.op_mode(spelling) == wanted:
                    return spelling
        raise PrintError(f"the {self.syn.name} syntax accepts no spelling for {what}")

    def pick_keyword(self, kind: str) -> str:
        """The first keyword the syntax accepts for define, print, input, return or break."""
        table = self.syn.keywords[kind]
        for wanted in ("ok", "warn"):
            for word, mode in table.items():
                if mode == wanted:
                    return self.word(word)
        raise PrintError(f"the {self.syn.name} syntax has no keyword for {kind}")

    def option(self, policy: str, emit_key: str) -> bool:
        """Whether to write an optional word (`then`, `do`)."""
        if policy == "required":
            return True
        if policy == "forbidden":
            return False
        return self.emit[emit_key] == "always"

    def add(self, depth: int, text: str) -> None:
        self.lines.append(" " * (self.emit["indent"] * depth) + text)

    # ------------------------------------------------------------------ expressions

    def times(self) -> str:
        return self.pick(
            self.emit["times"] if self.unicode else "*", _TIMES_CANDIDATES, "multiplication"
        )

    def divide(self) -> str:
        preferred = self.emit["divide"] if self.unicode else "/"
        return self.pick(preferred, _DIVIDE_CANDIDATES, "division")

    def compare_op(self, op: str) -> str:
        if op not in _COMPARE_ASCII:
            return op
        order = (op, _COMPARE_ASCII[op]) if self.unicode else (_COMPARE_ASCII[op], op)
        extra = ("<>",) if op == "≠" else ()
        for wanted in ("ok", "warn"):
            for spelling in (*order, *extra):
                if self.op_mode(spelling) == wanted:
                    return spelling
        raise PrintError(f"the {self.syn.name} syntax accepts no spelling for {op}")

    def prec(self, e: Expr) -> int:  # noqa: PLR0911
        match e:
            case Binary(op="or"):
                return _OR
            case Binary(op="and"):
                return _AND
            case Unary(op="not"):
                return _NOT
            case Compare():
                return _CMP
            case Binary(op="+" | "-"):
                return _ADD
            case Binary(op="^"):
                return _POW
            case Binary():
                return _MUL
            case Unary(op="-" | "sqrt"):
                return _UNARY
            case _:
                return _ATOM

    def sub(self, e: Expr, need: int) -> str:
        """`e`, bracketed if it binds more loosely than `need`."""
        text = self.expr(e)
        return f"({text})" if self.prec(e) < need else text

    def expr(self, e: Expr) -> str:  # noqa: PLR0911
        match e:
            case Num(text=t):
                return t
            case Str(value=v):
                return self.string(v)
            case Name(name=n):
                return n
            case Paren(inner=i):
                return f"({self.expr(i)})"
            case Call(name=n, args=a):
                return f"{n}({', '.join(self.expr(x) for x in a)})"
            case Index(target=t, index=i):
                return f"{self.sub(t, _POSTFIX)}[{self.expr(i)}]"
            case ListLit(items=items):
                return f"[{', '.join(self.expr(x) for x in items)}]"
            case Unary():
                return self.unary(e)
            case Compare():
                return self.compare(e)
            case Binary():
                return self.binary(e)
        raise PrintError(f"cannot print {type(e).__name__}")

    def string(self, value: str) -> str:
        if "\n" in value:
            raise PrintError("a string with a line break cannot be written on one line")
        if '"' not in value and self.syn.quotes.get("straight", "no") != "no":
            return f'"{value}"'
        if "”" not in value and self.syn.quotes.get("curly", "no") != "no":
            return f"“{value}”"
        raise PrintError("this syntax cannot write that string (its quote marks are not accepted)")

    def logic(self, word: str) -> str:
        return self.word(word)

    def unary(self, e: Unary) -> str:
        match e.op:
            case "-":
                return f"-{self.sub(e.operand, _UNARY)}"
            case "not":
                return f"{self.logic('not')} {self.sub(e.operand, _NOT)}"
            case "sqrt":
                return f"√{self.sub(e.operand, _POW)}"
            case "abs":
                inner = self.expr(e.operand)
                pad = " " if inner.startswith("|") or inner.endswith("|") else ""
                return f"|{pad}{inner}{pad}|"
        raise PrintError(f"cannot print the operator {e.op!r}")

    def compare(self, e: Compare) -> str:
        parts = [self.sub(e.first, _ADD)]
        for op, operand in zip(e.ops, e.rest, strict=True):
            parts += [self.compare_op(op), self.sub(operand, _ADD)]
        return " ".join(parts)

    def binary(self, e: Binary) -> str:  # noqa: PLR0911
        op = e.op
        if op in ("and", "or"):
            level = _AND if op == "and" else _OR
            tighter = level + 1  # the parser reads `a and b and c` left to right
            return f"{self.sub(e.left, level)} {self.logic(op)} {self.sub(e.right, tighter)}"
        if op in ("+", "-"):
            return f"{self.sub(e.left, _ADD)} {op} {self.sub(e.right, _MUL)}"
        if op == "^":
            return self.power(e)
        left = self.sub(e.left, _MUL)
        if op == "*":
            if e.implicit:
                return self.implicit(e, left)
            return f"{left} {self.times()} {self.sub(e.right, _UNARY)}"
        if op in ("/", "÷"):
            return f"{left} {self.divide()} {self.sub(e.right, _UNARY)}"
        if op in ("mod", "div"):
            return f"{left} {self.word(op)} {self.sub(e.right, _UNARY)}"
        raise PrintError(f"cannot print the operator {op!r}")

    def implicit(self, e: Binary, left: str) -> str:
        right = self.sub(e.right, _UNARY)
        if isinstance(e.left, Str) or right.startswith("-"):
            raise PrintError("that implicit product cannot be written without a sign")
        if isinstance(e.left, Num) and isinstance(e.right, Num):
            raise PrintError("two numbers side by side cannot be an implicit product")
        starts_name = right[:1].isalpha() and right[:1] not in "Eᴇ"
        tight = (isinstance(e.left, Num | Paren) and starts_name) or (
            right.startswith("(") and isinstance(e.left, Num | Paren | Call | Index)
        )
        tight = tight or (left.endswith(")") and (right[:1].isalpha() or right.startswith("(")))
        join = "" if tight else " "
        return f"{left}{join}{right}"

    def power(self, e: Binary) -> str:
        base = self.sub(e.left, _POSTFIX)
        exp = e.right
        sup = self.superscript(exp)
        if sup is not None:
            return base + sup
        # After `^` the parser reads a signed power, so `a^b^c` is a^(b^c).
        return f"{base}^{self.sub(exp, _UNARY)}"

    def superscript(self, exp: Expr) -> str | None:
        """`²` for a small whole-number exponent, when the syntax accepts superscripts."""
        if not self.unicode or self.syn.superscripts == "no":
            return None
        neg = isinstance(exp, Unary) and exp.op == "-"
        digits = exp.operand if isinstance(exp, Unary) and neg else exp
        if not (isinstance(digits, Num) and digits.text.isascii() and digits.text.isdigit()):
            return None
        return ("⁻" if neg else "") + "".join(_SUP_DIGITS[d] for d in digits.text)

    # ------------------------------------------------------------------ statements

    def block(self, body: list[Stmt], depth: int) -> None:
        for stmt in body:
            self.stmt(stmt, depth)

    def stmt(self, s: Stmt, depth: int) -> None:
        handler: dict[type, Callable[[Any, int], None]] = {
            Assign: self.assign, FuncAssign: self.func_assign, Input: self.input,
            Print: self.print, Append: self.append, ExprStmt: self.expr_stmt,
            Return: self.ret, Break: self.brk, If: self.if_, While: self.while_,
            For: self.for_, ForEach: self.for_each, RepeatTimes: self.repeat_times,
            RepeatUntil: self.repeat_until, Define: self.define,
        }  # fmt: skip
        handler[type(s)](s, depth)

    def assign_symbol(self, *, function: bool = False) -> str:
        preferred = self.emit["assign"] if self.unicode else "<-"
        found = self.pick(preferred, _ASSIGN_CANDIDATES, "assignment")
        if function and found == "=":
            raise PrintError("a function cannot be defined by assignment with '=' in this syntax")
        return found

    def assign(self, s: Assign, depth: int) -> None:
        self.add(depth, f"{self.expr(s.target)} {self.assign_symbol()} {self.expr(s.value)}")

    def func_assign(self, s: FuncAssign, depth: int) -> None:
        if self.syn.func_assign == "no":
            raise PrintError("this syntax does not allow defining a function by assignment")
        head = f"{s.name}({', '.join(s.params)})"
        self.add(depth, f"{head} {self.assign_symbol(function=True)} {self.expr(s.body)}")

    def input(self, s: Input, depth: int) -> None:
        self.add(depth, f"{self.pick_keyword('input')} {self.expr(s.target)}")

    def print(self, s: Print, depth: int) -> None:
        items = ", ".join(self.expr(i) for i in s.items)
        policy = self.syn.print_parens
        single_group = len(s.items) == 1 and isinstance(s.items[0], Paren)
        wrapped = policy == "required" or (
            policy == "optional" and (self.emit["print_parentheses"] == "always" or single_group)
        )
        if policy == "forbidden" and single_group:
            raise PrintError("a bracketed item cannot be the only item of print in this syntax")
        if wrapped:
            self.add(depth, f"{self.pick_keyword('print')}({items})")
        else:
            self.add(depth, f"{self.pick_keyword('print')} {items}".rstrip())

    def append(self, s: Append, depth: int) -> None:
        self.add(
            depth,
            f"{self.word('append')} {self.expr(s.value)} {self.word('to')} {self.expr(s.target)}",
        )

    def expr_stmt(self, s: ExprStmt, depth: int) -> None:
        self.add(depth, self.expr(s.expr))

    def ret(self, s: Return, depth: int) -> None:
        value = "" if s.value is None else f" {self.expr(s.value)}"
        self.add(depth, f"{self.pick_keyword('return')}{value}")

    def brk(self, s: Break, depth: int) -> None:
        self.add(depth, self.pick_keyword("break"))

    # ------------------------------------------------------------------ blocks

    def closer(self, kind: str, var: str = "") -> str | None:
        """The spelling that ends a block of `kind`, or None when indentation ends it (define)."""
        raw = self.emit["terminators"].get(kind, "")
        cased = (
            raw if any(c.isupper() for c in raw) and self.syn.case_insensitive else self.words(raw)
        )
        found = [cased, raw, raw.lower()]
        block = "repeat" if kind == "repeat" else kind
        for wanted in ("ok", "warn"):
            for text in found:
                if self.closer_mode(text, block) == wanted:
                    if "<variable>" not in text:
                        return text
                    if var:
                        return text.replace("<variable>", var)
            for spelling, (owner, mode) in self.syn.closers.items():
                if owner == block and mode == wanted:
                    text = " ".join(spelling)
                    if "<variable>" in text and not var:
                        continue
                    return self.words(text).replace("<variable>", var)
        if kind == "define" and self.syn.dedent_closes_define != "no":
            return None
        raise PrintError(f"the {self.syn.name} syntax has no way to end a {kind} block")

    def closer_mode(self, text: str, kind: str) -> str:
        words = tuple(self.syn.kw(w) for w in text.split())
        found = self.syn.closers.get(words)
        return found[1] if found is not None and found[0] == kind else "no"

    def end(self, kind: str, depth: int, var: str = "") -> None:
        text = self.closer(kind, var)
        if text is not None:
            self.add(depth, text)

    def if_(self, s: If, depth: int) -> None:
        use_then = self.option(self.syn.then, "if_then")
        for n, (cond, body, _) in enumerate(s.branches):
            head = self.word("if") if n == 0 else self.else_if()
            self.add(
                depth, f"{head} {self.expr(cond)}" + (f" {self.word('then')}" if use_then else "")
            )
            self.block(body, depth + 1)
        if s.orelse is not None:
            self.add(depth, self.word("else"))
            self.block(s.orelse, depth + 1)
        self.end("if", depth)

    def else_if(self) -> str:
        for wanted in ("ok", "warn"):
            for words, mode in self.syn.else_if.items():
                if mode == wanted:
                    return " ".join(self.word(w) for w in words)
        raise PrintError(f"the {self.syn.name} syntax has no 'else if' spelling")

    def while_(self, s: While, depth: int) -> None:
        do = f" {self.word('do')}" if self.option(self.syn.while_do, "while_do") else ""
        self.add(depth, f"{self.word('while')} {self.expr(s.cond)}{do}")
        self.block(s.body, depth + 1)
        self.end("while", depth)

    def for_(self, s: For, depth: int) -> None:
        do = f" {self.word('do')}" if self.option(self.syn.for_do, "for_do") else ""
        if s.step is not None and self.syn.for_step == "no":
            raise PrintError("this syntax does not allow 'step' in a for loop")
        step = "" if s.step is None else f" {self.word('step')} {self.expr(s.step)}"
        self.add(
            depth,
            f"{self.word('for')} {s.var} {self.word('from')} {self.expr(s.start)} "
            f"{self.word('to')} {self.expr(s.stop)}{step}{do}",
        )
        self.block(s.body, depth + 1)
        self.end("for", depth, s.var)

    def for_each(self, s: ForEach, depth: int) -> None:
        do = f" {self.word('do')}" if self.option(self.syn.for_do, "for_do") else ""
        self.add(
            depth,
            f"{self.word('for')} {self.word('each')} {s.var} {self.word('in')} "
            f"{self.expr(s.iterable)}{do}",
        )
        self.block(s.body, depth + 1)
        self.end("for", depth, s.var)

    def repeat_times(self, s: RepeatTimes, depth: int) -> None:
        self.add(depth, f"{self.word('repeat')} {self.expr(s.count)} {self.word('times')}")
        self.block(s.body, depth + 1)
        self.end("repeat", depth)

    def repeat_until(self, s: RepeatUntil, depth: int) -> None:
        self.add(depth, self.word("repeat"))
        self.block(s.body, depth + 1)
        self.add(depth, f"{self.word('until')} {self.expr(s.cond)}")

    def define(self, s: Define, depth: int) -> None:
        params = ", ".join(self.param(p) for p in s.params)
        colon = ":" if self.syn.define_colon == "required" else ""
        self.add(depth, f"{self.pick_keyword('define')} {s.name}({params}){colon}")
        self.block(s.body, depth + 1)
        if self.closer("define") is None and not s.body:
            raise PrintError("a function with no body needs an end keyword in this syntax")
        self.end("define", depth)

    def param(self, p: Param) -> str:
        text = p.name if p.sig is None else f"{p.name}({', '.join(p.sig)})"
        if p.default is None:
            return text
        if self.syn.default_params == "no":
            raise PrintError("this syntax does not allow default parameter values")
        return f"{text} = {self.expr(p.default)}"
