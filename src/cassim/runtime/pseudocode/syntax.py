"""The pseudocode syntax file: model, validation and built-in presets (SRS FR-SYN-001 to -009).

A syntax file is *data* (YAML or JSON text, or a dict): no code, no regular expressions. Each
construct may be spelled several ways and each spelling is `ok` (accepted), `warn` (accepted with
a warning) or `no` (rejected). Optional tokens are `required`, `optional` or `forbidden`. A file
is laid over the built-in default, so a partial file is valid and any entry it leaves out keeps
the default.

The lexer and parser read a compiled `Syntax`; they never look at the raw dict.
"""

import copy
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

try:
    import yaml
except ImportError:  # the app UI has no YAML package; syntax-file loading is unavailable there
    yaml = None

type Mode = Literal["ok", "warn", "no"]
type Policy = Literal["required", "optional", "forbidden"]

MODES = ("ok", "warn", "no")
POLICIES = ("required", "optional", "forbidden")
MAX_FILE_CHARS = 20_000  # NFR-SEC-003: syntax files are size-limited on import
MAX_PHRASE_WORDS = 3

# Words the grammar itself uses; a configurable keyword may not reuse them.
RESERVED: frozenset[str] = frozenset(
    {
        "if", "then", "else", "elseif", "elif", "while", "do", "for", "each", "from", "to", "step",
        "in", "repeat", "times", "until", "append", "is", "true", "and", "or", "not", "mod", "div",
    }
)  # fmt: skip

_OP_CATEGORIES = (
    "minus", "times", "divide", "mod", "div", "power", "equal", "not_equal", "less_equal",
    "greater_equal", "and", "or", "not", "sqrt_symbol",
)  # fmt: skip
_BLOCK_TERMINATORS = ("if", "while", "for", "repeat_times", "define")
_KEYWORD_SETS = (
    ("define", "keywords"), ("print", "keywords"), ("input", "keywords"),
    ("return", "keywords"), ("break", "keywords"),
)  # fmt: skip
_EMIT_CHOICES = {
    "comment": ("//", "#"),
    "assign": ("←", "<-", ":=", "="),
    "times": ("×", "*", "·"),
    "divide": ("÷", "/"),
    "if_then": ("always", "never"),
    "while_do": ("always", "never"),
    "for_do": ("always", "never"),
    "print_parentheses": ("always", "never"),
}
_ASCII_WORDS = frozenset({"and", "or", "not", "mod", "div"})


