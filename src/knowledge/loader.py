"""Knowledge-Loader: waehlt Playbook-Dateien/-Abschnitte fuer einen Agenten aus.

Injection-Prinzip (CLAUDE.md, Schicht 2): Agenten ziehen sich relevante
Playbook-Abschnitte als Block in ihren System-Prompt. Auswahl auf zwei Ebenen:
- Datei-Ebene: YAML-Frontmatter mit `agents: [...]` und `topics: [...]`
- Abschnitts-Ebene: `<!-- topic: xyz -->`-Marker im Text (Format der
  Nutzer-Playbooks). Eine Datei ohne Marker zaehlt als ein Abschnitt.

Limit-Verhalten (P-1 Befund 3.2/4.5, Entscheidung Lion): Ueberschreitet die
Auswahl das Zeichen-Limit, schlaegt der Loader LAUT mit ValueError und einer
Groessen-Aufstellung fehl — es wird NIEMALS still trunkiert. Der Nutzer
schaerft dann die Topics oder erhoeht KNOWLEDGE_CHAR_LIMIT bewusst.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from src.config import settings

log = logging.getLogger("sales_os.knowledge")

# Repo-Root/knowledge — relativ zu dieser Datei (src/knowledge/loader.py).
KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"

_SECTION_MARKER = re.compile(r"<!--\s*topic:\s*([\w-]+)\s*-->")
_LIST_VALUE = re.compile(r"^\[(.*)\]$")


@dataclass
class _Part:
    """Ein selektierter Textbaustein (Praeambel oder Abschnitt) einer Datei."""

    file: str
    topic: str | None  # None = Praeambel (Titel/Einleitung vor dem ersten Marker)
    text: str

    @property
    def header(self) -> str:
        if self.topic is None:
            return f"=== knowledge/{self.file} ==="
        return f"=== knowledge/{self.file} :: {self.topic} ==="

    def render(self) -> str:
        return f"{self.header}\n{self.text.strip()}"


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Parst minimales YAML-Frontmatter (topics/agents/status) ohne yaml-Dependency.

    Unterstuetzt nur `key: wert` und `key: [a, b, c]` — mehr braucht das Format
    nicht; eine pyyaml-Dependency fuer 3 Keys waere Overkill.
    """
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    header, body = raw[3:end], raw[end + 4 :].lstrip("\n")
    meta: dict = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not key:
            continue
        m = _LIST_VALUE.match(value)
        if m:
            meta[key] = [v.strip() for v in m.group(1).split(",") if v.strip()]
        else:
            meta[key] = value
    return meta, body


def _split_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Zerlegt einen Datei-Body an `<!-- topic: x -->`-Markern.

    Liefert (praeambel, [(topic, text), ...]). Der Marker gehoert zum Abschnitt
    dahinter; die Ueberschriftzeile VOR dem Marker (z.B. `## Champion`) wird dem
    Abschnitt zugeschlagen, damit Abschnitte selbsterklaerend bleiben.
    """
    matches = list(_SECTION_MARKER.finditer(body))
    if not matches:
        return body, []

    # Abschnitts-Start = Beginn der Ueberschriftzeile direkt vor dem Marker
    # (falls vorhanden), sonst der Marker selbst.
    starts: list[int] = []
    for m in matches:
        line_start = body.rfind("\n", 0, m.start()) + 1
        prev_line_end = line_start - 1
        prev_line_start = body.rfind("\n", 0, max(prev_line_end, 0)) + 1
        prev_line = body[prev_line_start:prev_line_end] if prev_line_end > 0 else ""
        starts.append(prev_line_start if prev_line.lstrip().startswith("#") else line_start)

    preamble = body[: starts[0]]
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        end = starts[i + 1] if i + 1 < len(matches) else len(body)
        sections.append((m.group(1), body[starts[i] : end]))
    return preamble, sections


def load_for(
    agent: str,
    topics: list[str] | None = None,
    *,
    limit: int | None = None,
    base_dir: Path | None = None,
) -> str:
    """Baut den injizierbaren Knowledge-Block fuer einen Agenten.

    Auswahl-Logik:
    - Eine Datei ist Kandidat, wenn `agent` in ihrem `agents:`-Frontmatter steht
      ODER (bei gesetzten `topics`) ihre `topics:` sich damit ueberschneiden.
    - Ohne `topics`-Parameter wird die ganze Kandidaten-Datei geladen.
    - Mit `topics` werden nur Abschnitte geladen, deren `<!-- topic: x -->`-Tag
      in `topics` liegt (plus Praeambel der Datei als Kontext); eine Datei ohne
      Marker wird komplett geladen, wenn ihre Datei-Topics passen.
    - Sortierung: Dateien mit mehr Topic-Treffern zuerst, dann alphabetisch.

    Wirft ValueError, wenn der Block das Limit ueberschreitet (nie still kuerzen).
    """
    directory = base_dir if base_dir is not None else KNOWLEDGE_DIR
    max_chars = limit if limit is not None else settings.KNOWLEDGE_CHAR_LIMIT
    if not directory.is_dir():
        return ""

    files: list[tuple[int, str, list[_Part]]] = []  # (match_score, name, parts)
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        status = str(meta.get("status", ""))
        if status.upper().startswith("STUB"):
            continue  # leere Skelette nicht in Prompts injizieren (Rauschen)
        file_agents = meta.get("agents") or []
        file_topics = meta.get("topics") or []
        agent_match = agent in file_agents
        topic_overlap = bool(topics) and bool(set(topics) & set(file_topics))
        if not (agent_match or topic_overlap):
            continue

        preamble, sections = _split_sections(body)
        parts: list[_Part] = []
        if topics:
            wanted = [(t, txt) for t, txt in sections if t in topics]
            if wanted:
                if preamble.strip():
                    parts.append(_Part(path.name, None, preamble))
                parts.extend(_Part(path.name, t, txt) for t, txt in wanted)
            elif not sections and topic_overlap:
                parts.append(_Part(path.name, None, body))  # markerlose Datei
            score = len(wanted)
        else:
            parts.append(_Part(path.name, None, body))  # ganze Datei fuer den Agenten
            score = 0

        if parts:
            files.append((score, path.name, parts))

    files.sort(key=lambda f: (-f[0], f[1]))
    all_parts = [part for _, _, parts in files for part in parts]
    if not all_parts:
        return ""

    block = "\n\n".join(part.render() for part in all_parts)
    if len(block) > max_chars:
        breakdown = "\n".join(f"  - {p.header}: {len(p.text):,} Zeichen" for p in all_parts)
        raise ValueError(
            f"Knowledge-Auswahl fuer agent='{agent}' topics={topics} umfasst "
            f"{len(block):,} Zeichen und ueberschreitet das Limit von {max_chars:,}.\n"
            f"Auswahl:\n{breakdown}\n"
            "Optionen: topics schaerfen ODER KNOWLEDGE_CHAR_LIMIT in "
            "src/config/settings.py bewusst erhoehen. Es wird NICHT still gekuerzt."
        )

    log.info(
        "knowledge geladen: agent=%s topics=%s teile=%d zeichen=%d",
        agent, topics, len(all_parts), len(block),
    )
    return block
