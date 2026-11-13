"""The `cassim` command line: a REPL, a script runner and one-shot evaluation.

The pieces that matter (`complete`, `evaluate_line`, `run_script`, `parse_settings`) are plain
functions, so they are tested without a terminal. Only the interactive prompt needs
prompt_toolkit, and it falls back to `input()` when that is not installed.
"""

import argparse
import importlib
import io
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from cassim.core import catalog
from cassim.core.format import to_ascii, to_pretty
from cassim.core.parser import COMMANDS
from cassim.core.session import Session
from cassim.core.settings import PRESETS, Ascii, Pretty, Settings, updated

PROMPT = "cassim> "
# `:approx ENTRY` evaluates ENTRY as Ctrl+Enter does on the handheld; the prompt's Ctrl-Enter and
# Alt-Enter keys just put this in front of what was typed.
APPROX_PREFIX = ":approx "
_APPROX_COMMAND = APPROX_PREFIX.strip()
SETTING_KEYS = (
    "angle",
    "calc",
    "domain",
    "digits",
    "cas_mode",
    "exp_format",
    "case",
    "pretty",
    "ascii",
)
_CONSTANTS = ("ans", "false", "infinity", "pi", "true", "undef")
_COMMENT = "//"
_WORD_AT_END = re.compile(r"[A-Za-z_@][A-Za-z0-9_.@]*$")
_CONVERSION_AT_END = re.compile(r"(?:▶|@>)([A-Za-z0-9]*)$")
HELP = f"""Type an entry as on the calculator. ASCII spellings work: pi, infinity, @i, @e, @> for ▶.
  :set angle=degree calc=approximate     change a setting ({", ".join(SETTING_KEYS)})
  :settings                              show the settings
  :approx ENTRY                          give ENTRY as a decimal, like Ctrl+Enter
                                         (Alt+Enter at the prompt does the same)
  :new                                   start a new Problem (clears variables)
  :vars                                  list the variables and functions
  :help                                  this text
  :quit                                  leave (Ctrl-D also works)
Tab completes function, command and variable names."""


@dataclass(frozen=True, slots=True)
class Output:
    """What an entry printed: the text, and whether it was an error."""

    text: str
    is_error: bool = False


def parse_settings(base: Settings, assignments: Iterable[str]) -> Settings:
    """Apply `key=value` words (or `key value` pairs) to the settings."""
    changes: dict[str, str] = {}
    words = list(assignments)
    index = 0
    while index < len(words):
        word = words[index]
        if "=" in word:
            key, _, value = word.partition("=")
        elif index + 1 < len(words):
            key, value = word, words[index + 1]
            index += 1
        else:
            raise ValueError(f"expected key=value, got {word!r}")
        if key not in SETTING_KEYS:
            raise ValueError(f"unknown setting {key!r}; the settings are {', '.join(SETTING_KEYS)}")
        changes[key] = value
        index += 1
    try:
        return updated(base, changes)
    except ValueError as error:
        raise ValueError(f"bad value: {error}") from None


def describe_settings(settings: Settings) -> str:
    return "  ".join(f"{key}={getattr(settings, key)}" for key in SETTING_KEYS)


def complete(session: Session, line: str) -> list[str]:
    """Names that could finish the word at the end of `line`."""
    conversion = _CONVERSION_AT_END.search(line)
    if conversion:
        prefix = conversion.group(1).casefold()
        return [n for n in catalog.conversion_names() if n.casefold().startswith(prefix)]
    word = _WORD_AT_END.search(line)
    if word is None:
        return []
    prefix = word.group().casefold()
    names = {
        *catalog.function_names(),
        *COMMANDS.values(),
        "Define",
        *_CONSTANTS,
        *session.scope.names(),
    }
    return sorted(
        (n for n in names if n.casefold().startswith(prefix) and n.casefold() != prefix),
        key=str.casefold,
    )


def completion_length(line: str) -> int:
    """How many characters at the end of `line` a completion replaces."""
    conversion = _CONVERSION_AT_END.search(line)
    if conversion:
        return len(conversion.group(1))
    word = _WORD_AT_END.search(line)
    return len(word.group()) if word else 0


def evaluate_line(
    session: Session, line: str, *, ascii_output: bool = False, approximate: bool = False
) -> Output | None:
    """Run one entry and say what to print; None if the line was blank."""
    if not line.strip() and not approximate:
        return None
    result = session.eval(line, approximate=approximate)
    if not result.text and result.error is None:
        return None  # nothing was entered and there was no previous result
    if result.error is not None:
        return Output(f"Error: {result.error}", is_error=True)
    ascii_output = ascii_output or session.settings.ascii is Ascii.ON
    text = result.text
    if session.settings.pretty is Pretty.ON and result.value is not None:
        text = to_pretty(result.value, session.settings, unicode=not ascii_output)
    return Output(to_ascii(text) if ascii_output else text)


def _set(session: Session, words: list[str]) -> Output:
    try:
        session.settings = parse_settings(session.settings, words)
    except ValueError as error:
        return Output(f"Error: {error}", is_error=True)
    return Output(describe_settings(session.settings))


def _new(session: Session, words: list[str]) -> Output:
    session.new_problem()
    return Output("New Problem")


def _quit(session: Session, words: list[str]) -> Output:
    raise EOFError


_COMMANDS: dict[str, Callable[[Session, list[str]], Output]] = {
    "help": lambda session, words: Output(HELP),
    "settings": lambda session, words: Output(describe_settings(session.settings)),
    "vars": lambda session, words: Output(" ".join(sorted(session.scope.names())) or "(none)"),
    "new": _new,
    "set": _set,
    "quit": _quit,
    "q": _quit,
    "exit": _quit,
}


