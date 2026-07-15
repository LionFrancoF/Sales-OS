# knowledge/ — Playbooks (kuratiertes Wissen)

Hier liegt das kuratierte Sales-Wissen als Markdown-Playbooks. Agenten ziehen
sich **relevante Abschnitte** in ihren System-Prompt (Knowledge-Injection) —
so entsteht die Ratgeber-Qualität nicht durch Training, sondern durch dein
Playbook. Die Dateien selbst kommen in **Schicht 3 (P3)**, der Loader
(`src/knowledge/loader.py`) ebenfalls.

## Format (ab P3)
Jede `.md`-Datei beginnt mit YAML-Frontmatter und ist intern in markierte
Abschnitte mit eigenen Topic-Tags gegliedert:

```markdown
---
topics: [meddpicc, champion, discovery]
agents: [meddpicc, meeting_prep]
---

<!-- section: champion topics: [champion, stakeholder] -->
## Champion vs. Coach
...
```

Der Loader kann so auf **Abschnitts-Ebene** selektieren (z. B. Account-Map lädt
nur `champion` + `stakeholder`). Physisches Splitten in Einzeldateien erst,
wenn eine Datei unhandlich wird.

## Eigenes Wissen hinzufügen (Kurzfassung)
1. Neue `.md` in `knowledge/` anlegen, Frontmatter (`topics`, `agents`) setzen.
2. Inhalt in Abschnitte mit `<!-- section: ... -->`-Markern gliedern.
3. Fertig — der Loader wählt passende Abschnitte automatisch je Agent/Topic.