DEFAULT_DATA: dict[str, Any] = {
    "syntax_version": 0,
    "name": "CASSim default (tolerant)",
    "based_on": None,
    "names": {"split_products": False},
    "lexical": {
        "keywords_case_insensitive": True,
        "identifiers_case_sensitive": True,
        "comments": {"//": "ok", "#": "ok"},
        "minus": {"-": "ok", "−": "ok", "–": "ok"},
        "times": {"×": "ok", "*": "ok", "·": "ok"},
        "divide": {"÷": "ok", "/": "ok"},
        "mod": {"mod": "ok", "MOD": "ok", "%": "warn"},
        "div": {"div": "ok", "DIV": "ok"},
        "sqrt_symbol": {"√": "ok"},
        "power": {"^": "ok", "**": "ok", "superscript_digits": "ok"},
        "equal": {"=": "ok", "==": "ok"},
        "not_equal": {"≠": "ok", "<>": "ok", "!=": "ok"},
        "less_equal": {"≤": "ok", "<=": "ok", "⩽": "ok"},
        "greater_equal": {"≥": "ok", ">=": "ok", "⩾": "ok"},
        "and": {"and": "ok", "∧": "ok"},
        "or": {"or": "ok", "∨": "ok"},
        "not": {"not": "ok", "¬": "ok"},
        "grouping": {"( )": "ok"},
        "abs_bars": "ok",
        "string_quotes": {"straight": "ok", "curly": "ok"},
    },
    "symbols": {
        "assign": {"ascii": ["<-", ":="], "unicode": ["←"]},
        "times": {"ascii": ["*"], "unicode": ["×", "·"]},
        "divide": {"ascii": ["/"], "unicode": ["÷"]},
        "less_equal": {"ascii": ["<="], "unicode": ["≤", "⩽"]},
        "greater_equal": {"ascii": [">="], "unicode": ["≥", "⩾"]},
        "not_equal": {"ascii": ["!=", "<>"], "unicode": ["≠"]},
        "sqrt": {"ascii": ["sqrt("], "unicode": ["√(", "√"]},
        "euler": {"ascii": ["@e"], "unicode": ["ⅇ"]},
        "pi": {"ascii": ["pi", "@pi"], "unicode": ["π"]},
        "infinity": {"ascii": ["inf"], "unicode": ["∞"]},
        "abs": {"ascii": ["abs("], "unicode": ["|x|"]},
        "power": {"ascii": ["^", "**"], "unicode": ["superscript integers"]},
        "and_or_not": {"ascii": ["and", "or", "not"], "unicode": ["∧", "∨", "¬"]},
        "convert_button_default": "unicode",
    },
    "palette": {
        "groups": {
            "arithmetic": ["×", "÷", "±", "≤", "≥", "≠", "←", "≈"],
            "powers_roots": ["²", "³", "ⁿ", "⁻¹", "√", "^", "π", "ⅇ", "∞"],
            "logic": ["∧", "∨", "¬"],
            "brackets": ["|x|", "( )", "[ ]"],
            "greek": ["θ", "α", "β", "δ", "λ", "μ", "σ"],
        },
        # Shown but not insertable: the lexer does not read them yet (± and ≈ are unexpected
        # characters; ⁿ is read as a name, not a power). Enable when the language takes them.
        "disabled": ["±", "≈", "ⁿ"],
        "templates": ["if", "for", "while", "repeat", "define"],
    },
    "constructs": {
        "assign": {"spellings": {"←": "ok", "<-": "ok", ":=": "ok", "=": "warn"}},
        "input": {"keywords": {"input": "ok"}},
        "print": {
            "end": "newline",
            "keywords": {"print": "ok", "output": "ok"},
            "parentheses": "optional",
            "item_separator": {",": "ok", "juxtaposed_after_string_literal": "warn"},
        },
        "if": {
            "then": "optional",
            "else_if": {"else if": "ok", "elseif": "ok", "elif": "ok"},
            "terminators": {"end if": "ok", "endif": "ok", "end": "no"},
        },
        "while": {
            "do": "optional",
            "is_true": "ok",
            "terminators": {"end while": "ok", "endwhile": "ok", "wend": "ok", "end": "no"},
        },
        "for": {
            "range_words": {"from": "required", "to": "required", "step": "ok"},
            "do": "optional",
            "terminators": {
                "end for": "ok", "endfor": "ok", "next": "ok", "next <variable>": "ok", "end": "no",
            },
        },
        "repeat_times": {
            "terminators": {"end repeat": "ok", "endrepeat": "ok", "next": "no", "end": "no"}
        },
        "repeat_until": {"until": "required"},
        "define": {
            "keywords": {"define": "ok", "function": "ok"},
            "colon_after_header": "optional",
            "terminators": {
                "end": "ok", "end define": "ok", "end function": "ok", "dedent": "ok",
            },
        },
        "function_by_assignment": "ok",
        "default_parameters": "ok",
        "return": {"keywords": {"return": "ok"}},
        "break": {"keywords": {"break": "ok"}},
    },
    "lists": {"index_base": 1},
    "structure": {"missing_inner_end": "warn", "surplus_end": "no"},
    "emit": {
        "keyword_case": "lower",
        "indent": 2,
        "comment": "//",
        "assign": "←",
        "times": "×",
        "divide": "÷",
        "if_then": "always",
        "while_do": "always",
        "for_do": "never",
        "terminators": {
            "if": "end if", "while": "end while", "for": "end for", "repeat": "end repeat",
            "define": "end",
        },
        "print_parentheses": "never",
        "symbols": "unicode",
    },
}  # fmt: skip


