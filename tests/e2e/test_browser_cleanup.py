"""Verify browser contexts do not survive a test or a failing fixture."""

from pathlib import Path

import pytest
from playwright.sync_api import Browser

pytestmark = pytest.mark.e2e
pytest_plugins = ("pytester",)


def test_contexts_are_cleaned_between_tests(pytester: pytest.Pytester, browser: Browser) -> None:
    assert browser.is_connected()
    root = Path(__file__).resolve().parents[2]
    pytester.makeconftest(
        f'import sys\nsys.path.insert(0, {str(root)!r})\npytest_plugins = ("tests.e2e.conftest",)'
    )
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def failed_setup(browser):
            browser.new_context()
            browser.new_page()
            raise RuntimeError("deliberate setup failure")

        def test_success(browser):
            assert not browser.contexts
            browser.new_context()
            browser.new_page()
            assert len(browser.contexts) == 2

        @pytest.mark.xfail(strict=True, raises=AssertionError)
        def test_failure(browser):
            assert not browser.contexts
            browser.new_context()
            browser.new_page()
            assert len(browser.contexts) == 2
            raise AssertionError("deliberate test failure")

        @pytest.mark.xfail(strict=True, raises=RuntimeError)
        def test_setup_failure(failed_setup):
            pass

        def test_clean_after_failures(browser):
            assert not browser.contexts
        """
    )
    result = pytester.runpytest_subprocess("-o", "addopts=", "-v")
    result.assert_outcomes(passed=2, xfailed=2)
