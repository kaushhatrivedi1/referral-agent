"""
Agent 1: Network Parser Agent

Job: turn the messy raw LinkedIn connections CSV export into clean,
structured Connection objects. Real exports have inconsistent title
casing, extra whitespace, and sometimes missing company/position fields
-- this agent's whole job is to make the rest of the pipeline not have
to think about any of that.
"""
import csv
from datetime import datetime
from typing import List

from common import Connection


def _parse_date(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    # LinkedIn exports dates like "15 Jan 2020"
    for fmt in ("%d %b %Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_connections(csv_path: str) -> List[Connection]:
    """Reads a LinkedIn 'Connections.csv' export and returns clean Connection objects.

    LinkedIn's real export has a few marketing/header lines before the
    actual column headers -- this skips to the real header row ('First Name').
    """
    connections: List[Connection] = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Find the real header row (LinkedIn prepends notes lines in real exports)
    header_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("First Name"):
            header_idx = i
            break

    reader = csv.DictReader(lines[header_idx:])
    for row in reader:
        first = (row.get("First Name") or "").strip()
        last = (row.get("Last Name") or "").strip()
        company = (row.get("Company") or "Unknown").strip()
        position = (row.get("Position") or "Unknown").strip()
        connected_on = _parse_date(row.get("Connected On", ""))

        if not first and not last:
            continue  # skip malformed rows

        connections.append(
            Connection(
                first_name=first,
                last_name=last,
                company=company,
                position=position,
                connected_on=connected_on,
            )
        )

    return connections


if __name__ == "__main__":
    conns = parse_connections("../data/mock_connections.csv")
    for c in conns:
        print(f"{c.full_name:20s} | {c.company:12s} | {c.position:28s} | {c.connected_on}")
