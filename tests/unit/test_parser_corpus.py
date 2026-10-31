"""Every corpus line must parse, whatever the review status of the expected value.

These tests use only the syntax of the captured text, so they do not depend on the engine.
Entries are parsed as lines and displayed results as single expressions, since the replay
harness will compare results by parsing them.
"""

from pathlib import Path

import pytest
import yaml

from emcas.core.lexer import Kind, tokenize
from emcas.core.parser import parse, parse_expression

SEED = Path(__file__).parents[2] / "corpus" / "seed"
# Status words shown in the results column rather than a value.
NOT_EXPRESSIONS = {"Done"}


def corpus_steps():
    for path in sorted(SEED.glob("*.yaml")):
        for case in yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]:
            for number, step in enumerate(case["steps"]):
                if "in" in step:
                    yield f"{case['id']}#{number}", step


STEPS = dict(corpus_steps())
# Entries the emulator rejected are not all parseable, and the parser need not read them.
ENTRIES = {key: step["in"] for key, step in STEPS.items() if not step.get("error")}
RESULTS = {
    key: step["out"]
    for key, step in STEPS.items()
    if isinstance(step.get("out"), str) and step["out"] not in NOT_EXPRESSIONS
}


@pytest.mark.parametrize("key", ENTRIES)
def test_entry_parses_and_round_trips(key):
    tree = parse(ENTRIES[key])
    assert tree.statements
    assert parse(str(tree)) == tree


@pytest.mark.parametrize("key", RESULTS)
def test_result_parses_and_round_trips(key):
    tree = parse_expression(RESULTS[key])
    assert parse_expression(str(tree)) == tree


def test_no_entry_types_a_capital_t_for_the_transpose():
    assert not [key for key, text in ENTRIES.items() if "^T" in text], "type the transpose as @t"


@pytest.mark.parametrize("key", RESULTS)
def test_result_uses_the_euler_constant_not_a_variable_e(key):
    names = [t.text for t in tokenize(RESULTS[key]) if t.kind is Kind.NAME]
    assert "e" not in names, "the calculator shows Euler's constant as ⅇ"
    assert "E" not in names
