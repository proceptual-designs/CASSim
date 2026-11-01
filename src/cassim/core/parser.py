"""Pratt parser: tokens to AST.

Precedence comes from the EOS table in the Reference Guide (see `Prec`). The grammar choices the
guide does not settle are recorded in docs/decisions/0007-parser-grammar.md.
"""

from cassim.core.ast import (
    BINARY_PREC,
    COMPARE_OPS,
    POSTFIX_OPS,
    RIGHT_ASSOCIATIVE,
    UNARY_OPERAND_PREC,
    Assign,
    Binary,
    Call,
    Command,
    Compare,
    Convert,
    Define,
    Dms,
    Expr,
    Index,
    Line,
    ListLit,
    Matrix,
    Name,
    Number,
    Postfix,
    Prec,
    Stmt,
    Store,
    String,
    Unary,
)
from cassim.core.errors import (
    MISSING_CLOSE_BRACE,
    MISSING_CLOSE_BRACKET,
    MISSING_CLOSE_PAREN,
    MISSING_OPEN_PAREN,
    SYNTAX,
    TISyntaxError,
)
from cassim.core.lexer import Kind, Token, tokenize

# A budget on how deep a tree may be, so that the parser and every later recursive walk stay well
# inside Python's stack, including under Pyodide. Nesting costs more than one more term in a chain
# because each level of nesting takes several parser frames. Long lists are wide, not deep, so
# they are not limited. Allows about 80 levels of parentheses, or a sum of about 240 terms.
MAX_DEPTH = 240
_NESTING_COST = 3

# Statements written without parentheses. Control flow (If, For, ...) belongs to cassim.basic.
_COMMAND_NAMES = """
    ANOVA ANOVA2way ClearAZ ClrErr CopyVar CubicReg DelVar Disp DispAt ExpReg Fill
    FiveNumSummary FTest_2Samp LinRegBx LinRegMx LinRegtIntervals LinRegtTest LnReg Local
    Lock Logistic LogisticD LU MedMed MultReg MultRegIntervals MultRegTests OneVar PassErr
    PowerReg QR QuadReg QuartReg RandSeed RefreshProbeVars Request RequestStr SinReg SortA
    SortD Text tInterval tInterval_2Samp tTest tTest_2Samp TwoVar unLock Wait zInterval
    zInterval_1Prop zInterval_2Prop zInterval_2Samp zTest zTest_1Prop zTest_2Prop
    zTest_2Samp χ²2way χ²GOF
"""
COMMANDS: dict[str, str] = {name.casefold(): name for name in _COMMAND_NAMES.split()}
_DEFINE = "define"
_VISIBILITY = {"libpub": "LibPub", "libpriv": "LibPriv"}
_NEEDS_PARENS = frozenset("√∫∏∑")
_PRIMARY_OPENERS = frozenset({"(", "{", "[", "#"})
_ASSIGNABLE = (Name, Call, Index)
_OPERATORS = POSTFIX_OPS | COMPARE_OPS | BINARY_PREC.keys() | {"[", "▶"}
_LITERALS: dict[Kind, type[Number | Dms | String | Name]] = {
    Kind.NUMBER: Number,
    Kind.DMS: Dms,
    Kind.STRING: String,
    Kind.NAME: Name,
}


def _infix_prec(op: str) -> int:
    if op == "▶":
        return Prec.CONVERT
    return Prec.COMPARE if op in COMPARE_OPS else BINARY_PREC[op]


