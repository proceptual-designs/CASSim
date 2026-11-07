"""The pseudocode syntax file: loading, validation, presets and a syntax-driven parser.

SRS FR-SYN-001 (syntax is data), -002 (spellings and optional tokens), -003 (invalid file falls
back), -004 (validation names the entry), -008 (presets), -009 (data only, size-limited).
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from cassim.runtime.pseudocode import (
    DEFAULT,
    PRESETS,
    Settings,
    SyntaxFileError,
    load_syntax,
    parse,
    run,
)
from cassim.runtime.pseudocode.syntax import (
    DEFAULT_DATA,
    MAX_FILE_CHARS,
    PRESET_DATA,
    load_or_default,
    load_syntax_text,
    parse_text,
    validate,
)

ROOT = Path(__file__).parents[2]
SEED = yaml.safe_load((ROOT / "corpus/pseudocode/seed.yaml").read_text(encoding="utf-8"))["cases"]


def with_syntax(**overlay: Any) -> Any:
    return load_syntax(overlay)


def warnings_of(source: str, syntax: Any = DEFAULT) -> list[str]:
    return [w.message for w in parse(source, syntax).warnings]


# ----------------------------------------------------------------------------- the files


def test_default_file_in_docs_is_the_built_in_default() -> None:
    """FR-SYN-001: docs/pseudocode/syntax-default.yaml and the built-in default are one thing."""
    text = (ROOT / "docs/pseudocode/syntax-default.yaml").read_text(encoding="utf-8")
    on_disk = parse_text(text)
    assert isinstance(on_disk, dict)
    assert validate(on_disk) == []
    assert on_disk == DEFAULT_DATA
    assert load_syntax_text(text).data == DEFAULT.data


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_is_valid(name: str) -> None:
    """FR-SYN-008: Default, VCAA, Author and Strict."""
    assert validate(PRESET_DATA[name]) == []
    assert PRESETS[name].name


def test_partial_file_keeps_the_default_for_what_it_leaves_out() -> None:
    syntax = load_syntax({"constructs": {"if": {"then": "required"}}})
    assert syntax.then == "required"
    assert syntax.while_do == "optional"
    assert syntax.closers == DEFAULT.closers


def test_based_on_starts_from_a_preset() -> None:
    syntax = load_syntax({"based_on": "strict", "constructs": {"if": {"then": "optional"}}})
    assert syntax.then == "optional"
    assert not syntax.case_insensitive  # still Strict's


# ------------------------------------------------------------------------ optional tokens


def test_then_may_be_required_optional_or_forbidden() -> None:
    """FR-SYN-002."""
    plain = "if 1 < 2\n  print 1\nend if"
    with_then = "if 1 < 2 then\n  print 1\nend if"
    required = with_syntax(constructs={"if": {"then": "required"}})
    forbidden = with_syntax(constructs={"if": {"then": "forbidden"}})
    assert run(plain, syntax=DEFAULT).halt == run(with_then, syntax=DEFAULT).halt == "finished"
    assert run(with_then, syntax=required).halt == "finished"
    assert "expected 'then'" in (run(plain, syntax=required).error or "")
    assert run(plain, syntax=forbidden).halt == "finished"
    assert "'then' is not accepted" in (run(with_then, syntax=forbidden).error or "")


def test_do_policy_for_while_and_for() -> None:
    source_for = "for i from 1 to 2 do\n  print i\nend for"
    source_while = "x ← 0\nwhile x < 1 do\n  x ← x + 1\nend while"
    no_do = with_syntax(constructs={"for": {"do": "forbidden"}, "while": {"do": "forbidden"}})
    need_do = with_syntax(constructs={"for": {"do": "required"}, "while": {"do": "required"}})
    assert run(source_for, syntax=DEFAULT).output == ["1", "2"]
    assert run(source_for, syntax=need_do).halt == "finished"
    assert "'do' is not accepted" in (run(source_for, syntax=no_do).error or "")
    assert "'do' is not accepted" in (run(source_while, syntax=no_do).error or "")
    assert "expected 'do'" in (
        run("for i from 1 to 2\n  print i\nend for", syntax=need_do).error or ""
    )


@pytest.mark.parametrize("closer", ["end for", "endfor", "next", "next i", "End For", "ENDFOR"])
def test_for_loop_closers(closer: str) -> None:
    """FR-SYN-002: `end for`, `endfor`, `next` with or without the variable."""
    result = run(f"for i from 1 to 3\n  print i\n{closer}", syntax=DEFAULT)
    assert result.output == ["1", "2", "3"], result.error


def test_closer_modes_ok_warn_no() -> None:
    source = "if 1 < 2\n  print 1\nendif"
    assert warnings_of(source) == []
    warn = with_syntax(constructs={"if": {"terminators": {"endif": "warn"}}})
    assert len(warnings_of(source, warn)) == 1
    reject = with_syntax(constructs={"if": {"terminators": {"endif": "no"}}})
    assert "'endif' is not accepted" in (run(source, syntax=reject).error or "")


def test_function_may_end_with_end_define_end_function_or_a_dedent() -> None:
    for closer in ("end", "end define", "end function"):
        assert run(f"define f()\n  return 4\n{closer}\nprint f()").output == ["4"]
    assert run("define f()\n  return 4\nprint f()").output == ["4"]
    no_dedent = with_syntax(constructs={"define": {"terminators": {"dedent": "no"}}})
    assert "indentation is not accepted" in (
        run("define f()\n  return 4\nprint f()", syntax=no_dedent).error or ""
    )


def test_else_if_spellings_have_modes() -> None:
    source = "x ← 2\nif x = 1 then\n  print 1\nelif x = 2 then\n  print 2\nend if"
    assert run(source).output == ["2"]
    strict = with_syntax(constructs={"if": {"else_if": {"elif": "no"}}})
    assert "'elif' is not accepted" in (run(source, syntax=strict).error or "")


def test_missing_inner_end_and_surplus_end_policies() -> None:
    missing = "for i from 1 to 2\n  if i = 1 then\n    print i\nend for"
    assert len(warnings_of(missing)) == 1
    assert "missing 'end if'" in (
        run(missing, syntax=with_syntax(structure={"missing_inner_end": "no"})).error or ""
    )
    assert warnings_of(missing, with_syntax(structure={"missing_inner_end": "ok"})) == []
    surplus = "print 1\nend if"
    assert "closes nothing" in (run(surplus).error or "")
    lenient = with_syntax(structure={"surplus_end": "warn"})
    assert run(surplus, syntax=lenient).output == ["1"]
    assert len(warnings_of(surplus, lenient)) == 1


def test_keyword_case_can_be_made_exact() -> None:
    source = "If 1 < 2 Then\n  Print 1\nEnd If"
    assert run(source).output == ["1"]
    exact = with_syntax(lexical={"keywords_case_insensitive": False})
    assert run(source, syntax=exact).halt == "error"
    assert run("if 1 < 2 then\n  print 1\nend if", syntax=exact).output == ["1"]


def test_print_parentheses_and_juxtaposed_items() -> None:
    required = with_syntax(constructs={"print": {"parentheses": "required"}})
    forbidden = with_syntax(constructs={"print": {"parentheses": "forbidden"}})
    assert run("print(1, 2)", syntax=required).output == ["1 2"]
    assert "needs its items in brackets" in (run("print 1, 2", syntax=required).error or "")
    assert run("print 1, 2", syntax=forbidden).output == ["1 2"]
    assert "not accepted" in (run("print(1, 2)", syntax=forbidden).error or "")
    reject = with_syntax(
        constructs={"print": {"item_separator": {"juxtaposed_after_string_literal": "no"}}}
    )
    assert run('print "a" 1').halt == "finished"
    assert "without a comma" in (run('print "a" 1', syntax=reject).error or "")


def test_assignment_spellings() -> None:
    assert warnings_of("x = 5") == ["'=' used to assign; treated as '←'"]
    ok = with_syntax(constructs={"assign": {"spellings": {"=": "ok"}}})
    assert warnings_of("x = 5", ok) == []
    no = with_syntax(constructs={"assign": {"spellings": {"=": "no", "<-": "no"}}})
    assert "not accepted" in (run("x = 5", syntax=no).error or "")
    assert "'<-' is not accepted" in (run("x <- 5", syntax=no).error or "")
    assert run("x ← 5\nprint x", syntax=no).output == ["5"]


def test_symbol_spellings_comments_and_quotes() -> None:
    no_hash = with_syntax(lexical={"comments": {"#": "no"}})
    assert run("print 1 # note").output == ["1"]
    assert "comment marker '#'" in (run("print 1 # note", syntax=no_hash).error or "")
    assert warnings_of("print 7 % 4") == [
        "'%' is not preferred in the CASSim default (tolerant) syntax"
    ]
    no_curly = with_syntax(lexical={"string_quotes": {"curly": "no"}})
    assert run("print “hi”").output == ["hi"]
    assert "curly quotes" in (run("print “hi”", syntax=no_curly).error or "")
    no_sup = with_syntax(lexical={"power": {"superscript_digits": "no"}})
    assert run("print 2³").output == ["8"]
    assert "superscript" in (run("print 2³", syntax=no_sup).error or "")


def test_logic_symbols_follow_the_word_forms() -> None:
    assert run("print 1 < 2 and 2 < 3").output == ["true"]
    assert run("print 1 < 2 ∧ 2 < 3").output == ["true"]
    no_symbol = with_syntax(lexical={"and": {"∧": "no"}})
    assert "'∧' is not accepted" in (run("print 1 < 2 ∧ 2 < 3", syntax=no_symbol).error or "")


def test_function_by_assignment_and_default_parameters_can_be_refused() -> None:
    func = "P(x) ← x + 1\nprint P(2)"
    default_param = "define f(a, b=2)\n  return a + b\nend\nprint f(1)"
    assert run(func).output == ["3"]
    assert run(default_param).output == ["3"]
    assert "not accepted" in (
        run(func, syntax=with_syntax(constructs={"function_by_assignment": "no"})).error or ""
    )
    no_defaults = with_syntax(constructs={"default_parameters": "no"})
    assert "not accepted" in (run(default_param, syntax=no_defaults).error or "")


def test_colon_after_function_header_policy() -> None:
    source = "define f(x):\n  return x\nend\nprint f(3)"
    assert run(source).output == ["3"]
    forbidden = with_syntax(constructs={"define": {"colon_after_header": "forbidden"}})
    assert "colon" in (run(source, syntax=forbidden).error or "")
    required = with_syntax(constructs={"define": {"colon_after_header": "required"}})
    assert "expected ':'" in (run("define f(x)\n  return x\nend", syntax=required).error or "")


def test_extra_keywords_can_be_added() -> None:
    """FR-SYN-001: keywords and terminators are data."""
    syntax = load_syntax(
        {
            "constructs": {
                "print": {"keywords": {"say": "ok"}},
                "define": {
                    "keywords": {"procedure": "ok"},
                    "terminators": {"end procedure": "ok"},
                },
            }
        }
    )
    assert run("procedure f()\n  say 5\nend procedure\nf()", syntax=syntax).output == ["5"]


# --------------------------------------------------------------------------- name splitting


def test_presets_differ_on_name_splitting() -> None:
    source = "a ← 2\nx ← 3\nprint ax"
    assert run(source, syntax=PRESETS["vcaa"]).output == ["6"]
    assert run(source, syntax=PRESETS["author"]).output == ["6"]
    for name in ("default", "strict"):
        error = run(source, syntax=PRESETS[name]).error or ""
        assert "did you mean a*x?" in error


# ------------------------------------------------------------------------- validation


def problems(**overlay: Any) -> list[str]:
    return validate(overlay)


def test_unknown_entries_are_named() -> None:
    assert problems(contructs={}) == ["contructs: unknown entry"]
    found = problems(constructs={"if": {"thn": "required"}})
    assert found == ["constructs.if.thn: unknown entry"]


def test_bad_modes_and_policies_are_named() -> None:
    assert any("constructs.if.then" in p for p in problems(constructs={"if": {"then": "maybe"}}))
    found = problems(constructs={"while": {"terminators": {"wend": "sometimes"}}})
    assert found == [
        "constructs.while.terminators.wend: must be one of ok, warn, no (got 'sometimes')"
    ]
    assert any("emit.keyword_case" in p for p in problems(emit={"keyword_case": "shout"}))


def test_a_bare_end_for_two_constructs_is_rejected() -> None:
    """FR-SYN-004: no innermost-block rule, so one bare `end` may end only one construct."""
    found = problems(constructs={"if": {"terminators": {"end": "ok"}}})
    assert len(found) == 1
    assert "terminators.end" in found[0]
    assert "bare 'end'" in found[0]
    assert "if" in found[0]
    assert "define" in found[0]


def test_one_spelling_for_two_constructs_is_rejected() -> None:
    found = problems(constructs={"repeat_times": {"terminators": {"next": "ok"}}})
    assert len(found) == 1
    assert "'next'" in found[0]


def test_a_keyword_for_two_constructs_is_rejected() -> None:
    found = problems(constructs={"input": {"keywords": {"print": "ok"}}})
    assert any("also a keyword for" in p for p in found)


def test_reserved_words_cannot_be_keywords() -> None:
    found = problems(constructs={"print": {"keywords": {"while": "ok"}}})
    assert any("reserved by the grammar" in p for p in found)


def test_no_spelling_left_for_a_required_construct() -> None:
    nothing = problems(
        constructs={"assign": {"spellings": {"←": "no", "<-": "no", ":=": "no", "=": "no"}}}
    )
    assert any("no spelling is left for assignment" in p for p in nothing)
    no_print = problems(constructs={"print": {"keywords": {"print": "no", "output": "no"}}})
    assert any("no keyword is left for print" in p for p in no_print)
    no_end = problems(
        constructs={"while": {"terminators": {"end while": "no", "endwhile": "no", "wend": "no"}}}
    )
    assert any("no way left to end a while block" in p for p in no_end)


def test_the_engine_has_no_spelling_it_was_not_given() -> None:
    found = problems(lexical={"times": {"⊗": "ok"}})
    assert any("lexical.times.⊗" in p for p in found)


def test_phrases_are_plain_words() -> None:
    found = problems(constructs={"if": {"terminators": {"end; if": "ok"}}})
    assert any("one to three plain words" in p for p in found)


def test_keywords_that_collide_with_a_users_variables_are_reported() -> None:
    syntax = load_syntax({"constructs": {"print": {"keywords": {"say": "ok"}}}})
    assert syntax.keyword_collisions(["x", "say", "Print", "total"]) == ["Print", "say"]


# --------------------------------------------------------------------------- data only


def test_file_is_data_only_and_size_limited() -> None:
    """FR-SYN-009 (NFR-SEC-003)."""
    with pytest.raises(SyntaxFileError, match="larger than"):
        load_syntax_text("# " + "x" * MAX_FILE_CHARS)
    with pytest.raises(SyntaxFileError, match="not valid YAML"):
        load_syntax_text("name: !!python/object/apply:os.system ['echo hi']")
    with pytest.raises(SyntaxFileError, match="expected a table"):
        load_syntax_text("- just\n- a list")
    with pytest.raises(SyntaxFileError, match="based_on"):
        load_syntax({"based_on": "nonsense"})


def test_json_text_loads_too() -> None:
    syntax = load_syntax_text('{"name": "mine", "constructs": {"if": {"then": "required"}}}')
    assert syntax.name == "mine"
    assert syntax.then == "required"


def test_invalid_file_falls_back_to_the_default_with_reasons() -> None:
    """FR-SYN-003."""
    syntax, reasons = load_or_default("constructs:\n  if:\n    then: sometimes\n")
    assert syntax is DEFAULT
    assert reasons
    again, none = load_or_default("name: fine")
    assert again.name == "fine"
    assert none == []


# ------------------------------------------------------------------------ strict preset


def test_strict_accepts_one_spelling_per_construct() -> None:
    good = (
        "define f(x)\n  return x × 2\nend\n"
        "for i from 1 to 2\n  if f(i) ≥ 4 then\n    print f(i)\n  end if\nend for"
    )
    strict = PRESETS["strict"]
    assert run(good, syntax=strict).output == ["4"]
    for bad in (
        "x <- 1",
        "x = 1",
        "print 2 * 3",
        "# note\nprint 1",
        "If 1 < 2 Then\nPrint 1\nEnd If",
    ):
        assert run(bad, syntax=strict).halt == "error", bad
    assert "'endif' is not accepted" in (
        run("if 1 < 2 then\n  print 1\nendif", syntax=strict).error or ""
    )
    assert "'then'" in (run("if 1 < 2\n  print 1\nend if", syntax=strict).error or "")


def test_strict_turns_the_inner_end_warning_into_an_error() -> None:
    source = "for i from 1 to 2\n  if i = 1 then\n    print i\nend for"
    assert len(warnings_of(source)) == 1
    assert "missing 'end if'" in (run(source, syntax=PRESETS["strict"]).error or "")


# --------------------------------------------------- the tolerant presets read every golden program


def settings_for(case: dict[str, Any]) -> Settings:
    return Settings(display="full", **case.get("settings", {}))


@pytest.mark.parametrize("preset", ["vcaa", "author"])
@pytest.mark.parametrize("case", SEED, ids=[c["id"] for c in SEED])
def test_tolerant_presets_give_the_default_result(case: dict[str, Any], preset: str) -> None:
    """FR-SYN-008: VCAA and Author read every golden program and agree with the default."""
    base = PRESETS[case.get("syntax", "default")]
    inputs = case.get("inputs", [])
    expected = run(case["pseudocode"], settings_for(case), inputs, syntax=base)
    got = run(case["pseudocode"], settings_for(case), inputs, syntax=PRESETS[preset])
    assert (got.halt, got.output) == (expected.halt, expected.output)
    assert [w.message for w in got.warnings] == [w.message for w in expected.warnings]
