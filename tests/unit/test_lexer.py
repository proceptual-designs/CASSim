# Requirements traced here: FR-LANG-001, FR-LANG-002, FR-LANG-004, FR-EVAL-005
import pytest

from cassim.core.errors import MISSING_QUOTE, SYNTAX, TISyntaxError
from cassim.core.lexer import Kind, tokenize


def kinds_and_text(src: str) -> list[tuple[Kind, str]]:
    return [(t.kind, t.text) for t in tokenize(src)[:-1]]


def texts(src: str) -> list[str]:
    return [t.text for t in tokenize(src)[:-1]]


@pytest.mark.parametrize(
    "src",
    ["0", "12", "1.", ".5", "1.5", "1ᴇ5", "1.ᴇ-13", "2ᴇ+3", "0b1011", "0hFF"],
)
def test_number_is_one_token_kept_as_typed(src):
    assert kinds_and_text(src) == [(Kind.NUMBER, src)]


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("2x", ["2", "x"]),
        ("2e", ["2", "e"]),
        ("2e3", ["2", "e3"]),
        ("2e-1", ["2", "e", "-", "1"]),
        ("2E3", ["2", "E3"]),
        ("2E-1", ["2", "E", "-", "1"]),
        ("2ⅇ", ["2", "ⅇ"]),
        ("ⅇx", ["ⅇ", "x"]),
        ("2π", ["2", "π"]),
        ("πx", ["π", "x"]),
        ("xπ", ["x", "π"]),
        ("ax", ["ax"]),
        ("x2", ["x2"]),
        ("1./3", ["1.", "/", "3"]),
        ("1.+2", ["1.", "+", "2"]),
        ("x.+2", ["x", ".+", "2"]),
    ],
)
def test_token_boundaries(src, expected):
    assert texts(src) == expected


@pytest.mark.parametrize(
    "src",
    [
        "stat.results",
        "stat.r²",
        "stat.Q₁X",
        "stat.x̄",
        "lib\\fn",
        "mm_solve",
        "_m",
        "@n1",
        "@k2",
        "χ²Cdf",
        "sin⁻¹",
        "cosh⁻¹",
        "σx",
    ],
)
def test_name_is_one_token(src):
    assert kinds_and_text(src) == [(Kind.NAME, src)]


@pytest.mark.parametrize(
    ("spelling", "canonical"),
    [
        ("<=", "≤"),
        (">=", "≥"),
        ("/=", "≠"),
        ("->", "→"),
        ("@>", "▶"),
        ("►", "▶"),
        ("=>", "⇒"),
        ("<=>", "⇔"),
        ("@t", "ᵀ"),
        ("@r", "ʳ"),
        ("@g", "ᵍ"),
        ("@d", "°"),
        ("@<", "∠"),
        ("·", "*"),
    ],
)
def test_operator_spellings_fold_to_one(spelling, canonical):
    assert kinds_and_text(spelling) == [(Kind.OP, canonical)]


@pytest.mark.parametrize("word", ["and", "AND", "Or", "not", "xor", "nor", "nand"])
def test_word_operators_ignore_case(word):
    assert kinds_and_text(word) == [(Kind.OP, word.casefold())]


def test_at_constant_is_not_the_transpose():
    assert kinds_and_text("@t1") == [(Kind.NAME, "@t1")]


@pytest.mark.parametrize("src", ["list@>mat(", "list▶mat(", "LIST►MAT("])
def test_arrow_inside_a_catalog_name(src):
    assert tokenize(src)[0].kind is Kind.NAME
    assert tokenize(src)[0].text.casefold() == "list▶mat"


@pytest.mark.parametrize(
    ("src", "name"),
    [
        ("exp@>list(", "exp▶list"),
        ("freqTable@>list(", "freqTable▶list"),
        ("P@>Rx(", "P▶Rx"),
        ("P@>Ry(", "P▶Ry"),
        ("R@>Pr(", "R▶Pr"),
        ("R@>Ptheta(", "R▶Ptheta"),
        ("R▶Pθ(", "R▶Pθ"),
    ],
)
def test_every_arrow_name_in_the_guide(src, name):
    assert kinds_and_text(src)[0] == (Kind.NAME, name)


def test_arrow_needs_the_call_to_be_a_catalog_name():
    assert texts("list@>Polar") == ["list", "▶", "Polar"]


def test_dms_literal():
    assert kinds_and_text("60°15'45\"") == [(Kind.DMS, "60°15'45\"")]
    assert kinds_and_text("30°30'") == [(Kind.DMS, "30°30'")]
    assert kinds_and_text("30@d30'") == [(Kind.DMS, "30°30'")]


def test_string_value_excludes_quotes():
    assert kinds_and_text('"a b"') == [(Kind.STRING, "a b")]


def test_space_before_is_recorded():
    assert [t.space_before for t in tokenize("a b")] == [False, True, False]


def test_unterminated_string():
    with pytest.raises(TISyntaxError) as info:
        tokenize('1+"abc')
    assert info.value.code == MISSING_QUOTE
    assert info.value.pos == 2


@pytest.mark.parametrize("src", ["$", "x²", "@", "."])
def test_illegal_character(src):
    with pytest.raises(TISyntaxError) as info:
        tokenize(src)
    assert info.value.code == SYNTAX


def test_keyboard_spellings_of_look_alike_symbols():
    assert kinds_and_text("@e") == [(Kind.NAME, "ⅇ")]
    assert kinds_and_text("@i") == [(Kind.NAME, "ⅈ")]
    assert kinds_and_text("1.5@E-3") == [(Kind.NUMBER, "1.5ᴇ-3")]
    assert kinds_and_text("@e1") == [(Kind.NAME, "@e1")]