class _Parser:
    def __init__(self, text: str) -> None:
        self._tokens = tokenize(text)
        self._i = 0
        self._depth = 0
        # True directly inside [ ], where a space may separate elements as in `[1 2 3]`.
        self._in_row = False

    @property
    def _tok(self) -> Token:
        return self._tokens[self._i]

    def _advance(self) -> Token:
        token = self._tok
        self._i += 1
        return token

    def _at(self, op: str) -> bool:
        return self._tok.kind is Kind.OP and self._tok.text == op

    def _accept(self, op: str) -> bool:
        found = self._at(op)
        if found:
            self._i += 1
        return found

    def _expect(self, op: str, code: int = SYNTAX) -> None:
        if not self._accept(op):
            raise TISyntaxError(code, self._tok.pos)

    def _syntax_error(self) -> TISyntaxError:
        return TISyntaxError(SYNTAX, self._tok.pos)

    def _trailing_error(self) -> TISyntaxError:
        """Report text left over after a complete statement."""
        code = MISSING_OPEN_PAREN if self._at(")") else SYNTAX
        return TISyntaxError(code, self._tok.pos)

    # Statements

    def line(self) -> Line:
        statements: list[Stmt] = []
        while self._tok.kind is not Kind.EOF:
            if self._accept(":"):
                continue
            statements.append(self._statement())
            if self._tok.kind is not Kind.EOF and not self._at(":"):
                raise self._trailing_error()
        return Line(tuple(statements))

    def only_expression(self) -> Expr:
        expr = self._expr(0)
        if self._tok.kind is not Kind.EOF:
            raise self._trailing_error()
        return expr

    def _statement(self) -> Stmt:
        token = self._tok
        if token.kind is Kind.NAME:
            word = token.text.casefold()
            if word == _DEFINE:
                return self._define()
            if word in COMMANDS:
                return self._command()
        expr = self._expr(0)
        if self._accept(":="):
            self._check_target(expr, token)
            return Assign(expr, self._expr(0))
        if self._accept("→"):
            at = self._tok
            target = self._expr(Prec.POST)
            self._check_target(target, at)
            return Store(expr, target)
        return expr

    def _check_target(self, target: Expr, token: Token) -> None:
        if not isinstance(target, _ASSIGNABLE):
            raise TISyntaxError(SYNTAX, token.pos)

    def _define(self) -> Define:
        self._advance()
        visibility = None
        if self._tok.kind is Kind.NAME and self._tok.text.casefold() in _VISIBILITY:
            visibility = _VISIBILITY[self._advance().text.casefold()]
        at = self._tok
        target = self._expr(Prec.POST)
        self._check_target(target, at)
        self._expect("=")
        return Define(target, self._expr(0), visibility)

    def _command(self) -> Command:
        name = COMMANDS[self._advance().text.casefold()]
        args: list[Expr] = []
        if self._tok.kind is not Kind.EOF and not self._at(":"):
            args.append(self._expr(0))
            while self._accept(","):
                args.append(self._expr(0))
        return Command(name, tuple(args))

    # Expressions

    def _expr(self, minimum: int) -> Expr:
        start = self._depth
        self._deepen(_NESTING_COST)
        left = self._prefix()
        while (extended := self._extend(left, minimum)) is not None:
            left = extended
            self._deepen(1)
        self._depth = start
        return left

    def _deepen(self, cost: int) -> None:
        self._depth += cost
        if self._depth > MAX_DEPTH:
            raise TISyntaxError(SYNTAX, self._tok.pos, "Expression is too complex")

    def _prefix(self) -> Expr:
        token = self._tok
        if token.kind is Kind.OP and token.text in UNARY_OPERAND_PREC:
            self._advance()
            return Unary(token.text, self._expr(UNARY_OPERAND_PREC[token.text]))
        return self._primary()

    def _extend(self, left: Expr, minimum: int) -> Expr | None:
        """Absorb one more operator into `left`, or return None if `left` is complete."""
        if self._starts_next_element(self._tok):
            return None
        if self._at_operator():
            return self._operator(left, minimum)
        return self._implicit_product(left, minimum)

    def _at_operator(self) -> bool:
        token = self._tok
        if token.kind is not Kind.OP:
            return False
        if token.text == "[":  # after a number, `[` starts a factor: `2[1,2]`
            return self._tokens[self._i - 1].kind is not Kind.NUMBER
        return token.text in _OPERATORS

    def _operator(self, left: Expr, minimum: int) -> Expr | None:
        op = self._tok.text
        if op in POSTFIX_OPS:
            self._advance()
            return Postfix(op, left)
        if op == "[":
            return self._index(left)
        if _infix_prec(op) < minimum:
            return None
        if op == "▶":
            return self._convert(left)
        return self._compare(left) if op in COMPARE_OPS else self._binary(left)

    def _binary(self, left: Expr) -> Binary:
        op = self._advance().text
        prec = BINARY_PREC[op]
        return Binary(op, left, self._expr(prec if op in RIGHT_ASSOCIATIVE else prec + 1))

    def _compare(self, first: Expr) -> Compare:
        rest: list[tuple[str, Expr]] = []
        while self._tok.kind is Kind.OP and self._tok.text in COMPARE_OPS:
            op = self._advance().text
            rest.append((op, self._expr(Prec.COMPARE + 1)))
        return Compare(first, tuple(rest))

    def _convert(self, value: Expr) -> Convert:
        self._advance()
        if self._tok.kind is not Kind.NAME:
            raise self._syntax_error()
        name = self._advance().text
        if self._accept("("):
            return Convert(value, Call(name, self._items(")", MISSING_CLOSE_PAREN)))
        return Convert(value, Name(name))

    def _index(self, base: Expr) -> Index:
        self._advance()
        subscripts = self._items("]", MISSING_CLOSE_BRACKET)
        if not subscripts:
            raise self._syntax_error()
        return Index(base, subscripts)

    def _implicit_product(self, left: Expr, minimum: int) -> Expr | None:
        if minimum > Prec.MUL or not self._starts_factor(self._tok):
            return None
        return Binary("*", left, self._expr(Prec.MUL + 1))

    def _starts_factor(self, token: Token) -> bool:
        if token.kind is Kind.NUMBER:  # `2 3` is an error, but `x 3` and `(x)3` are products
            return self._tokens[self._i - 1].kind is not Kind.NUMBER
        if token.kind in (Kind.DMS, Kind.NAME):
            return True
        return token.kind is Kind.OP and token.text in _PRIMARY_OPENERS

    def _starts_next_element(self, token: Token) -> bool:
        """True at a space-separated element, as in the display form `[√(2) ∠π/4 1]`."""
        if not (self._in_row and token.space_before):
            return False
        return token.kind in (Kind.NUMBER, Kind.DMS, Kind.STRING, Kind.NAME) or (
            token.kind is Kind.OP and (token.text in _PRIMARY_OPENERS or token.text == "∠")
        )

    def _primary(self) -> Expr:
        token = self._tok
        if token.kind is Kind.OP and token.text in _PRIMARY_OPENERS:
            self._advance()
            return self._bracketed(token.text)
        if token.kind not in _LITERALS:
            raise self._syntax_error()
        self._advance()
        return self._name(token) if token.kind is Kind.NAME else _LITERALS[token.kind](token.text)

    def _name(self, token: Token) -> Expr:
        word = token.text.casefold()
        if word in COMMANDS or word == _DEFINE:
            raise TISyntaxError(SYNTAX, token.pos)
        call_allowed = not (self._in_row and self._tok.space_before)
        if call_allowed and self._accept("("):
            return Call(token.text, self._items(")", MISSING_CLOSE_PAREN))
        if token.text in _NEEDS_PARENS:
            raise TISyntaxError(MISSING_OPEN_PAREN, self._tok.pos)
        return Name(token.text)

    def _bracketed(self, opener: str) -> Expr:
        if opener == "#":
            self._deepen(_NESTING_COST)
            operand = self._primary()
            self._depth -= _NESTING_COST
            return Unary("#", operand)
        if opener == "{":
            return ListLit(self._items("}", MISSING_CLOSE_BRACE))
        if opener == "[":
            return self._matrix()
        in_row, self._in_row = self._in_row, False
        expr = self._expr(0)
        self._expect(")", MISSING_CLOSE_PAREN)
        self._in_row = in_row
        return expr

    def _items(self, closer: str, code: int) -> tuple[Expr, ...]:
        """Parse comma-separated expressions up to `closer`, which may come straight away."""
        in_row, self._in_row = self._in_row, False
        items: list[Expr] = []
        if not self._at(closer):
            items.append(self._expr(0))
            while self._accept(","):
                items.append(self._expr(0))
        self._expect(closer, code)
        self._in_row = in_row
        return tuple(items)

    def _matrix(self) -> Matrix:
        in_row, self._in_row = self._in_row, True
        rows: list[tuple[Expr, ...]] = []
        row: list[Expr] = [self._expr(0)]
        while not self._accept("]"):
            if self._accept(";"):
                rows.append(tuple(row))
                row = [self._expr(0)]
                continue
            if not self._accept(",") and not self._starts_next_element(self._tok):
                raise TISyntaxError(MISSING_CLOSE_BRACKET, self._tok.pos)
            row.append(self._expr(0))
        rows.append(tuple(row))
        self._in_row = in_row
        return _flatten_nested(Matrix(tuple(rows)))


def _flatten_nested(matrix: Matrix) -> Matrix:
    """Turn the nested spelling `[[1,2],[3,4]]` into `[1,2;3,4]`."""
    if len(matrix.rows) != 1:
        return matrix
    inner: list[tuple[Expr, ...]] = []
    for element in matrix.rows[0]:
        if not isinstance(element, Matrix) or len(element.rows) != 1:
            return matrix
        inner.append(element.rows[0])
    return Matrix(tuple(inner))


def parse(text: str) -> Line:
    """Parse one entry line. Raises TISyntaxError if it cannot be read."""
    return _Parser(text).line()


def parse_expression(text: str) -> Expr:
    """Parse text that must be a single expression, such as a displayed result."""
    return _Parser(text).only_expression()
