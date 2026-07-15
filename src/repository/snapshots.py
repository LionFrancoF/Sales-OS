"""Repository: MeddpiccSnapshots (append-only, versioniert — nie ueberschreiben)."""
from __future__ import annotations

from src.domain.meddpicc import MeddpiccSnapshot
from src.repository import db
from src.repository._serde import dump_json, load_json


def _to_row(s: MeddpiccSnapshot) -> dict:
    d = s.model_dump(mode="json")
    for json_col in ("source_activity_ids", "dimensions", "deal_risks", "next_best_questions"):
        d[json_col] = dump_json(d[json_col])
    return d


def _from_row(row) -> MeddpiccSnapshot:
    d = dict(row)
    d["source_activity_ids"] = load_json(d["source_activity_ids"], [])
    d["dimensions"] = load_json(d["dimensions"], {})
    d["deal_risks"] = load_json(d["deal_risks"], [])
    d["next_best_questions"] = load_json(d["next_best_questions"], [])
    return MeddpiccSnapshot(**d)


def save_snapshot(snapshot: MeddpiccSnapshot) -> MeddpiccSnapshot:
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO snapshots (id, deal_id, created_at, source_activity_ids,
               framework, framework_rationale, dimensions, overall_score, score_rationale,
               momentum, deal_risks, next_best_questions, summary_for_manager, prompt_version)
               VALUES (:id, :deal_id, :created_at, :source_activity_ids,
               :framework, :framework_rationale, :dimensions, :overall_score, :score_rationale,
               :momentum, :deal_risks, :next_best_questions, :summary_for_manager, :prompt_version)""",
            _to_row(snapshot),
        )
    return snapshot


def get_latest_snapshot(deal_id: str) -> MeddpiccSnapshot | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE deal_id = ? ORDER BY created_at DESC LIMIT 1",
            (deal_id,),
        ).fetchone()
    return _from_row(row) if row else None


def list_snapshots(deal_id: str) -> list[MeddpiccSnapshot]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE deal_id = ? ORDER BY created_at", (deal_id,)
        ).fetchall()
    return [_from_row(r) for r in rows]
