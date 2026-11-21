"""The `cassim` command line: REPL pieces, script runner and entry point."""

import io

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from cassim.cli import repl
from cassim.cli.repl import (
    HELP,
    Output,
    ScriptOptions,
    complete,
    completion_length,
    describe_settings,
    evaluate_line,
    main,
    parse_settings,
    respond,
    run_script,
)
from cassim.cli.terminal import make_reader
from cassim.core import catalog
from cassim.core.session import Session
from cassim.core.settings import PRESETS, Angle, Calc, CasMode, Settings


def answer(session, line):
    output = respond(session, line)
    assert output is not None
    return output


def script(lines, **options):
    out = io.StringIO()
    status = run_script(Session(), lines, out, ScriptOptions(**options))
    return status, out.getvalue()


# ---- completion ------------------------------------------------------------------------------


def test_completion_offers_catalog_functions_commands_and_variables():
    session = Session()
    session.eval("alpha:=3")
    assert "solve" in complete(session, "so")
    assert "SortA" in complete(session, "Sort")
    assert complete(session, "x+alp") == ["alpha"]
    assert "DelVar" in complete(session, "del")
    assert "Define" in complete(session, "Defi")
    assert "pi" in complete(session, "p")


def test_completion_is_case_insensitive_and_skips_an_exact_match():
    session = Session()
    assert "normCdf" in complete(session, "NORMC")
    assert "solve" not in complete(session, "solve")  # nothing left to add
    assert complete(session, "1+") == []
    assert complete(session, "") == []


def test_completion_after_an_arrow_offers_conversions():
    session = Session()
    assert complete(session, "255@>Ba") == ["Base10", "Base16", "Base2"]
    assert "Polar" in complete(session, "z▶Po")
    assert completion_length("255@>Ba") == 2
    assert completion_length("x+solv") == 4
    assert completion_length("1+") == 0


def test_completion_sees_new_variables_and_functions():
    session = Session()
    session.eval("area(r):=pi*r^2")
    assert complete(session, "are") == ["area"]
    session.eval("delVar area")
    assert complete(session, "are") == []


def test_catalog_name_lists():
    names = catalog.function_names()
    assert names == sorted(names, key=str.casefold)
    assert {"solve", "derivative", "normCdf", "tvmPmt", "seq"} <= set(names)
    assert "Base16" in catalog.conversion_names()


# ---- entries and settings --------------------------------------------------------------------


def test_evaluate_line():
    session = Session()
    assert evaluate_line(session, "2+3") == Output("5")
    assert evaluate_line(session, "   ") is None
    assert evaluate_line(session, "1+") == Output("Error: Syntax error", is_error=True)
    assert evaluate_line(session, "pi", ascii_output=True) == Output("pi")
    assert evaluate_line(session, "solve(x^2=2,x)", ascii_output=True) == Output(
        "x=-sqrt(2) or x=sqrt(2)"
    )
    assert evaluate_line(session, "a:=1:Done") is not None


def test_parse_settings():
    base = Settings()
    assert parse_settings(base, ["angle=degree"]).angle is Angle.DEGREE
    assert parse_settings(base, ["angle", "degree", "calc", "approximate"]).calc is Calc.APPROXIMATE
    assert parse_settings(base, ["cas_mode=off"]).cas_mode is CasMode.OFF
    assert parse_settings(base, ["exp_format=scientific"]).exp_format == "scientific"
    assert parse_settings(base, ["digits=fix2"]).digits == "fix2"
    assert parse_settings(base, []) == base


@pytest.mark.parametrize(
    ("words", "message"),
    [
        (["colour=red"], "unknown setting"),
        (["angle"], "expected key=value"),
        (["angle=turns"], "bad value"),
    ],
)
def test_parse_settings_rejects_nonsense(words, message):
    with pytest.raises(ValueError, match=message):
        parse_settings(Settings(), words)


def test_colon_commands():
    session = Session()
    assert respond(session, ":help") == Output(HELP)
    assert answer(session, ":set angle=degree").text.startswith("angle=degree")
    assert session.settings.angle is Angle.DEGREE
    assert answer(session, ":settings").text == describe_settings(session.settings)
    respond(session, "a:=5")
    respond(session, "f(x):=x")
    assert respond(session, ":vars") == Output("a f")
    assert respond(session, ":new") == Output("New Problem")
    assert respond(session, ":vars") == Output("(none)")
    assert answer(session, ":set angle=turns").is_error
    assert answer(session, ":set colour=red").is_error
    assert answer(session, ":nope").is_error
    for quit_word in (":quit", ":q", ":exit"):
        with pytest.raises(EOFError):
            respond(session, quit_word)


def test_assignment_is_not_mistaken_for_a_colon_command():
    session = Session()
    assert respond(session, ":=5") is not None
    assert respond(session, "x:=5") == Output("5")


# ---- scripts ---------------------------------------------------------------------------------


