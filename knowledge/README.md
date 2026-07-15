# knowledge/ — Playbooks (kuratiertes Wissen)

Hier liegt Lions Sales-Wissen als Markdown-Playbooks. Agenten ziehen sich
**relevante Abschnitte** über `src/knowledge/loader.py` in ihren System-Prompt
(Knowledge-Injection) — die Ratgeber-Qualität entsteht durch dieses kuratierte
Wissen, nicht durch Training.

## ⚠️ Privat — nicht im Repo
Die Playbook-Inhalte sind persönliches Sales-IP und **gitignored** (nur diese
README ist committed; das Repo ist public). Konsequenz: **kein Git-Backup** für
diese Dateien — den Ordner separat sichern (Time Machine, Drive o.ä.).

## Format
Jede Datei: YAML-Frontmatter + Abschnitte mit `<!-- topic: x -->`-Markern:

```markdown
---
topics: [champion, metrics]
agents: [meddpicc_analyzer, meeting_prep]
status: FREIGEGEBEN (Lion, 07/2026)
---

# Mein Playbook

## Champion
<!-- topic: champion -->
- Regel ...
```

- `agents`: welche Agenten die Datei komplett laden (`load_for("meddpicc_analyzer")`).
- `topics`: wofür die Datei relevant ist; mit `load_for(agent, topics=[...])`
  werden nur die passenden `<!-- topic: x -->`-Abschnitte geladen (z.B. lädt
  Account-Map nur `champion` + `stakeholder`).
- `status`: `FREIGEGEBEN` = wird geladen · `STUB` = wird übersprungen, bis gefüllt.
- Datei ohne Marker = ein Abschnitt. Physisches Splitten erst, wenn eine Datei
  unhandlich wird.

## Limit-Verhalten
Überschreitet die Auswahl `KNOWLEDGE_CHAR_LIMIT` (settings.py, 24.000), schlägt
der Loader **laut fehl** (ValueError mit Aufstellung) — es wird nie still
gekürzt. Dann: Topics schärfen oder Limit bewusst erhöhen.

## Eigenes Wissen hinzufügen (Kurzfassung)
1. Neue `.md` hier ablegen, Frontmatter (`topics`, `agents`, `status: FREIGEGEBEN`) setzen.
2. Inhalt in Abschnitte mit `<!-- topic: x -->` gliedern.
3. Fertig — der Loader findet sie automatisch, nichts zu registrieren.
