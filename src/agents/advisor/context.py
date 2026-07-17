"""Kontext-Assembler des Beraters: liest AUSSCHLIESSLICH ueber das Repository.

Wiederverwendbarer Baustein (Wachstums-Regel): spaetere Module (Meeting-Prep,
Pipeline-Briefing) duerfen dieselben Funktionen nutzen. Reine Daten-Aufbereitung,
kein LLM — dadurch ohne Mocks testbar.
"""
from __future__ import annotations

from src.domain.contact import Contact
from src.domain.deal import Deal
from src.domain.meddpicc import MeddpiccSnapshot
from src.repository.accounts import get_account
from src.repository.activities import list_activities
from src.repository.contacts import list_contacts
from src.repository.deals import get_deal_by_name, list_deals
from src.repository.snapshots import get_latest_snapshot

# Wieviele Activities in den Deal-Kontext gehen (juengste zuerst); die juengste
# zusaetzlich mit Roh-Text — aeltere nur als Kurzzeile (Kostengrenze analog
# Analyzer-Kontextgrenze: nie die komplette Roh-Historie).
_MAX_ACTIVITIES = 5


def _render_contact(c: Contact) -> str:
    bits = [c.name]
    if c.title:
        bits.append(c.title)
    align = [
        f"Rolle: {c.role_in_deal}" if c.role_in_deal else None,
        f"Einfluss: {c.influence}" if c.influence else None,
        f"Haltung: {c.disposition}" if c.disposition else None,
        f"Beziehung: {c.relationship_strength}" if c.relationship_strength else None,
    ]
    align_txt = ", ".join(a for a in align if a)
    return f"- {' | '.join(bits)}" + (f" ({align_txt})" if align_txt else "")


def _render_snapshot(s: MeddpiccSnapshot) -> str:
    lines = [
        f"Letzte MEDDPICC-Analyse ({s.created_at:%d.%m.%Y}, Score {s.overall_score}, "
        f"Momentum {s.momentum}):",
        f"  Momentum-Begruendung: {s.momentum_rationale}",
    ]
    for key, dim in s.dimensions.items():
        lines.append(f"  - {key}: {dim.confidence} — {dim.findings}")
        if dim.gaps:
            lines.append(f"    Luecken: {'; '.join(dim.gaps)}")
    if s.deal_risks:
        lines.append("  Risiken: " + " | ".join(s.deal_risks))
    if s.next_best_questions:
        lines.append("  Offene beste Fragen: " + " | ".join(s.next_best_questions))
    return "\n".join(lines)


def build_deal_context(deal_name: str) -> str:
    """Vollkontext EINES Deals: Account, Deal, Kontakte, letzter Snapshot, Activities.

    Wirft LookupError, wenn der Deal nicht existiert (CLI meldet das sauber)."""
    deal: Deal = get_deal_by_name(deal_name)
    account = get_account(deal.account_id)
    contacts = list_contacts(account.id)
    snapshot = get_latest_snapshot(deal.id)
    activities = sorted(list_activities(deal.id), key=lambda a: a.occurred_at, reverse=True)

    parts = [
        f"=== DEAL-KONTEXT: {deal.name} @ {account.name} ===",
        f"Stage: {deal.stage} (Win {deal.win_probability}%)"
        + (f" | Close-Reason: {deal.close_reason}" if deal.close_reason else ""),
        f"Account: {account.name}"
        + (f", Branche: {account.industry}" if account.industry else "")
        + (f", Groesse: {account.size_estimate}" if account.size_estimate else ""),
    ]
    if contacts:
        parts.append("Kontakte:\n" + "\n".join(_render_contact(c) for c in contacts))
    else:
        parts.append("Kontakte: (keine erfasst)")
    if snapshot:
        parts.append(_render_snapshot(snapshot))
    else:
        parts.append("Noch keine MEDDPICC-Analyse vorhanden.")
    if activities:
        recent = activities[:_MAX_ACTIVITIES]
        lines = ["Juengste Activities (neueste zuerst):"]
        for i, a in enumerate(recent):
            lines.append(f"- {a.occurred_at:%d.%m.%Y} {a.type}: {a.summary or '(ohne Summary)'}")
            if i == 0:
                lines.append(f"  Roh-Text der juengsten Note:\n{a.raw_text}")
        if len(activities) > len(recent):
            lines.append(f"(+ {len(activities) - len(recent)} aeltere Activities nicht gelistet)")
        parts.append("\n".join(lines))
    else:
        parts.append("Noch keine Activities erfasst.")
    return "\n\n".join(parts)


def build_pipeline_context() -> str:
    """Kompakt-Digest ALLER Deals fuer pipeline-uebergreifende Fragen. Kein LLM."""
    deals = list_deals()
    if not deals:
        return "=== PIPELINE-KONTEXT ===\n(keine Deals in der DB)"
    lines = [f"=== PIPELINE-KONTEXT ({len(deals)} Deals) ==="]
    for deal in deals:
        account = get_account(deal.account_id)
        snapshot = get_latest_snapshot(deal.id)
        line = f"- {deal.name} @ {account.name} | Stage {deal.stage} (Win {deal.win_probability}%)"
        if snapshot:
            line += f" | Score {snapshot.overall_score}, Momentum {snapshot.momentum}"
            if snapshot.deal_risks:
                line += f" | Top-Risiken: {'; '.join(snapshot.deal_risks[:2])}"
        else:
            line += " | (noch keine Analyse)"
        lines.append(line)
    return "\n".join(lines)
