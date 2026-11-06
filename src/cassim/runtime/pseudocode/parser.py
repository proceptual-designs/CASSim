"""Pratt expression parser and line-oriented block parser for the pseudocode dialect.

The grammar is the tolerant default of docs/pseudocode/syntax-default.yaml, written directly: the
syntax-file-driven version (FR-SYN-001) replaces the tables at the top of this module. End keywords
decide structure; indentation closes a block only when an end keyword is missing
(dialect section 5).
"""

from dataclasses import dataclass

from cassim.runtime.pseudocode.errors import PseudocodeSyntaxError
from cassim.runtime.pseudocode.lexer import Token, tokenize
from cassim.runtime.pseudocode.tree import (
    Append,
    Assign,
    Binary,
    Break,
    Call,
    Compare,
    Define,
    Diagnostic,
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

CONSTANT_NAMES = {"π", "pi", "ⅇ", "ⅈ"}
# Words that end an expression and so can never start an implicitly multiplied factor.
_STOP_WORDS = {"then", "do", "to", "step", "times", "is", "and", "or", "not", "mod", "div", "from",
               "in", "until", "else"}  # fmt: skip
_NEXT_WORDS = 2  # `next` or `next k`
_MIN_FUNC_ASSIGN = 4  # name ( ) ←
_COMPARE = {"=", "≠", "<", ">", "≤", "≥"}
_CLOSERS: dict[tuple[str, ...], str] = {
    ("endif",): "if", ("end", "if"): "if",
    ("endwhile",): "while", ("wend",): "while", ("end", "while"): "while",
    ("endfor",): "for", ("end", "for"): "for",
    ("endrepeat",): "repeat", ("end", "repeat"): "repeat",
    ("enddefine",): "define", ("endfunction",): "define", ("end", "define"): "define",
    ("end", "function"): "define", ("end",): "define",
}  # fmt: skip


@dataclass(slots=True)
class Line:
    toks: list[Token]
    no: int
    col: int


def _closer_kind(line: Line) -> str | None:
    if any(t.kind != "NAME" for t in line.toks):
        return None
    words = tuple(t.text.lower() for t in line.toks)
    if words and words[0] == "next" and len(words) <= _NEXT_WORDS:  # `next` or `next k`
        return "for"
    return _CLOSERS.get(words)


def _continuation(line: Line) -> str | None:
    first = line.toks[0]
    if first.kind != "NAME":
        return None
    word = first.text.lower()
    if word in ("elseif", "elif"):
        return "elseif"
    if word == "else":
        nxt = line.toks[1].text.lower() if len(line.toks) > 1 else ""
        return "elseif" if nxt == "if" else "else"
    if word == "until":
        return "until"
    return None


def _text(line: Line) -> str:
    return " ".join(t.raw or t.text for t in line.toks)


class Parser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.lines: list[Line] = []
        current: list[Token] = []
        for tok in tokenize(source):
            if tok.kind == "NEWLINE":
                if current:
                    self.lines.append(Line(current, current[0].line, current[0].col))
                current = []
            elif tok.kind != "EOF":
                current.append(tok)
        self.pos = 0
        self.warnings: list[Diagnostic] = []
        self.stack: list[str] = []
        self.t: list[Token] = []  # tokens of the line being parsed
        self.i = 0
        self.abs_depth = 0

    # ------------------------------------------------------------------ helpers

    def warn(self, line: int, message: str) -> None:
        diagnostic = Diagnostic(line, message)
        if diagnostic not in self.warnings:
            self.warnings.append(diagnostic)

    def error(self, message: str, tok: Token | None = None) -> PseudocodeSyntaxError:
        if tok is None and self.t:
            tok = self.t[min(self.i, len(self.t) - 1)]
        return PseudocodeSyntaxError(message, tok.line if tok else 0, tok.col if tok else 0)

    def peek(self) -> Token | None:
        return self.t[self.i] if self.i < len(self.t) else None

    def at_op(self, *ops: str) -> bool:
        tok = self.peek()
        return tok is not None and tok.kind == "OP" and tok.text in ops

    def at_word(self, *words: str) -> bool:
        tok = self.peek()
        return tok is not None and tok.kind == "NAME" and tok.text.lower() in words

    def take(self) -> Token:
        tok = self.peek()
        if tok is None:
            raise self.error("unexpected end of line")
        self.i += 1
        return tok

    def expect_op(self, op: str) -> Token:
        if not self.at_op(op):
            tok = self.peek()
            found = f", found {tok.raw or tok.text!r}" if tok else ""
            raise self.error(f"expected {op!r}{found}")
        return self.take()

    def expect_word(self, word: str) -> Token:
        if not self.at_word(word):
            raise self.error(f"expected {word!r}")
        return self.take()

    def skip_word(self, *words: str) -> bool:
        if self.at_word(*words):
            self.i += 1
            return True
        return False

    def expect_end(self) -> None:
        tok = self.peek()
        if tok is not None:
            raise self.error(f"unexpected {tok.raw or tok.text!r}", tok)

    def use(self, line: Line) -> None:
        self.t, self.i, self.abs_depth = line.toks, 0, 0

    # ------------------------------------------------------------------ program and blocks

    def parse_program(self) -> Program:
        body = self.parse_body(None)
        if self.pos < len(self.lines):
            line = self.lines[self.pos]
            if _continuation(line):
                raise PseudocodeSyntaxError(
                    f"'{line.toks[0].text}' without a matching block", line.no
                )
            raise PseudocodeSyntaxError(f"'{_text(line)}' closes nothing", line.no)
        return Program(body, self.source.splitlines(), self.warnings)

    def parse_body(self, opener: Line | None) -> list[Stmt]:
        """Statements up to a closer, a continuation (else, until) or, if indented, a dedent."""
        body: list[Stmt] = []
        dedent_closes = False
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            if _continuation(line) or _closer_kind(line):
                break
            if opener is not None and body and dedent_closes and line.col <= opener.col:
                break
            if opener is not None and not body:
                dedent_closes = line.col > opener.col
            body.append(self.parse_statement())
        return body

    def parse_block(self, kind: str, opener: Line) -> list[Stmt]:
        self.stack.append(kind)
        try:
            return self.parse_body(opener)
        finally:
            self.stack.pop()

    def close_block(self, kind: str, opener: Line) -> None:
        """Consume the closer of `kind`, or note that it is missing."""
        if self.pos >= len(self.lines):
            if kind != "define":
                raise PseudocodeSyntaxError(
                    f"missing 'end {kind}' for the {kind} on line {opener.no}", opener.no
                )
            return
        line = self.lines[self.pos]
        closer = _closer_kind(line)
        if closer == kind:
            self.pos += 1
            return
        if closer is not None and closer not in self.stack:
            raise PseudocodeSyntaxError(f"'{_text(line)}' closes nothing", line.no)
        if kind != "define":
            self.warn(opener.no, f"missing 'end {kind}' for the {kind} on line {opener.no}")

    # ------------------------------------------------------------------ statements

    def parse_statement(self) -> Stmt:
        line = self.lines[self.pos]
        self.use(line)
        first = line.toks[0]
        word = first.text.lower() if first.kind == "NAME" else ""
        nxt = line.toks[1] if len(line.toks) > 1 else None
        assigning = nxt is not None and nxt.kind == "OP" and nxt.text == "←"
        if word and not assigning:
            block = {
                "define": self.parse_define, "function": self.parse_define,
                "if": self.parse_if, "while": self.parse_while, "for": self.parse_for,
                "repeat": self.parse_repeat,
            }.get(word)  # fmt: skip
            if block is not None:
                return block(line)
            simple = {
                "return": self.parse_return, "print": self.parse_print, "output": self.parse_print,
                "input": self.parse_input, "append": self.parse_append, "break": self.parse_break,
            }.get(word)  # fmt: skip
            if simple is not None:
                self.pos += 1
                self.i = 1
                return simple(line)
        self.pos += 1
        return self.parse_simple(line)

    def parse_simple(self, line: Line) -> Stmt:
        if self._is_func_assign():
            name = self.take().text
            self.expect_op("(")
            params: list[str] = []
            while not self.at_op(")"):
                params.append(self.take().text)
                if self.at_op(","):
                    self.take()
            self.expect_op(")")
            self.expect_op("←")
            body = self.parse_or()
            self.expect_end()
            return FuncAssign(name, tuple(params), body, line.no)
        expr = self.parse_or()
        if self.at_op("←"):
            self.take()
            target = self._target(expr)
            value = self.parse_or()
            self.expect_end()
            return Assign(target, value, line.no)
        self.expect_end()
        if (
            isinstance(expr, Compare)
            and expr.ops == ("=",)
            and isinstance(expr.first, Name | Index)
        ):
            self.warn(line.no, "'=' used to assign; treated as '←'")
            return Assign(self._target(expr.first), expr.rest[0], line.no)
        return ExprStmt(expr, line.no)

    def _is_func_assign(self) -> bool:
        t = self.t
        if (
            len(t) < _MIN_FUNC_ASSIGN
            or t[0].kind != "NAME"
            or t[1].text != "("
            or t[1].kind != "OP"
        ):
            return False
        j = 2
        while j < len(t) and (t[j].kind == "NAME" or t[j].text == ","):
            j += 1
        return j + 1 < len(t) and t[j].text == ")" and t[j + 1].text == "←"

    def _target(self, expr: Expr) -> Name | Index:
        if isinstance(expr, Name | Index):
            return expr
        raise self.error("the left of ← must be a variable")

    def parse_return(self, line: Line) -> Stmt:
        value = None if self.peek() is None else self.parse_or()
        self.expect_end()
        return Return(value, line.no)

    def parse_break(self, line: Line) -> Stmt:
        self.expect_end()
        return Break(line.no)

    def parse_input(self, line: Line) -> Stmt:
        target = self._target(self.parse_postfix())
        self.expect_end()
        return Input(target, line.no)

    def parse_append(self, line: Line) -> Stmt:
        value = self.parse_or()
        self.expect_word("to")
        target = self.parse_or()
        self.expect_end()
        return Append(value, target, line.no)

    def parse_print(self, line: Line) -> Stmt:
        items: list[Expr] = []
        wrapped = self.at_op("(") and self._matching_paren(self.i) == len(self.t) - 1
        if wrapped:  # print(a, b): the brackets hold the whole argument list
            self.take()
        while self.peek() is not None and not (wrapped and self.at_op(")")):
            items.append(self.parse_or())
            if self.at_op(","):
                self.take()
            elif self.peek() is not None and not (wrapped and self.at_op(")")):
                self.warn(line.no, "print items without a comma; treated as separate items")
        if wrapped:
            self.expect_op(")")
        self.expect_end()
        return Print(items, line.no)

    def _matching_paren(self, start: int) -> int:
        depth = 0
        for j in range(start, len(self.t)):
            tok = self.t[j]
            if tok.kind == "OP" and tok.text == "(":
                depth += 1
            elif tok.kind == "OP" and tok.text == ")":
                depth -= 1
                if depth == 0:
                    return j
        return -1

    def parse_define(self, line: Line) -> Stmt:
        self.i = 1
        name = self.take()
        if name.kind != "NAME":
            raise self.error("expected a function name", name)
        params: list[Param] = []
        if self.at_op("("):
            self.take()
            while not self.at_op(")"):
                params.append(self._parse_param())
                if self.at_op(","):
                    self.take()
                elif not self.at_op(")"):
                    raise self.error("expected ',' or ')' in the parameter list")
            self.expect_op(")")
        if self.at_op(":"):
            self.take()
        self.expect_end()
        self.pos += 1
        body = self.parse_block("define", line)
        self.close_block("define", line)
        return Define(name.text, tuple(params), body, line.no)

    def _parse_param(self) -> Param:
        pname = self.take()
        if pname.kind != "NAME":
            raise self.error("expected a parameter name", pname)
        sig = None
        if self.at_op("("):
            self.take()
            names = [self.take().text]
            while self.at_op(","):
                self.take()
                names.append(self.take().text)
            self.expect_op(")")
            sig = tuple(names)
        default = None
        if self.at_op("="):
            self.take()
            default = self.parse_or()
        return Param(pname.text, sig, default)

    def parse_if(self, line: Line) -> Stmt:
        branches: list[tuple[Expr, list[Stmt], int]] = []
        orelse: list[Stmt] | None = None
        else_line = 0
        cur, keyword_len = line, 1
        while True:
            self.use(cur)
            self.i = keyword_len
            cond = self.parse_or()
            self.skip_word("then")
            if self.peek() is not None:  # one-line form: if c then statement
                rest = self.t[self.i :]
                self.pos += 1
                self.lines.insert(self.pos, Line(rest, cur.no, rest[0].col))
                stmt = self.parse_statement()
                del self.lines[self.pos - 1]
                self.pos -= 1
                branches.append((cond, [stmt], cur.no))
            else:
                self.pos += 1
                branches.append((cond, self.parse_block("if", line), cur.no))
            if self.pos >= len(self.lines):
                break
            cont = self.lines[self.pos]
            kind = _continuation(cont)
            if kind == "elseif":
                cur = cont
                keyword_len = 2 if cont.toks[0].text.lower() == "else" else 1
                continue
            if kind == "else":
                else_line = cont.no
                self.pos += 1
                orelse = self.parse_block("if", line)
            break
        self.close_block("if", line)
        return If(branches, orelse, line.no, else_line)

    def parse_while(self, line: Line) -> Stmt:
        self.i = 1
        cond = self.parse_or()
        if self.skip_word("is"):
            self.expect_word("true")
        self.skip_word("do")
        self.expect_end()
        self.pos += 1
        body = self.parse_block("while", line)
        self.close_block("while", line)
        return While(cond, body, line.no)

    def parse_for(self, line: Line) -> Stmt:
        self.i = 1
        if self.skip_word("each"):
            var = self.take().text
            self.expect_word("in")
            iterable = self.parse_or()
            self.skip_word("do")
            self.expect_end()
            self.pos += 1
            body = self.parse_block("for", line)
            self.close_block("for", line)
            return ForEach(var, iterable, body, line.no)
        var = self.take().text
        self.expect_word("from")
        start = self.parse_or()
        self.expect_word("to")
        stop = self.parse_or()
        step = self.parse_or() if self.skip_word("step") else None
        self.skip_word("do")
        self.expect_end()
        self.pos += 1
        body = self.parse_block("for", line)
        self.close_block("for", line)
        return For(var, start, stop, step, body, line.no)

    def parse_repeat(self, line: Line) -> Stmt:
        self.i = 1
        if self.peek() is not None:
            count = self.parse_or()
            self.expect_word("times")
            self.expect_end()
            self.pos += 1
            body = self.parse_block("repeat", line)
            self.close_block("repeat", line)
            return RepeatTimes(count, body, line.no)
        self.pos += 1
        body = self.parse_block("repeat", line)
        if self.pos >= len(self.lines) or _continuation(self.lines[self.pos]) != "until":
            raise PseudocodeSyntaxError(f"'repeat' on line {line.no} has no 'until'", line.no)
        until = self.lines[self.pos]
        self.use(until)
        self.i = 1
        cond = self.parse_or()
        self.expect_end()
        self.pos += 1
        return RepeatUntil(body, cond, line.no, until.no)

    # ------------------------------------------------------------------ expressions

    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.at_word("or"):
            line = self.take().line
            left = Binary("or", left, self.parse_and(), line)
        return left

    def parse_and(self) -> Expr:
        left = self.parse_not()
        while self.at_word("and"):
            line = self.take().line
            left = Binary("and", left, self.parse_not(), line)
        return left

    def parse_not(self) -> Expr:
        if self.at_word("not"):
            line = self.take().line
            return Unary("not", self.parse_not(), line)
        return self.parse_compare()

    def parse_compare(self) -> Expr:
        first = self.parse_add()
        ops: list[str] = []
        rest: list[Expr] = []
        while self.at_op(*_COMPARE):
            ops.append(self.take().text)
            rest.append(self.parse_add())
        if not ops:
            return first
        return Compare(first, tuple(ops), tuple(rest), getattr(first, "line", 0))

    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while self.at_op("+", "-"):
            tok = self.take()
            left = Binary(tok.text, left, self.parse_mul(), tok.line)
        return left

    def _starts_factor(self) -> bool:
        tok = self.peek()
        if tok is None:
            return False
        if tok.kind == "NUMBER":
            return True
        if tok.kind == "NAME":
            return tok.text.lower() not in _STOP_WORDS
        if tok.kind == "OP":
            if tok.text == "|":
                return self.abs_depth == 0
            return tok.text in ("(", "√")
        return False

    def parse_mul(self) -> Expr:
        left = self.parse_unary()
        while True:
            tok = self.peek()
            if tok is None:
                break
            if tok.kind == "OP" and tok.text in ("*", "/", "÷", "%"):
                self.take()
                op = "mod" if tok.text == "%" else tok.text
                left = Binary(op, left, self.parse_unary(), tok.line)
            elif tok.kind == "NAME" and tok.text.lower() in ("div", "mod"):
                self.take()
                left = Binary(tok.text.lower(), left, self.parse_unary(), tok.line)
            elif self._starts_factor() and not isinstance(left, Str):
                if isinstance(left, Num) and tok.kind == "NUMBER":
                    break
                left = Binary("*", left, self.parse_unary(), tok.line, implicit=True)
            else:
                break
        return left

    def parse_unary(self) -> Expr:
        tok = self.peek()
        if tok is not None and tok.kind == "OP":
            if tok.text == "-":
                self.take()
                return Unary("-", self.parse_unary(), tok.line)
            if tok.text == "+":
                self.take()
                return self.parse_unary()
            if tok.text == "√":
                self.take()
                return Unary("sqrt", self.parse_pow(), tok.line)
        return self.parse_pow()

    def parse_pow(self) -> Expr:
        base = self.parse_postfix()
        while True:
            tok = self.peek()
            if tok is None:
                break
            if tok.kind == "SUP":
                self.take()
                exp: Expr = Num(tok.text.lstrip("-"), tok.line)
                if tok.text.startswith("-"):
                    exp = Unary("-", exp, tok.line)
                base = Binary("^", base, exp, tok.line)
            elif tok.kind == "OP" and tok.text == "^":
                self.take()
                base = Binary("^", base, self.parse_unary(), tok.line)
            else:
                break
        return base

    def parse_postfix(self) -> Expr:
        expr = self.parse_primary()
        while True:
            tok = self.peek()
            if tok is None or tok.kind != "OP" or tok.text != "[":
                break
            if self.t[self.i - 1].end != tok.col:  # `a [i]` is not an index
                break
            self.take()
            index = self.parse_or()
            self.expect_op("]")
            expr = Index(expr, index, tok.line)
        return expr

    def parse_args(self) -> tuple[Expr, ...]:
        args: list[Expr] = []
        self.expect_op("(")
        while not self.at_op(")"):
            args.append(self.parse_or())
            if self.at_op(","):
                self.take()
            elif not self.at_op(")"):
                raise self.error("expected ',' or ')'")
        self.expect_op(")")
        return tuple(args)

    def parse_primary(self) -> Expr:  # noqa: PLR0911
        tok = self.take()
        if tok.kind == "NUMBER":
            return Num(tok.text.replace("−", "-").replace("ᴇ", "E"), tok.line)
        if tok.kind == "STRING":
            return Str(tok.text, tok.line)
        if tok.kind == "NAME":
            if self.at_op("(") and tok.text not in CONSTANT_NAMES:
                return Call(tok.text, self.parse_args(), tok.line)
            return Name(tok.text, tok.line)
        if tok.kind == "OP":
            if tok.text == "(":
                saved, self.abs_depth = self.abs_depth, 0
                inner = self.parse_or()
                self.abs_depth = saved
                if self.at_op(","):
                    raise self.error("tuples are not supported yet")
                self.expect_op(")")
                return Paren(inner, tok.line)
            if tok.text == "[":
                return self._parse_bracket(tok)
            if tok.text == "|":
                self.abs_depth += 1
                inner = self.parse_or()
                self.expect_op("|")
                self.abs_depth -= 1
                return Unary("abs", inner, tok.line)
        raise self.error(f"unexpected {tok.raw or tok.text!r}", tok)

    def _parse_bracket(self, tok: Token) -> Expr:
        """`[]`, `[x]` and `[1, 2]` are lists; only `( )` groups (decision 0020 item 3)."""
        saved, self.abs_depth = self.abs_depth, 0
        items: list[Expr] = []
        while not self.at_op("]"):
            items.append(self.parse_or())
            if self.at_op(","):
                self.take()
            elif not self.at_op("]"):
                raise self.error("expected ',' or ']'")
        self.expect_op("]")
        self.abs_depth = saved
        return ListLit(tuple(items), tok.line)


def parse(source: str) -> Program:
    return Parser(source).parse_program()
