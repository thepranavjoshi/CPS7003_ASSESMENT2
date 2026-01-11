from __future__ import annotations

from dataclasses import dataclass

class PermissionError(Exception):
    pass

@dataclass(frozen=True)
class Actor:
    username: str
    role: str  # admin/curator/front_desk

def require_role(actor: Actor, allowed: set[str]) -> None:
    if actor.role not in allowed:
        raise PermissionError(f"Action requires one of roles: {sorted(allowed)} (you are '{actor.role}')")
