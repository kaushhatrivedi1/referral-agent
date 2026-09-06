"""
Agent 3: Company-Match Agent

Job: given a target company name, filter the scored connection list down
to people who currently work there. Kept intentionally simple for the
baseline -- normalized string matching on the Company field. No external
org-chart data or scraping involved.
"""
from datetime import datetime
from typing import List

from common import ScoredConnection


def _normalize(name: str) -> str:
    return name.strip().lower()


def match_company(scored_connections: List[ScoredConnection], target_company: str) -> List[ScoredConnection]:
    target = _normalize(target_company)
    matches = [
        sc for sc in scored_connections
        if _normalize(sc.connection.company) == target
    ]
    # Best referral candidates first: highest relationship strength on top, ties
    # broken by actual connection date so ordering never depends on CSV row order.
    # toordinal() rather than timestamp() -- the latter raises on datetime.min.
    return sorted(
        matches,
        key=lambda sc: (
            -sc.strength_score,
            -(sc.connection.connected_on or datetime.min).toordinal(),
        ),
    )


if __name__ == "__main__":
    from parser_agent import parse_connections
    from strength_agent import score_all

    conns = parse_connections("../data/mock_connections.csv")
    scored = score_all(conns)
    matches = match_company(scored, "Google")
    for m in matches:
        print(f"{m.connection.full_name:20s} | {m.connection.position:28s} | score={m.strength_score:.2f}")
