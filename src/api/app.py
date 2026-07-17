"""FastAPI — duenne Kompatibilitaets-Haut (P7).

Regeln (CLAUDE.md, bindend): Endpoints rufen exakt dieselben Funktionen wie
die CLI (process_note, analyze, Repository) — KEINE Businesslogik hier.
Fehlerbild: 404 unbekannte Entities, 409 Dedup-Treffer, 422 mit
Kandidatenliste, wenn die Entity-Resolution unter der Schwelle liegt
(die API kann nicht interaktiv nachfragen).

Start: uvicorn src.api.app:app --reload
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from src.domain.account import Account
from src.domain.contact import Contact
from src.domain.correction import Correction
from src.domain.deal import Deal
from src.domain.meddpicc import MeddpiccSnapshot
from src.orchestrator.ingest import IngestReport, process_note
from src.orchestrator.resolver import ResolutionUnclear

log = logging.getLogger("sales_os.api")

app = FastAPI(
    title="Sales OS API",
    description="Duenne Haut ueber den CLI-Funktionen — lokal, ohne Auth (V1).",
    version="0.7.0",
)


@app.middleware("http")
async def _reset_llm_budget(request, call_next):
    """Breaker-Zaehler gelten pro Nutzer-Aktion: im langlebigen Server-Prozess
    heisst das pro Request — sonst wuergt der Breaker die API nach kumulierten
    25 Calls dauerhaft ab (Befund 17.07., Regression-Test vorhanden)."""
    from src.agents import llm

    llm.reset_budget()
    return await call_next(request)


# ---------------------------------------------------------------- Request-/Response-Modelle

class IngestRequest(BaseModel):
    text: str = Field(description="Rohe Notiz (messy ok).")
    deal_name: str | None = Field(default=None, description="Uebersteuert die automatische Zuordnung.")
    source: str = Field(default="api", description="Herkunft, landet an der Activity.")


class AnalyzeRequest(BaseModel):
    notes: str = Field(description="Roh-Notes fuer die MEDDPICC-Analyse.")


class CorrectionRequest(BaseModel):
    deal_id: str
    field_path: str = Field(description="z.B. dimensions.champion.confidence")
    corrected_value: str
    comment: str = ""


class AdviseRequest(BaseModel):
    question: str = Field(description="Freie Sales-Frage an den Berater.")
    deal_name: str | None = Field(default=None, description="Deal-Vollkontext aus der DB.")
    pipeline: bool = Field(default=False, description="Kompakt-Digest aller Deals als Kontext.")
    topics: list[str] | None = Field(default=None, description="Nur passende Playbook-Abschnitte laden.")


class AdviseResponse(BaseModel):
    answer: str
    prompt_version: str


class DealDetail(BaseModel):
    """GET /deals/{id}: Deal inkl. Account, Kontakten, letztem Snapshot, Korrekturen."""

    deal: Deal
    account: Account
    contacts: list[Contact]
    latest_snapshot: MeddpiccSnapshot | None
    corrections: list[Correction]


class CandidateOut(BaseModel):
    deal: Deal
    confidence: float


# ---------------------------------------------------------------- Endpoints

@app.post("/ingest", response_model=IngestReport)
def post_ingest(body: IngestRequest):
    """Kompletter Ingestion-Durchlauf — dieselbe Funktion wie `cli ingest`."""
    try:
        report = process_note(body.text, deal_name=body.deal_name, source=body.source, ask=None)
    except ResolutionUnclear as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(e),
                "candidates": [
                    CandidateOut(deal=deal, confidence=score).model_dump(mode="json")
                    for deal, score in e.candidates
                ],
                "hint": "deal_name im Request setzen — die API kann nicht interaktiv nachfragen.",
            },
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if report.aborted:
        raise HTTPException(status_code=409, detail=report.aborted)
    return report


@app.post("/advise", response_model=AdviseResponse)
def post_advise(body: AdviseRequest):
    """Der Berater — dieselbe Funktion wie `cli advise` (one-shot, stateless;
    Mehrrunden-Verlauf ist bewusst ein CLI-Session-Feature)."""
    from src.agents.advisor.agent import advise
    from src.agents.advisor.prompts import PROMPT_VERSION

    try:
        answer, _ = advise(
            body.question, deal_name=body.deal_name, pipeline=body.pipeline, topics=body.topics
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AdviseResponse(answer=answer, prompt_version=PROMPT_VERSION)


@app.post("/deals/{deal_id}/analyze", response_model=MeddpiccSnapshot)
def post_analyze(deal_id: str, body: AnalyzeRequest):
    """Analyse fuer einen bekannten Deal — dieselbe Funktion wie `cli analyze --deal`."""
    from src.agents.meddpicc.agent import analyze
    from src.repository.deals import get_deal
    from src.repository.snapshots import get_latest_snapshot, save_snapshot

    try:
        deal = get_deal(deal_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    previous = get_latest_snapshot(deal.id)
    try:
        snapshot = analyze(body.notes, previous_snapshot=previous, deal=deal)
    except ValueError as e:  # z.B. leere Notes
        raise HTTPException(status_code=422, detail=str(e))
    return save_snapshot(snapshot)


@app.get("/deals", response_model=list[Deal])
def get_deals():
    from src.repository.deals import list_deals

    return list_deals()


@app.get("/deals/{deal_id}", response_model=DealDetail)
def get_deal_detail(deal_id: str):
    from src.repository.accounts import get_account
    from src.repository.contacts import list_contacts
    from src.repository.corrections import get_corrections
    from src.repository.deals import get_deal
    from src.repository.snapshots import get_latest_snapshot

    try:
        deal = get_deal(deal_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    account = get_account(deal.account_id)
    return DealDetail(
        deal=deal,
        account=account,
        contacts=list_contacts(account.id),
        latest_snapshot=get_latest_snapshot(deal.id),
        corrections=get_corrections(deal.id),
    )


@app.post("/corrections", response_model=Correction)
def post_correction(body: CorrectionRequest):
    """Feedback sammeln — dieselbe Funktion wie `cli correct` (Injektion nach M4)."""
    from src.agents.meddpicc.agent import AGENT_NAME
    from src.repository.corrections import record_correction
    from src.repository.deals import get_deal

    try:
        get_deal(body.deal_id)  # 404 statt stiller Waisen-Korrektur
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return record_correction(
        body.deal_id, AGENT_NAME, body.field_path, body.corrected_value, body.comment
    )


@app.get("/export/csv")
def export_csv(entity: Literal["deals", "contacts", "activities"]):
    """CSV-Export je Entitaet (Kompatibilitaet mit Fremdsoftware)."""
    from src.repository.activities import list_all_activities
    from src.repository.contacts import list_all_contacts
    from src.repository.deals import list_deals

    rows = {
        "deals": list_deals,
        "contacts": list_all_contacts,
        "activities": list_all_activities,
    }[entity]()

    buffer = io.StringIO()
    if rows:
        fieldnames = list(rows[0].model_dump(mode="json").keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for item in rows:
            writer.writerow(item.model_dump(mode="json"))
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{entity}.csv"'},
    )
