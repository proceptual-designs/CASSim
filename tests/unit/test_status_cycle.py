from cassim.core.settings import Settings, next_choice, updated


def test_status_click_cycles() -> None:
    """Clicking the title-bar status: Rad<->Deg, Auto<->Approx, Real->Rect->Polar->Real."""
    s = Settings()
    assert next_choice(s, "angle") == "degree"
    assert next_choice(updated(s, {"angle": "degree"}), "angle") == "radian"
    assert next_choice(updated(s, {"angle": "gradian"}), "angle") == "radian"
    assert next_choice(s, "calc") == "approximate"
    assert next_choice(updated(s, {"calc": "exact"}), "calc") == "auto"
    domains = ("real", "rectangular", "polar")
    assert [next_choice(updated(s, {"domain": d}), "domain") for d in domains] == [
        "rectangular",
        "polar",
        "real",
    ]
