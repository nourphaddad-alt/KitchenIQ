from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_phase_one_is_functional_default_workspace() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    assert not app.exception
    assert app.radio[0].options == [
        "Phase 1 · Audit & Profit",
        "Phase 2 · Most Valuable Promotion",
    ]
    assert any("Restaurant audit & profit foundation" in item.value for item in app.header)
    assert any("Platform Report Analysis" in item.value for item in app.header)
    assert not any("Specification ready" in item.value for item in app.markdown)


def test_phase_two_contains_simulator_ranking_and_target() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20)
    app.run()
    app.radio[0].set_value("Phase 2 · Most Valuable Promotion").run()

    assert not app.exception
    assert any("Most Valuable Promotion" in item.value for item in app.header)
    tab_labels = [tab.label for tab in app.tabs]
    assert tab_labels == [
        "Promotion simulator",
        "Offer guardrails",
        "MVP ranking",
        "17% target",
    ]
    assert not app.file_uploader


def test_phase_one_offers_working_mock_reports_for_supported_platforms() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()

    assert any(
        button.label == "Download Uber Eats mock report"
        for button in app.get("download_button")
    )
    platform = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Delivery Platform"
    )
    platform.set_value("Deliveroo").run()

    assert not app.exception
    assert any(
        button.label == "Download Deliveroo mock report"
        for button in app.get("download_button")
    )