class SyntaxFileError(ValueError):
    """A syntax file is not valid. `problems` names each entry at fault (FR-SYN-004)."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


def _merge(base: dict[str, Any], over: Mapping[str, Any]) -> dict[str, Any]:
    """`over` laid on `base`: tables merge key by key, anything else is replaced."""
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(out.get(key), dict) and isinstance(value, Mapping):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


# --------------------------------------------------------------------------- the compiled form


@dataclass(frozen=True, slots=True)
class Syntax:
    """What the lexer and parser consult. Build one with `load_syntax` or take a `PRESETS` entry."""

    name: str
    data: dict[str, Any] = field(repr=False, compare=False)
    case_insensitive: bool
    comments: dict[str, Mode]
    op_modes: dict[str, Mode]  # operator spelling -> mode (assign spellings included)
    word_modes: dict[str, Mode]  # and or not mod div (lower case)
    superscripts: Mode
    quotes: dict[str, Mode]
    keywords: dict[str, dict[str, Mode]]  # define print input return break: word -> mode
    then: Policy
    else_if: dict[tuple[str, ...], Mode]
    while_do: Policy
    for_do: Policy
    is_true: Mode
    for_step: Mode
    print_parens: Policy
    juxtaposed: Mode
    define_colon: Policy
    closers: dict[tuple[str, ...], tuple[str, Mode]]  # words -> (block kind, mode)
    dedent_closes_define: Mode
    missing_inner_end: Mode
    surplus_end: Mode
    func_assign: Mode
    default_params: Mode
    eq_assign: Mode  # `x = 5` as an assignment
    split_products: bool

    def kw(self, text: str) -> str:
        """A keyword as the grammar compares it."""
        return text.lower() if self.case_insensitive else text

    def word_mode(self, word: str) -> Mode:
        return self.word_modes.get(word.lower(), "ok")

    def keyword_collisions(self, names: Iterable[str]) -> list[str]:
        """Names a program uses that this syntax reserves (FR-SYN-004)."""
        reserved: set[str] = set(RESERVED)
        for words in self.keywords.values():
            reserved |= {w for w, m in words.items() if m != "no"}
        return sorted({n for n in names if self.kw(n) in reserved})


def _best(modes: Iterable[Mode]) -> Mode:
    seen = set(modes)
    return "ok" if "ok" in seen else "warn" if "warn" in seen else "no"


def _compile_closers(
    con: dict[str, Any], norm: Callable[[str], str]
) -> dict[tuple[str, ...], tuple[str, Mode]]:
    """Closing spellings -> (block kind, mode); bare `end` goes to its one construct."""
    closers: dict[tuple[str, ...], tuple[str, Mode]] = {}
    bare_end_kind = "define"
    for kind in _BLOCK_TERMINATORS:
        for spelling, mode in con[kind]["terminators"].items():
            if spelling == "end" and mode != "no":
                bare_end_kind = kind
    for kind in _BLOCK_TERMINATORS:
        block = "repeat" if kind == "repeat_times" else kind
        for spelling, mode in con[kind]["terminators"].items():
            if spelling == "dedent":
                continue
            words = tuple(norm(w) for w in spelling.split())
            if words == ("end",):
                closers[words] = (bare_end_kind, mode if kind == bare_end_kind else "no")
            elif words not in closers or closers[words][1] == "no":
                closers[words] = (block, mode)
    return closers


def _compile(d: dict[str, Any]) -> Syntax:
    lex, con = d["lexical"], d["constructs"]
    ci = bool(lex["keywords_case_insensitive"])
    op_modes: dict[str, Mode] = {}
    for cat in _OP_CATEGORIES:
        for spelling, mode in lex[cat].items():
            if spelling != "superscript_digits" and not spelling.isalpha():
                op_modes[spelling] = mode
    for spelling, mode in con["assign"]["spellings"].items():
        if spelling != "=":  # `=` is also the comparison; the parser decides which it is
            op_modes[spelling] = mode
    word_modes: dict[str, Mode] = {}
    for cat in ("and", "or", "not", "mod", "div"):
        spellings = [(s, m) for s, m in lex[cat].items() if s.isalpha()]
        if spellings:
            word_modes[cat] = _best(m for _, m in spellings)
    norm = str.lower if ci else str
    closers = _compile_closers(con, norm)
    structure = d["structure"]
    return Syntax(
        name=str(d["name"]),
        data=d,
        case_insensitive=ci,
        comments=dict(lex["comments"]),
        op_modes=op_modes,
        word_modes=word_modes,
        superscripts=lex["power"].get("superscript_digits", "no"),
        quotes=dict(lex["string_quotes"]),
        keywords={k: {norm(w): m for w, m in con[k]["keywords"].items()} for k, _ in _KEYWORD_SETS},
        then=con["if"]["then"],
        else_if={tuple(norm(w) for w in s.split()): m for s, m in con["if"]["else_if"].items()},
        while_do=con["while"]["do"],
        for_do=con["for"]["do"],
        is_true=con["while"]["is_true"],
        for_step=con["for"]["range_words"]["step"],
        print_parens=con["print"]["parentheses"],
        juxtaposed=con["print"]["item_separator"]["juxtaposed_after_string_literal"],
        define_colon=con["define"]["colon_after_header"],
        closers=closers,
        dedent_closes_define=con["define"]["terminators"].get("dedent", "no"),
        missing_inner_end=structure["missing_inner_end"],
        surplus_end=structure["surplus_end"],
        func_assign=con["function_by_assignment"],
        default_params=con["default_parameters"],
        eq_assign=con["assign"]["spellings"]["="],
        split_products=bool(d["names"]["split_products"]),
    )


# --------------------------------------------------------------------------- validation


def _check_keys(data: object, template: object, path: str, problems: list[str]) -> None:
    """Reject entries the schema does not know (a typo must not silently do nothing)."""
    if not isinstance(template, dict):
        return
    if not isinstance(data, dict):
        problems.append(f"{path}: expected a table of entries")
        return
    open_keys = path in _OPEN_TABLES
    for key, value in data.items():
        if key not in template and not open_keys:
            problems.append(f"{path}.{key}: unknown entry" if path else f"{key}: unknown entry")
        elif key in template:
            _check_keys(value, template[key], f"{path}.{key}" if path else key, problems)


# Tables whose keys are spellings the file may add to (keywords, terminators, else-if spellings).
_OPEN_TABLES = {
    f"constructs.{c}.{t}"
    for c, t in (
        ("define", "keywords"), ("print", "keywords"), ("input", "keywords"),
        ("return", "keywords"), ("break", "keywords"), ("if", "terminators"),
        ("while", "terminators"), ("for", "terminators"), ("repeat_times", "terminators"),
        ("define", "terminators"), ("if", "else_if"),
    )
} | {"symbols", "palette.groups", "emit.terminators"}  # fmt: skip


def _check_modes(d: dict[str, Any], problems: list[str]) -> None:  # noqa: PLR0912
    lex, con = d["lexical"], d["constructs"]

    def mode(path: str, value: object) -> None:
        if value not in MODES:
            problems.append(f"{path}: must be one of ok, warn, no (got {value!r})")

    def policy(path: str, value: object) -> None:
        if value not in POLICIES:
            problems.append(f"{path}: must be one of required, optional, forbidden")

    known_ops = {cat: set(DEFAULT_DATA["lexical"][cat]) for cat in (*_OP_CATEGORIES, "comments")}
    for cat, allowed in known_ops.items():
        for spelling, value in lex[cat].items():
            if spelling not in allowed:
                problems.append(f"lexical.{cat}.{spelling}: the engine has no such spelling")
            mode(f"lexical.{cat}.{spelling}", value)
    for spelling, value in lex["string_quotes"].items():
        mode(f"lexical.string_quotes.{spelling}", value)
    for spelling, value in con["assign"]["spellings"].items():
        if spelling not in DEFAULT_DATA["constructs"]["assign"]["spellings"]:
            problems.append(
                f"constructs.assign.spellings.{spelling}: the engine has no such spelling"
            )
        mode(f"constructs.assign.spellings.{spelling}", value)
    policy("constructs.if.then", con["if"]["then"])
    policy("constructs.while.do", con["while"]["do"])
    policy("constructs.for.do", con["for"]["do"])
    policy("constructs.print.parentheses", con["print"]["parentheses"])
    policy("constructs.define.colon_after_header", con["define"]["colon_after_header"])
    mode("constructs.while.is_true", con["while"]["is_true"])
    mode("constructs.for.range_words.step", con["for"]["range_words"]["step"])
    mode("constructs.print.item_separator.juxtaposed_after_string_literal",
         con["print"]["item_separator"]["juxtaposed_after_string_literal"])  # fmt: skip
    mode("constructs.function_by_assignment", con["function_by_assignment"])
    mode("constructs.default_parameters", con["default_parameters"])
    mode("structure.missing_inner_end", d["structure"]["missing_inner_end"])
    mode("structure.surplus_end", d["structure"]["surplus_end"])
    for kind in _BLOCK_TERMINATORS:
        for spelling, value in con[kind]["terminators"].items():
            mode(f"constructs.{kind}.terminators.{spelling}", value)
    for kind, _ in _KEYWORD_SETS:
        for spelling, value in con[kind]["keywords"].items():
            mode(f"constructs.{kind}.keywords.{spelling}", value)
    for spelling, value in con["if"]["else_if"].items():
        mode(f"constructs.if.else_if.{spelling}", value)
    if lex["keywords_case_insensitive"] not in (True, False):
        problems.append("lexical.keywords_case_insensitive: must be true or false")
    if d["names"]["split_products"] not in (True, False):
        problems.append("names.split_products: must be true or false")
    emit = d["emit"]
    if emit["keyword_case"] not in ("lower", "UPPER", "Capitalised"):
        problems.append("emit.keyword_case: must be lower, UPPER or Capitalised")
    if emit["symbols"] not in ("unicode", "ascii", "keep"):
        problems.append("emit.symbols: must be unicode, ascii or keep")
    if (
        not isinstance(emit["indent"], int)
        or isinstance(emit["indent"], bool)
        or not (
            1 <= emit["indent"] <= 8  # noqa: PLR2004
        )
    ):
        problems.append("emit.indent: must be a whole number from 1 to 8")
    for key, allowed in _EMIT_CHOICES.items():
        if emit[key] not in allowed:
            problems.append(f"emit.{key}: must be one of {', '.join(allowed)}")
    for key in ("if", "while", "for", "repeat", "define"):
        value = emit["terminators"].get(key)
        if value is not None and not (isinstance(value, str) and value.strip()):
            problems.append(f"emit.terminators.{key}: must be a spelling such as 'end {key}'")


def _check_phrase(path: str, spelling: str, problems: list[str]) -> None:
    words = spelling.replace("<variable>", "v").split()
    if not words or len(words) > MAX_PHRASE_WORDS or not all(w.isalpha() for w in words):
        problems.append(f"{path}.{spelling}: a spelling is one to three plain words")


def _check_grammar(d: dict[str, Any], problems: list[str]) -> None:  # noqa: PLR0912
    """Contradictions and ambiguity (FR-SYN-004). Each message names the entry at fault."""
    con = d["constructs"]
    if not any(m != "no" for m in con["assign"]["spellings"].values()):
        problems.append("constructs.assign.spellings: no spelling is left for assignment")
    for kind, _ in _KEYWORD_SETS:
        if not any(m != "no" for m in con[kind]["keywords"].values()):
            problems.append(f"constructs.{kind}.keywords: no keyword is left for {kind}")
        for spelling in con[kind]["keywords"]:
            _check_phrase(f"constructs.{kind}.keywords", spelling, problems)
            if " " in spelling:
                problems.append(f"constructs.{kind}.keywords.{spelling}: a keyword is one word")
            elif spelling.lower() in RESERVED:
                problems.append(f"constructs.{kind}.keywords.{spelling}: reserved by the grammar")
    seen: dict[str, str] = {}
    for kind, _ in _KEYWORD_SETS:
        for spelling, mode in con[kind]["keywords"].items():
            key = spelling.lower()
            if mode != "no" and key in seen and seen[key] != kind:
                problems.append(
                    f"constructs.{kind}.keywords.{spelling}: also a keyword for {seen[key]}"
                )
            elif mode != "no":
                seen[key] = kind
    for kind in _BLOCK_TERMINATORS:
        terms = con[kind]["terminators"]
        for spelling in terms:
            if spelling != "dedent":
                _check_phrase(f"constructs.{kind}.terminators", spelling, problems)
        if not any(m != "no" for m in terms.values()):
            problems.append(f"constructs.{kind}.terminators: no way left to end a {kind} block")
    owners: dict[tuple[str, ...], str] = {}
    for kind in _BLOCK_TERMINATORS:
        for spelling, mode in con[kind]["terminators"].items():
            if spelling == "dedent" or mode == "no":
                continue
            words = tuple(spelling.lower().split())
            if words in owners and owners[words] != kind:
                what = "a bare 'end'" if words == ("end",) else f"'{spelling}'"
                problems.append(
                    f"constructs.{kind}.terminators.{spelling}: {what} would end both"
                    f" {owners[words]} and {kind}; only one construct may accept it"
                )
            else:
                owners[words] = kind
    spellings: set[tuple[str, ...]] = set()
    for spelling, mode in con["if"]["else_if"].items():
        _check_phrase("constructs.if.else_if", spelling, problems)
        if mode != "no":
            spellings.add(tuple(spelling.lower().split()))
    if con["define"]["terminators"].get("dedent", "no") == "no" and not any(
        m != "no" for s, m in con["define"]["terminators"].items() if s != "dedent"
    ):
        problems.append("constructs.define.terminators: no way left to end a function")


def validate(data: Mapping[str, Any]) -> list[str]:
    """Problems with a syntax dict, empty when it is valid. Each names the entry at fault."""
    problems: list[str] = []
    _check_keys(data, DEFAULT_DATA, "", problems)
    if problems:
        return problems
    merged = _merge(DEFAULT_DATA, data)
    _check_modes(merged, problems)
    if not problems:
        _check_grammar(merged, problems)
    return problems


# --------------------------------------------------------------------------- loading


def load_syntax(data: Mapping[str, Any] | None = None) -> Syntax:
    """Compile a syntax dict (laid over the default). Raises `SyntaxFileError` if it is invalid."""
    overlay: Mapping[str, Any] = data or {}
    based_on = overlay.get("based_on")
    if based_on is not None:
        if based_on not in PRESET_DATA:
            raise SyntaxFileError([f"based_on: no preset called {based_on!r}"])
        overlay = _merge(
            PRESET_DATA[based_on], {k: v for k, v in overlay.items() if k != "based_on"}
        )
        overlay["based_on"] = based_on
    problems = validate(overlay)
    if problems:
        raise SyntaxFileError(problems)
    return _compile(_merge(DEFAULT_DATA, overlay))


if yaml is not None:

    class _DataLoader(yaml.SafeLoader):
        """Safe YAML where only `true` and `false` are booleans."""

    _DataLoader.yaml_implicit_resolvers = {
        first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:bool"]
        for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    _DataLoader.add_implicit_resolver(
        "tag:yaml.org,2002:bool",
        re.compile(r"^(?:true|false)$"),
        "tf",
    )
else:

    class _DataLoader:
        pass


def parse_text(text: str) -> object:
    """YAML or JSON text as plain data (no tags, no code)."""
    if yaml is None:
        raise SyntaxFileError(["file: YAML support is unavailable"])
    return yaml.load(text, Loader=_DataLoader)  # ty: ignore[invalid-argument-type]


def load_syntax_text(text: str) -> Syntax:
    """Parse YAML or JSON text (data only, size-limited) and compile it (FR-SYN-009)."""
    if len(text) > MAX_FILE_CHARS:
        raise SyntaxFileError([f"file: larger than {MAX_FILE_CHARS} characters"])
    if yaml is None:
        raw = parse_text(text)
    else:
        try:
            raw = parse_text(text)
        except yaml.YAMLError as e:
            raise SyntaxFileError([f"file: not valid YAML or JSON ({type(e).__name__})"]) from e
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise SyntaxFileError(["file: expected a table of entries"])
    return load_syntax(raw)


def load_or_default(text: str) -> tuple[Syntax, list[str]]:
    """An invalid file falls back to the default with the reasons (FR-SYN-003)."""
    try:
        return load_syntax_text(text), []
    except SyntaxFileError as e:
        return DEFAULT, e.problems


# --------------------------------------------------------------------------- built-in presets

_VCAA: dict[str, Any] = {
    "name": "VCAA",
    "based_on": None,
    "names": {"split_products": True},  # exam text writes `ax³ + bx²`
    "emit": {
        "keyword_case": "Capitalised",
        "terminators": {
            "if": "EndIf", "while": "EndWhile", "for": "EndFor", "repeat": "EndRepeat",
            "define": "End",
        },
    },
}  # fmt: skip
_AUTHOR: dict[str, Any] = {
    "name": "Author (S. Tyler)",
    "names": {"split_products": True},  # the book's `P(x) ← ax³ + bx² + cx + d`
    "emit": {"keyword_case": "lower", "for_do": "never"},
}
_STRICT: dict[str, Any] = {
    "name": "Strict",
    "names": {"split_products": False},
    "lexical": {
        "keywords_case_insensitive": False,
        "comments": {"#": "no"},
        "minus": {"−": "no", "–": "no"},
        "times": {"*": "no", "·": "no"},
        "divide": {"/": "no"},
        "mod": {"MOD": "no", "%": "no"},
        "div": {"DIV": "no"},
        "power": {"**": "no", "superscript_digits": "no"},
        "equal": {"==": "no"},
        "not_equal": {"<>": "no", "!=": "no"},
        "less_equal": {"<=": "no", "⩽": "no"},
        "greater_equal": {">=": "no", "⩾": "no"},
        "and": {"∧": "no"},
        "or": {"∨": "no"},
        "not": {"¬": "no"},
        "string_quotes": {"curly": "no"},
    },
    "constructs": {
        "assign": {"spellings": {"<-": "no", ":=": "no", "=": "no"}},
        "print": {
            "keywords": {"output": "no"},
            "parentheses": "forbidden",
            "item_separator": {"juxtaposed_after_string_literal": "no"},
        },
        "if": {
            "then": "required",
            "else_if": {"elseif": "no", "elif": "no"},
            "terminators": {"endif": "no"},
        },
        "while": {
            "do": "forbidden",
            "is_true": "no",
            "terminators": {"endwhile": "no", "wend": "no"},
        },
        "for": {
            "do": "forbidden",
            "terminators": {"endfor": "no", "next": "no", "next <variable>": "no"},
        },
        "repeat_times": {"terminators": {"endrepeat": "no"}},
        "define": {
            "keywords": {"function": "no"},
            "colon_after_header": "forbidden",
            "terminators": {"end define": "no", "end function": "no", "dedent": "no"},
        },
        "function_by_assignment": "no",
    },
    "structure": {"missing_inner_end": "no", "surplus_end": "no"},
}  # fmt: skip

PRESET_DATA: dict[str, dict[str, Any]] = {
    "default": copy.deepcopy(DEFAULT_DATA),
    "vcaa": _merge(DEFAULT_DATA, _VCAA),
    "author": _merge(DEFAULT_DATA, _AUTHOR),
    "strict": _merge(DEFAULT_DATA, _STRICT),
}
PRESET_DATA["vcaa"]["based_on"] = "default"
PRESET_DATA["author"]["based_on"] = "default"
PRESET_DATA["strict"]["based_on"] = "default"

PRESETS: dict[str, Syntax] = {name: _compile(data) for name, data in PRESET_DATA.items()}
DEFAULT: Syntax = PRESETS["default"]