def _command(session: Session, line: str) -> Output:
    """A `:` command of the REPL itself."""
    name, *words = line[1:].split() or [""]
    handler = _COMMANDS.get(name)
    if handler is None:
        return Output(f"Error: unknown command :{name}; try :help", is_error=True)
    return handler(session, words)


def respond(session: Session, line: str, *, ascii_output: bool = False) -> Output | None:
    stripped = line.strip()
    if stripped == _APPROX_COMMAND or stripped.startswith(APPROX_PREFIX):
        entry = stripped[len(_APPROX_COMMAND) :]
        return evaluate_line(session, entry, ascii_output=ascii_output, approximate=True)
    if stripped.startswith(":") and not stripped.startswith(":="):
        return _command(session, stripped)
    return evaluate_line(session, line, ascii_output=ascii_output)


@dataclass(frozen=True, slots=True)
class ScriptOptions:
    ascii_output: bool = False
    echo: bool = True  # print each entry before its result
    keep_going: bool = False  # carry on after an error


def run_script(
    session: Session, lines: Iterable[str], out: TextIO, options: ScriptOptions | None = None
) -> int:
    """Run the entries of a script, printing each with its result. Returns the exit status.

    Blank lines and lines starting with `//` are skipped. The first error stops the script
    (status 1) unless `keep_going` is set.
    """
    options = options or ScriptOptions()
    status = 0
    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith(_COMMENT):
            continue
        output = respond(session, line, ascii_output=options.ascii_output)
        if output is None:
            continue
        if options.echo:
            print(f"{PROMPT}{line}", file=out)
        print(output.text, file=out)
        if output.is_error:
            status = 1
            print(f"(line {number})", file=out)
            if not options.keep_going:
                break
    return status


def _reader(session: Session) -> Callable[[str], str] | None:
    """A prompt with tab completion, or None if prompt_toolkit is not installed."""
    try:
        terminal = importlib.import_module("cassim.cli.terminal")
    except ImportError:
        return None
    return terminal.make_reader(session).prompt


def interactive(session: Session, *, ascii_output: bool = False) -> int:
    """Read entries until end of input. Uses prompt_toolkit when there is a terminal."""
    prompt = _reader(session) if sys.stdin.isatty() else None
    if sys.stdin.isatty():
        print("CASSim. :help for help, :quit to leave.")
    while True:
        try:
            if prompt is not None:
                line = prompt(PROMPT)
            else:
                line = input(PROMPT if sys.stdin.isatty() else "")
        except EOFError, KeyboardInterrupt:
            return 0
        try:
            output = respond(session, line, ascii_output=ascii_output)
        except EOFError:
            return 0
        if output is not None:
            print(output.text)


def build_settings(course: str | None, assignments: Iterable[str]) -> Settings:
    base = PRESETS[course] if course else Settings()
    return parse_settings(base, assignments)


def new_session(course: str | None, assignments: Iterable[str]) -> Session:
    return Session(build_settings(course, assignments))


def read_script(path: str) -> list[str]:
    if path == "-":
        return sys.stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8").splitlines()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cassim",
        description=(
            "A simulation of the TI-Nspire CX CAS. Starts the graphical app; with --text, -c, "
            "--ascii or run, the text interface."
        ),
    )
    parser.add_argument("--text", action="store_true", help="start the text REPL, not the app")
    parser.add_argument(
        "--web", action="store_true", help="open the graphical app in the browser, not a window"
    )
    parser.add_argument(
        "--view", choices=("handheld", "computer"), help="the app's view (default: as last used)"
    )
    parser.add_argument("--course", choices=sorted(PRESETS), help="start from a course preset")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=f"a setting ({', '.join(SETTING_KEYS)}); may be repeated",
    )
    parser.add_argument(
        "--ascii", action="store_true", help="print results in plain ASCII spelling"
    )
    parser.add_argument(
        "-c", dest="expression", metavar="ENTRY", help="evaluate one entry and exit"
    )
    commands = parser.add_subparsers(dest="command")
    run = commands.add_parser("run", help="run a script of entries, one per line (- for stdin)")
    run.add_argument("file")
    run.add_argument("--keep-going", action="store_true", help="carry on after an error")
    run.add_argument("--quiet", action="store_true", help="print results without the entries")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of the `cassim` command. Returns the exit status."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = _parser()
    args = parser.parse_args(argv)
    text = args.text or args.ascii or args.expression is not None or args.command == "run"
    if text and (args.web or args.view):
        parser.error("--web and --view are for the graphical app, not the text interface")
    try:
        settings = build_settings(args.course, args.set)
    except ValueError as error:
        print(f"cassim: {error}", file=sys.stderr)
        return 2
    if not text:
        from cassim.app.main import run  # noqa: PLC0415  (Flet is loaded only for the app)
        from cassim.devices.nspire.ui.state import Mode  # noqa: PLC0415

        view = Mode(args.view) if args.view else None
        # --course and --set change the settings; with neither, the app keeps its own
        run(web=args.web, view=view, settings=settings if args.course or args.set else None)
        return 0
    session = Session(settings)
    if args.command == "run":
        try:
            lines = read_script(args.file)
        except OSError as error:
            print(f"cassim: cannot read {args.file}: {error.strerror}", file=sys.stderr)
            return 2
        options = ScriptOptions(args.ascii, echo=not args.quiet, keep_going=args.keep_going)
        return run_script(session, lines, sys.stdout, options)
    if args.expression is not None:
        options = ScriptOptions(args.ascii, echo=False)
        return run_script(session, [args.expression], sys.stdout, options)
    return interactive(session, ascii_output=args.ascii)
