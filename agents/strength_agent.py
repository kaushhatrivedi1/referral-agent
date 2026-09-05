"""
Agent 2: Relationship-Strength Agent

Job: score how "warm" each connection actually is. This baseline uses
signals that are honestly available from a LinkedIn export -- mainly
connection recency -- and is explicit that richer signals (message
history, mutual engagement) are a Phase 2 improvement, not baseline
overclaiming.
"""
from datetime import datetime
from typing import List

from common import Connection, ScoredConnection

NOW = datetime.now()


def _recency_score(connected_on: datetime | None) -> float:
    """More recent connections score higher. Unknown dates get a neutral 0.4."""
    if connected_on is None:
        return 0.4
    days_ago = (NOW - connected_on).days
    years_ago = days_ago / 365.0

    if years_ago <= 1:
        return 1.0
    if years_ago <= 3:
        return 0.7
    if years_ago <= 6:
        return 0.4
    return 0.2


def score_connection(conn: Connection) -> ScoredConnection:
    recency = _recency_score(conn.connected_on)

    if conn.connected_on is None:
        reasoning = "Connection date unknown -- treated as moderate/unknown tie."
    else:
        years_ago = round((NOW - conn.connected_on).days / 365.0, 1)
        if years_ago <= 1:
            reasoning = f"Connected {years_ago} years ago -- likely still an active, recent tie."
        elif years_ago <= 3:
            reasoning = f"Connected {years_ago} years ago -- moderately warm, worth reconnecting."
        else:
            reasoning = f"Connected {years_ago} years ago -- dormant tie, needs a re-introduction framing."

    return ScoredConnection(connection=conn, strength_score=round(recency, 2), reasoning=reasoning)


def score_all(connections: List[Connection]) -> List[ScoredConnection]:
    return [score_connection(c) for c in connections]


if __name__ == "__main__":
    from parser_agent import parse_connections

    conns = parse_connections("../data/mock_connections.csv")
    scored = score_all(conns)
    for s in sorted(scored, key=lambda x: -x.strength_score):
        print(f"{s.connection.full_name:20s} | score={s.strength_score:.2f} | {s.reasoning}")