def test_script_prints_each_entry_and_result():
    status, shown = script(["f(x):=x^2", "f(3)"])
    assert status == 0
    assert shown == "cassim> f(x):=x^2\nDone\ncassim> f(3)\n9\n"


def test_script_skips_comments_and_blank_lines_and_can_be_quiet():
    status, shown = script(["// a comment", "", "   ", "2+2", "  // another"], echo=False)
    assert (status, shown) == (0, "4\n")


def test_script_stops_at_the_first_error_unless_asked_to_continue():
    status, shown = script(["1", "1+", "3"], echo=False)
    assert status == 1
    assert shown == "1\nError: Syntax error\n(line 2)\n"
    status, shown = script(["1", "1+", "3"], echo=False, keep_going=True)
    assert status == 1
    assert shown.endswith("3\n")


def test_script_applies_colon_commands():
    status, shown = script([":set angle=degree", "sin(30)"], echo=False)
    assert status == 0
    assert shown.splitlines()[-1] == "1/2"


def test_script_in_ascii():
    _, shown = script(["pi", "solve(x^2=2,x)"], echo=False, ascii_output=True)
    assert shown == "pi\nx=-sqrt(2) or x=sqrt(2)\n"


# ---- entry point -----------------------------------------------------------------------------


def test_main_evaluates_one_entry(capsys):
    assert main(["-c", "2^10"]) == 0
    assert capsys.readouterr().out == "1024\n"
    assert main(["--course", "general", "-c", "1/3"]) == 0
    assert capsys.readouterr().out == "0.33333333\n"
    assert main(["--set", "angle=degree", "-c", "sin(30)"]) == 0
    assert capsys.readouterr().out == "1/2\n"
    assert main(["--ascii", "-c", "infinity"]) == 0
    assert capsys.readouterr().out == "infinity\n"


def test_main_forwards_a_direct_app_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[dict[str, object]] = []
    monkeypatch.setattr("cassim.app.main.run", lambda **options: opened.append(options))

    assert main(["--web", "--app", "pseudocode"]) == 0

    assert opened[0]["web"] is True
    assert opened[0]["app"] == "pseudocode"


def test_text_mode_rejects_direct_app_choice() -> None:
    with pytest.raises(SystemExit):
        main(["--text", "--app", "pseudocode"])


def test_main_reports_an_error_status(capsys):
    assert main(["-c", "1/"]) == 1
    assert "Syntax error" in capsys.readouterr().out
    assert main(["--set", "angle=turns", "-c", "1"]) == 2
    assert "bad value" in capsys.readouterr().err


def test_main_runs_a_script_file(tmp_path, capsys):
    path = tmp_path / "demo.tib"
    path.write_text("// demo\nx:={1,2,3,4}\nmean(x)\nsolve(x^2=9,x)\n", encoding="utf-8")
    assert main(["run", str(path)]) == 0
    shown = capsys.readouterr().out
    assert "cassim> mean(x)\n5/2\n" in shown
    assert main(["run", str(path), "--quiet"]) == 0
    assert capsys.readouterr().out.splitlines()[:2] == ["{1,2,3,4}", "5/2"]


def test_main_script_errors(tmp_path, capsys):
    assert main(["run", str(tmp_path / "missing.tib")]) == 2
    assert "cannot read" in capsys.readouterr().err
    path = tmp_path / "bad.tib"
    path.write_text("1\n1+\n3\n", encoding="utf-8")
    assert main(["run", str(path), "--quiet"]) == 1
    assert capsys.readouterr().out.endswith("(line 2)\n")
    assert main(["run", str(path), "--quiet", "--keep-going"]) == 1
    assert capsys.readouterr().out.splitlines()[-1] == "3"


def test_main_runs_a_script_from_standard_input(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("2+2\n"))
    assert main(["run", "-", "--quiet"]) == 0
    assert capsys.readouterr().out == "4\n"


def test_the_repl_reads_entries_until_the_end_of_input(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("a:=2\na^10\n:set angle=degree\nsin(30)\n"))
    assert main(["--text"]) == 0
    shown = capsys.readouterr().out.splitlines()
    assert shown[:2] == ["2", "1024"]
    assert shown[-1] == "1/2"


def test_the_repl_stops_at_quit(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("1\n:quit\n2\n"))
    assert main(["--text"]) == 0
    assert capsys.readouterr().out.splitlines() == ["1"]


def test_presets_are_available_by_name():
    assert set(PRESETS) >= {"general", "methods", "specialist"}
    assert repl.new_session("general", []).settings == PRESETS["general"]
    assert repl.new_session(None, ["angle=degree"]).settings.angle is Angle.DEGREE


def test_help_names_the_settings():
    for key in repl.SETTING_KEYS:
        assert key in HELP


# ---- Ctrl+Enter: give the entry as a decimal ---------------------------------------------------


