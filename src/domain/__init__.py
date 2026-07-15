"""Schicht 1: Domain-Modelle (Pydantic). Null Logik ausser Feld-Defaults/Validierung,
keine Imports aus anderen Schichten (settings.py ist Querschnitt, kein Layer).

Re-Export der Aggregate fuer bequeme Imports (`from src.domain import Deal`).
"""
from __future__ import annotations

from src.domain.account import Account
from src.domain.activity import Activity, ActivityType
from src.domain.contact import (
    Contact,
    Disposition,
    Influence,
    RelationshipStrength,
    RoleInDeal,
)
from src.domain.contact_history import ContactHistoryEntry
from src.domain.correction import Correction
from src.domain.deal import Deal, DealStage, Framework
from src.domain.meddpicc import (
    Confidence,
    DimensionAssessment,
    MeddpiccSnapshot,
    Momentum,
    Trend,
)

__all__ = [
    "Account",
    "Activity",
    "ActivityType",
    "Contact",
    "RoleInDeal",
    "Influence",
    "Disposition",
    "RelationshipStrength",
    "ContactHistoryEntry",
    "Correction",
    "Deal",
    "DealStage",
    "Framework",
    "Confidence",
    "DimensionAssessment",
    "MeddpiccSnapshot",
    "Momentum",
    "Trend",
]
