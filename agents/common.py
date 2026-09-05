"""Shared data structures used by every agent in the pipeline."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Connection:
    first_name: str
    last_name: str
    company: str
    position: str
    connected_on: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class ScoredConnection:
    connection: Connection
    strength_score: float          # 0.0 - 1.0
    reasoning: str


@dataclass
class OutreachDraft:
    scored_connection: ScoredConnection
    message: str
