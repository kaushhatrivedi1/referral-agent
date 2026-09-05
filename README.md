# Who Should Actually Refer You — A Multi-Agent Referral Pipeline

A 4-agent pipeline that reads your real LinkedIn connections export, scores
how "warm" each relationship actually is, filters to a target company, and
drafts a specific (non-generic) outreach message for your best referral
candidates.

## Why this is agentic, not just a script

Each stage requires a genuinely different kind of reasoning, and each agent
only sees the output of the previous one — not the raw input:

1. **Parser Agent** — cleans messy real-world CSV data into structured records.
2. **Strength Agent** — judges relationship warmth from available signals.
3. **Company-Match Agent** — filters to relevant candidates at a target company.
4. **Outreach Agent** — drafts a tailored message, conditioning tone on the
   strength agent's reasoning (a warm tie gets a direct ask; a dormant tie
   gets a re-introduction framing).

## Dependencies

- Python 3.10+
- No third-party packages required for the baseline (standard library only).
- Optional: an `ANTHROPIC_API_KEY` environment variable to upgrade Agent 4
  from template-based drafts to real LLM-generated ones. **Not required —
  the pipeline runs completely free and produces real output without it.**

## Setup

```bash
git clone <your-repo-url>
cd referral-agent
# no pip install needed for the baseline
```

To enable LLM-drafted messages (optional):
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Getting your own input data

1. Go to LinkedIn → Settings & Privacy → Data Privacy → "Get a copy of your data"
2. Select "Connections" and request the archive (LinkedIn emails it within
   a few hours to a day).
3. Unzip it and locate `Connections.csv`.
4. Place it in `data/` (or point `--input` at wherever you saved it).

For testing without waiting on a real export, `data/mock_connections.csv`
is a small synthetic sample in the exact same format LinkedIn exports.

## Running the baseline

```bash
python3 run_baseline.py --input data/mock_connections.csv \
    --company Google --role "Software Engineer" --top-n 3
```

To run against your real export once it arrives:
```bash
python3 run_baseline.py --input data/Connections.csv \
    --company "<Target Company>" --role "<Target Role>" --top-n 3
```

## Actual baseline output (captured from a real run)

```
$ python3 run_baseline.py --input data/mock_connections.csv --company Google --role "Software Engineer" --top-n 3
[Agent 1: Parser]        Reading data/mock_connections.csv ...
                         Parsed 10 connections.

[Agent 2: Strength]      Scoring relationship strength for each connection ...
                         Scored 10 connections.

[Agent 3: Company-Match] Filtering to connections at 'Google' ...
                         Found 5 match(es) at Google.

[Agent 4: Outreach]      Drafting outreach for top 3 candidate(s) ...

======================================================================
RESULTS: Best referral candidates at Google for 'Software Engineer'
======================================================================

#1  Jennifer Lopez  (UX Designer)
    Relationship strength: 0.4  |  Connected 5.0 years ago -- dormant tie, needs a re-introduction framing.
    Drafted message:
    "Hi Jennifer, it's been a while since we connected (Connected 5.0 years ago) -- hope things are going well at Google. I'm exploring a Software Engineer role there and would love to reconnect and hear about your experience on the team, if you have a few minutes."

#2  James Brown  (Recruiter)
    Relationship strength: 0.4  |  Connected 4.0 years ago -- dormant tie, needs a re-introduction framing.
    Drafted message:
    "Hi James, it's been a while since we connected (Connected 4.0 years ago) -- hope things are going well at Google. I'm exploring a Software Engineer role there and would love to reconnect and hear about your experience on the team, if you have a few minutes."

#3  Sarah Chen  (Senior Software Engineer)
    Relationship strength: 0.2  |  Connected 6.6 years ago -- dormant tie, needs a re-introduction framing.
    Drafted message:
    "Hi Sarah, it's been a while since we connected (Connected 6.6 years ago) -- hope things are going well at Google. I'm exploring a Software Engineer role there and would love to reconnect and hear about your experience on the team, if you have a few minutes."

======================================================================
```

Note: relationship-strength scores are relative to whenever the command is
run (recency is computed against the current date), so re-running this
later against the same CSV will show different "years ago" numbers and
possibly a different top-3 ordering.

## Where output appears

Results print directly to the terminal: the ranked list of candidates,
their relationship-strength score and reasoning, and a drafted outreach
message for each. Nothing is written to disk by default.

## Known limitations (baseline, Phase 0)

- Relationship strength currently uses only connection recency, since that's
  the signal reliably present in a standard LinkedIn export. Message
  history, mutual-connection overlap, and post-engagement signals are
  planned for Phase 2.
- Company matching is exact-string based (normalized case/whitespace only).
  It will miss connections whose `Company` field is stale or informally
  written (e.g. "Google" vs. "Google LLC").
- No target-company org-chart modeling — the pipeline only ranks *your own*
  existing connections, it does not identify people at the company you
  aren't already connected to.

## File structure

```
referral-agent/
├── README.md
├── run_baseline.py          # orchestrator — runs all 4 agents in sequence
├── data/
│   └── mock_connections.csv # synthetic sample export for testing
└── agents/
    ├── common.py             # shared data models
    ├── parser_agent.py        # Agent 1
    ├── strength_agent.py      # Agent 2
    ├── company_match_agent.py # Agent 3
    └── outreach_agent.py      # Agent 4
```
