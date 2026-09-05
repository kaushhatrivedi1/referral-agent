"""
run_baseline.py

Runs the full 4-agent referral pipeline end to end:
  Parser Agent -> Strength Agent -> Company-Match Agent -> Outreach Agent

Usage:
    python run_baseline.py --input data/mock_connections.csv \
        --company Google --role "Software Engineer"

Zero subscriptions required: works out of the box using a template-based
outreach drafter. Set ANTHROPIC_API_KEY as an environment variable to
upgrade Agent 4 to real LLM-drafted messages.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agents"))


def _load_dotenv(path: str = ".env") -> None:
    """Minimal stdlib-only .env loader (no python-dotenv dependency)."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and value:
            os.environ.setdefault(key, value)


_load_dotenv()

from parser_agent import parse_connections
from strength_agent import score_all
from company_match_agent import match_company
from outreach_agent import draft_outreach
from job_posting_parser import parse_job_posting


def main():
    parser = argparse.ArgumentParser(description="Who-should-refer-you multi-agent pipeline")
    parser.add_argument("--input", default="data/mock_connections.csv", help="Path to LinkedIn connections CSV export")
    parser.add_argument("--company", help="Target company name, e.g. Google")
    parser.add_argument("--role", help="Target role, e.g. 'Software Engineer'")
    parser.add_argument(
        "--posting",
        help='Alternative to --company/--role: paste a job title as-is, e.g. "Software Engineer at Google"',
    )
    parser.add_argument("--top-n", type=int, default=3, help="How many candidates to draft messages for")
    args = parser.parse_args()

    company, role = args.company, args.role

    if args.posting:
        parsed_company, parsed_role = parse_job_posting(args.posting)
        if not parsed_company:
            parser.error(
                f"Could not parse --posting {args.posting!r}. "
                f"Try a format like 'Software Engineer at Google', or use --company/--role directly."
            )
        company, role = parsed_company, parsed_role
        print(f"[Job Posting Parser]     Parsed '{args.posting}' -> company={company!r}, role={role!r}\n")

    if not company or not role:
        parser.error("Provide either --posting, or both --company and --role.")

    args.company, args.role = company, role

    print(f"[Agent 1: Parser]        Reading {args.input} ...")
    connections = parse_connections(args.input)
    print(f"                         Parsed {len(connections)} connections.\n")

    print("[Agent 2: Strength]      Scoring relationship strength for each connection ...")
    scored = score_all(connections)
    print(f"                         Scored {len(scored)} connections.\n")

    print(f"[Agent 3: Company-Match] Filtering to connections at '{args.company}' ...")
    matches = match_company(scored, args.company)
    print(f"                         Found {len(matches)} match(es) at {args.company}.\n")

    if not matches:
        print(f"No connections found at {args.company}. Nothing to draft. Exiting.")
        return

    top_matches = matches[: args.top_n]
    print(f"[Agent 4: Outreach]      Drafting outreach for top {len(top_matches)} candidate(s) ...\n")
    drafts = draft_outreach(top_matches, args.company, args.role)

    print("=" * 70)
    print(f"RESULTS: Best referral candidates at {args.company} for '{args.role}'")
    print("=" * 70)
    for i, d in enumerate(drafts, 1):
        sc = d.scored_connection
        print(f"\n#{i}  {sc.connection.full_name}  ({sc.connection.position})")
        print(f"    Relationship strength: {sc.strength_score}  |  {sc.reasoning}")
        print(f"    Drafted message:")
        print(f"    \"{d.message}\"")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
