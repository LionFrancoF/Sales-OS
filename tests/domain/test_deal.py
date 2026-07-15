"""Tests fuer das Deal-Modell inkl. Win-%-Ableitung aus der Stage."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.config.settings import STAGE_GATES
from src.domain.deal import Deal


def test_deal_win_probability_derived_from_stage():
    d = Deal(account_id="acc-1", name="Acme Platform", stage="EVALUATION")
    assert d.win_probability == STAGE_GATES["EVALUATION"]["win"]


def test_deal_win_probability_override_kept():
    d = Deal(account_id="acc-1", name="Acme Platform", stage="EVALUATION", win_probability=55)
    assert d.win_probability == 55


def test_deal_default_stage_is_prospect():
    d = Deal(account_id="acc-1", name="New Logo")
    assert d.stage == "PROSPECT"
    assert d.win_probability == STAGE_GATES["PROSPECT"]["win"]


def test_deal_invalid_stage():
    with pytest.raises(ValidationError):
        Deal(account_id="acc-1", name="X", stage="ONBOARDING")


@pytest.mark.parametrize("bad_win", [-1, 101, 150])
def test_deal_win_probability_out_of_range(bad_win):
    with pytest.raises(ValidationError):
        Deal(account_id="acc-1", name="X", win_probability=bad_win)


def test_deal_negative_amount_invalid():
    with pytest.raises(ValidationError):
        Deal(account_id="acc-1", name="X", amount_estimate=-10.0)
