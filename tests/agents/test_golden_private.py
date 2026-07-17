"""Privat-Ablage fuer Golden-Referenzen aus echten Deals (Entscheidung Lion 17.07.2026):
Kundenzitate duerfen nie ins public Repo — private/-Unterordner sind gitignored,
der Eval scannt sie aber mit."""

from pathlib import Path

from src.agents.meddpicc.evaluation import find_golden_cases

_EXPECTED = """# Soll-Bewertung — {account}
## Metrics
- Confidence: UNBEKANNT
## Gesamt
- Overall score (0–100): 20
- Momentum (POSITIV / NEUTRAL / NEGATIV): NEUTRAL
"""


def _make_case(golden_dir: Path, notes_dir: Path, account: str, n_notes: int = 2) -> None:
    golden_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    (golden_dir / f"{account}_{n_notes:02d}.expected.md").write_text(
        _EXPECTED.format(account=account), encoding="utf-8"
    )
    for i in range(1, n_notes + 1):
        (notes_dir / f"{account}_{i:02d}.txt").write_text(f"note {i}", encoding="utf-8")


def test_private_subdirs_are_scanned(tmp_path):
    golden, notes = tmp_path / "golden", tmp_path / "notes"
    _make_case(golden, notes, "synthcase")
    _make_case(golden / "private", notes / "private", "echtkunde", n_notes=3)

    cases = find_golden_cases(golden, notes)

    accounts = sorted(exp.account for exp, _ in cases)
    assert accounts == ["echtkunde", "synthcase"]
    echt = next(nf for exp, nf in cases if exp.account == "echtkunde")
    assert len(echt) == 3
    assert all("private" in str(p) for p in echt)


def test_private_expected_without_notes_fails_loud(tmp_path):
    golden, notes = tmp_path / "golden", tmp_path / "notes"
    _make_case(golden, notes, "synthcase")
    (golden / "private").mkdir(parents=True)
    (golden / "private" / "verwaist_01.expected.md").write_text(
        _EXPECTED.format(account="verwaist"), encoding="utf-8"
    )

    try:
        find_golden_cases(golden, notes)
        raise AssertionError("erwartete FileNotFoundError fuer verwaiste Privat-Referenz")
    except FileNotFoundError as e:
        assert "verwaist" in str(e)
