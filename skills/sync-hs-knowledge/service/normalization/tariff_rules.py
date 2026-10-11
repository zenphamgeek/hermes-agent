"""Tariff Schedules and Rates Normalizer (FR-070 - FR-074)."""

import re
from datetime import date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import TariffSchedule, TariffRate
from service.parsers.vietnamese import normalize_vietnamese_text


class NormalizedTariffRate(BaseModel):
    hs_code: str
    rate_type: str = "ad_valorem"  # ad_valorem, specific, compound, mixed
    rate_value: Optional[float] = None
    rate_unit: Optional[str] = "%"
    condition_text: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None


class TariffNormalizer:
    @staticmethod
    def parse_rate_string(raw_rate: str) -> tuple[str, Optional[float], Optional[str], Optional[str]]:
        """Parses rate strings like '5%', '0%', '10 USD/kg', 'Miễn thuế'."""
        text = raw_rate.strip()
        if not text or text == "-" or text.lower() == "kct":
            return "exempt", 0.0, "%", None

        # Check percentage e.g. 5% or 5.5%
        pct_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%', text)
        if pct_match:
            return "ad_valorem", float(pct_match.group(1)), "%", None

        # Check raw number
        num_match = re.match(r'^([0-9]+(?:\.[0-9]+)?)$', text)
        if num_match:
            return "ad_valorem", float(num_match.group(1)), "%", None

        return "conditional", None, None, normalize_vietnamese_text(text)

    def save_rates_to_db(self, schedule_id: str, rates: List[NormalizedTariffRate], db: Session):
        for r in rates:
            rate_obj = TariffRate(
                schedule_id=schedule_id,
                hs_code=r.hs_code,
                rate_type=r.rate_type,
                rate_value=r.rate_value,
                rate_unit=r.rate_unit,
                condition_text=r.condition_text,
                valid_from=r.valid_from,
                valid_to=r.valid_to
            )
            db.add(rate_obj)
        db.commit()
