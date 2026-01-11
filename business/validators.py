from __future__ import annotations

import re
from datetime import datetime, date

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

class ValidationError(Exception):
    pass

def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format")

def validate_email(email: str) -> None:
    if not _EMAIL_RE.match(email):
        raise ValidationError("Invalid email format")

def validate_rating(rating: int) -> None:
    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5")

def validate_price(price: float) -> None:
    if price < 0:
        raise ValidationError("Price must be non-negative")
