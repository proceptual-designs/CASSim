"""Two display and naming options: two-dimensional output, and case-sensitive variable names."""

from cassim.cli.repl import Output, respond
from cassim.core.format import to_pretty
from cassim.core.session import Session
from cassim.core.settings import Case, Settings, updated


def drawn(session: Session, line: str, *, unicode: bool = True) -> str:
    value = session.eval(line).value
    assert value is not None
    return to_pretty(value, session.settings, unicode=unicode)


def pretty(line: str, *, unicode: bool = True) -> str:
    return drawn(Session(), line, unicode=unicode)


def said(session: Session, line: str, *, ascii_output: bool = False) -> Output:
    output = respond(session, line, ascii_output=ascii_output)
    assert output is not None
    return output


def test_fraction_is_drawn_over_a_bar():
    assert pretty("x/(x+1)") == "   x\n───────\n x + 1"


def test_power_is_raised():
    assert pretty("(x+1)^2") == "       2\n(x + 1)"


def test_square_root_has_a_radical_and_bar():
    assert pretty("sqrt(x+1)") == "  ▁▁▁▁▁\n√ x + 1"


def test_matrix_is_fenced_in_tall_brackets():
    assert pretty("[1,2;3,4]") == "⎡1  2⎤\n⎣3  4⎦"


def test_list_stays_on_one_line():
    assert pretty("{1,2,3}") == "{1, 2, 3}"


def test_ascii_drawing_uses_plain_characters():
    drawn = pretty("[x/2,1;y^2,sqrt(2)]", unicode=False)
    assert drawn.isascii()
    assert drawn.splitlines()[0].startswith("/")


def test_decimals_follow_the_digits_setting():
    session = Session(updated(Settings(), {"calc": "approximate", "digits": "float3"}))
    assert drawn(session, "1/3") == "0.333"


def test_repl_prints_pretty_only_when_asked():
    session = Session()
    assert said(session, "1/3").text == "1/3"
    respond(session, ":set pretty=on")
    assert said(session, "1/3").text == " 1\n───\n 3"
    assert said(session, "1/3", ascii_output=True).text.isascii()
    respond(session, ":set pretty=off")
    assert said(session, "1/3").text == "1/3"


def test_pretty_setting_rejects_other_values():
    assert said(Session(), ":set pretty=maybe").is_error


def test_names_ignore_case_by_default():
    session = Session()
    session.eval("Abc:=3")
    assert session.eval("abc+ABC").text == "6"


def test_case_sensitive_names_are_separate_variables():
    session = Session()
    session.set(case="sensitive")
    session.eval("x:=1")
    session.eval("X:=2")
    assert session.eval("x").text == "1"
    assert session.eval("X").text == "2"
    assert session.eval("x+X").text == "3"


def test_case_sensitive_undefined_name_keeps_its_case():
    session = Session()
    session.set(case="sensitive")
    assert session.eval("Y+1").text == "Y+1"


def test_case_sensitive_user_functions():
    session = Session()
    session.set(case="sensitive")
    session.eval("f(x):=x^2")
    session.eval("F(x):=x^3")
    assert session.eval("f(2)").text == "4"
    assert session.eval("F(2)").text == "8"


def test_built_in_names_stay_case_insensitive():
    session = Session()
    session.set(case="sensitive")
    assert session.eval("SIN(0)").text == "0"
    assert session.eval("Pi").text == "π"


def test_case_sensitive_solving_and_calculus_keep_the_unknown_case():
    session = Session()
    session.set(case="sensitive")
    assert session.eval("solve(T^2=4,T)").text == "T=-2 or T=2"
    assert session.eval("derivative(T^2,T)").text == "2·T".replace("·", "*")


def test_stat_results_ignore_case_even_when_names_do_not():
    session = Session()
    session.set(case="sensitive")
    session.eval("a:={1,2,3,4}")
    session.eval("b:={2,4,6,9}")
    session.eval("LinRegMx a,b,1")
    assert session.eval("stat.R²").text == session.eval("stat.r²").text


def test_turning_case_sensitivity_off_merges_names():
    session = Session()
    session.set(case="sensitive")
    session.eval("x:=1")
    session.eval("X:=2")
    session.set(case="insensitive")
    assert session.eval("x").text == "2"
    assert session.settings.case is Case.INSENSITIVE


def test_ascii_setting_spells_results_with_keyboard_characters():
    session = Session()
    assert session.eval("sqrt(2)*pi").text == "√(2)*π"
    session.set(ascii="on")
    result = session.eval("sqrt(2)*pi")
    assert result.text == "sqrt(2)*pi"
    assert session.eval("arcsin(x)").text == "arcsin(x)"


def test_ascii_setting_in_the_repl_also_covers_pretty_output():
    session = Session()
    respond(session, ":set ascii=on pretty=on")
    assert said(session, "[1,2;3,4]").text.isascii()
    assert said(session, "pi/2").text.replace("\n", "").strip().isascii()