def test_approximate_entry_is_the_same_as_wrapping_in_approx():
    for line in ("1/3", "sqrt(2)", "{1/2,pi}", "solve(x^2=2,x)", "[1,2;3,4]^-1", "exact(0.75)"):
        wrapped = Session().eval(f"approx({line})")
        direct = Session().eval(line, approximate=True)
        assert (wrapped.error, direct.error) == (None, None), line
        assert direct.text == wrapped.text, line


def test_approximate_ignores_the_calculation_mode_and_leaves_text_alone():
    exact = Session(Settings(calc=Calc.EXACT))
    assert exact.eval("1/3", approximate=True).text == "0.33333333"
    assert exact.eval("1/3").text == "1/3"
    assert Session().eval('"hi"', approximate=True).text == '"hi"'
    assert Session().eval("f(x):=x", approximate=True).text == "Done"
    assert Session().eval("2+2", approximate=True).text == "4."


def test_approximate_answer_becomes_ans_and_does_not_change_variables():
    session = Session()
    assert session.eval("a:=1/3", approximate=True).text == "0.33333333"
    assert session.eval("ans").text == "0.33333333"
    assert session.eval("a").text == "1/3"


def test_approximate_on_an_empty_line_gives_the_previous_answer_as_a_decimal():
    session = Session()
    assert session.eval("", approximate=True).text == ""  # no previous answer yet
    assert session.eval("2/3").text == "2/3"
    assert session.eval("", approximate=True).text == "0.66666667"
    assert session.eval("   ", approximate=True).text == "0.66666667"
    assert session.eval("ans").text == "0.66666667"  # and the decimal is now Ans
    assert session.eval("solve(x^2=2,x)").text == "x=-√(2) or x=√(2)"
    assert session.eval("", approximate=True).text == "x=-1.4142136 or x=1.4142136"


def test_approximate_on_an_empty_line_ignores_done_and_plain_empty_lines():
    session = Session()
    session.eval("1/4")
    session.eval("f(x):=x")  # prints Done, which is not an answer
    assert session.eval("", approximate=True).text == "0.25"
    assert session.eval("").text == ""  # without approximate an empty line does nothing


def test_approx_command_on_an_empty_line_in_the_repl():
    session = Session()
    assert respond(session, ":approx") is None  # nothing yet
    respond(session, "1/8")
    assert respond(session, ":approx") == Output("0.125")
    assert respond(session, ":approx ") == Output("0.125")
    assert respond(session, "") is None  # a plain empty line still does nothing


def test_approx_command_in_the_repl():
    session = Session()
    assert respond(session, ":approx 1/3") == Output("0.33333333")
    assert respond(session, ":approx solve(x^2=2,x)") == Output("x=-1.4142136 or x=1.4142136")
    assert answer(session, ":approx 1/").is_error
    assert answer(session, ":approxx 1").is_error  # a different, unknown command
    assert answer(session, ":approx 1/3").text == "0.33333333"
    assert "Ctrl+Enter" in HELP


def test_prompt_keys_put_approx_in_front_of_the_entry():
    session = Session()
    for keys, expected in (
        ("1/3\r", "1/3"),
        ("1/3\x1b\r", ":approx 1/3"),  # Alt-Enter
        ("1/3\n", ":approx 1/3"),  # Ctrl-Enter, as a terminal that reports it sends it
        ("\x1b\r", ":approx "),  # Alt-Enter on an empty prompt: approximate the last answer
        ("\n", ":approx "),
    ):
        with create_pipe_input() as pipe, create_app_session(input=pipe, output=DummyOutput()):
            pipe.send_text(keys)
            reader = make_reader(session, input=pipe, output=DummyOutput())
            assert reader.prompt("") == expected


def test_the_app_is_the_default_and_takes_view_and_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`cassim` opens the app; --web, --view, --course and --set go to it; --text is the REPL."""
    import cassim.app.main as app  # noqa: PLC0415
    from cassim.devices.nspire.ui.state import Mode  # noqa: PLC0415

    started: list[tuple[bool, Mode | None, str | None, Settings | None]] = []
    monkeypatch.setattr(
        app,
        "run",
        lambda *, web=False, view=None, app=None, settings=None: started.append(
            (web, view, app, settings)
        ),
    )
    monkeypatch.setattr(repl, "interactive", lambda session, ascii_output: 0)
    assert main([]) == 0
    assert main(["--web"]) == 0
    assert main(["--view", "handheld", "--course", "methods"]) == 0
    assert main(["--set", "angle=degree"]) == 0
    assert started == [
        (False, None, None, None),
        (True, None, None, None),
        (False, Mode.HANDHELD, None, PRESETS["methods"]),
        (False, None, None, Settings(angle=Angle.DEGREE)),
    ]
    assert main(["--text"]) == 0
    assert main(["--text", "--course", "methods"]) == 0
    assert len(started) == 4


def test_app_options_are_refused_with_the_text_interface() -> None:
    with pytest.raises(SystemExit):
        main(["--text", "--web"])
    with pytest.raises(SystemExit):
        main(["-c", "1", "--view", "handheld"])
