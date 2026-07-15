"""Tests fuer den Knowledge-Loader (Auswahl-Logik, Limit, leerer Ordner).

Alle Fixtures sind synthetisch (tmp_path) — echte Playbooks sind gitignored
und duerfen in Tests nicht vorausgesetzt werden.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.knowledge.loader import load_for


def _write(directory: Path, name: str, text: str) -> None:
    (directory / name).write_text(text, encoding="utf-8")


ALPHA = """---
topics: [champion, metrics]
agents: [analyzer]
status: FREIGEGEBEN
---

# Alpha Playbook

## Champion-Kapitel
<!-- topic: champion -->
- Regel C1: Champion braucht Einfluss.

## Metrics-Kapitel
<!-- topic: metrics -->
- Regel M1: Kundenzahlen zaehlen.
"""

BETA = """---
topics: [objections]
agents: [meeting_prep]
---

# Beta Playbook

Einwand-Wissen ohne Abschnitts-Marker.
"""


@pytest.fixture()
def kdir(tmp_path: Path) -> Path:
    _write(tmp_path, "alpha.md", ALPHA)
    _write(tmp_path, "beta.md", BETA)
    _write(tmp_path, "README.md", "# wird nie geladen")
    return tmp_path


def test_agent_selection_loads_whole_file(kdir: Path):
    block = load_for("analyzer", base_dir=kdir)
    assert "Regel C1" in block and "Regel M1" in block  # ganze Datei
    assert "Beta Playbook" not in block  # anderer Agent
    assert "wird nie geladen" not in block  # README ausgeschlossen
    assert "=== knowledge/alpha.md ===" in block  # Trenner


def test_topic_filters_on_section_level(kdir: Path):
    block = load_for("analyzer", topics=["champion"], base_dir=kdir)
    assert "Regel C1" in block
    assert "Regel M1" not in block  # metrics-Abschnitt nicht angefragt
    assert "=== knowledge/alpha.md :: champion ===" in block
    assert "# Alpha Playbook" in block  # Praeambel als Kontext dabei


def test_topic_overlap_matches_file_without_agent(kdir: Path):
    # 'research' steht in keiner agents-Liste, aber topics matchen die Datei.
    block = load_for("research", topics=["metrics"], base_dir=kdir)
    assert "Regel M1" in block and "Regel C1" not in block


def test_markerless_file_loaded_whole_on_topic_match(kdir: Path):
    block = load_for("meeting_prep", topics=["objections"], base_dir=kdir)
    assert "Einwand-Wissen ohne Abschnitts-Marker." in block


def test_no_match_returns_empty(kdir: Path):
    assert load_for("unbekannter_agent", base_dir=kdir) == ""
    assert load_for("analyzer", topics=["gibt_es_nicht"], base_dir=kdir) == ""


def test_empty_and_missing_dir_return_empty(tmp_path: Path):
    assert load_for("analyzer", base_dir=tmp_path) == ""
    assert load_for("analyzer", base_dir=tmp_path / "nope") == ""


def test_over_limit_raises_loudly(kdir: Path):
    with pytest.raises(ValueError) as exc:
        load_for("analyzer", base_dir=kdir, limit=50)
    msg = str(exc.value)
    assert "ueberschreitet das Limit" in msg
    assert "alpha.md" in msg  # Aufstellung nennt die Quelle
    assert "NICHT still" in msg


def test_frontmatter_missing_agents_tolerated(tmp_path: Path):
    _write(tmp_path, "gamma.md", "---\ntopics: [foo]\n---\n\nInhalt gamma.\n")
    # kein agents-Key: via Topic erreichbar, via Agent nicht — kein Crash.
    assert "Inhalt gamma." in load_for("x", topics=["foo"], base_dir=tmp_path)
    assert load_for("x", base_dir=tmp_path) == ""


def test_stub_files_are_skipped(tmp_path: Path):
    _write(
        tmp_path,
        "stub.md",
        "---\ntopics: [champion]\nagents: [analyzer]\nstatus: STUB (von Lion zu fuellen)\n---\n\nLeeres Skelett.\n",
    )
    assert load_for("analyzer", base_dir=tmp_path) == ""


def test_more_topic_hits_ranked_first(tmp_path: Path):
    _write(tmp_path, "zwei_treffer.md", ALPHA)  # matcht champion UND metrics
    _write(
        tmp_path,
        "ein_treffer.md",
        "---\ntopics: [champion]\nagents: []\n---\n\n## C\n<!-- topic: champion -->\n- nur einer\n",
    )
    block = load_for("x", topics=["champion", "metrics"], base_dir=tmp_path)
    assert block.index("zwei_treffer.md") < block.index("ein_treffer.md")
