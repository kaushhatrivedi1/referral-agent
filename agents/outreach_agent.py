"""
Agent 4: Outreach-Drafting Agent

Job: draft a specific, non-generic outreach message per matched
connection, using their relationship-strength reasoning to set tone.

Zero-subscription, provider-agnostic design: nothing is required to run
this. If an LLM key is present it's used for a genuinely tailored draft;
otherwise a rule-based template is used, so the whole pipeline always
runs end-to-end and produces real output.

Supported providers (checked in this order, first key found wins):
  - ANTHROPIC_API_KEY  -> Claude (api.anthropic.com)
  - LLM_API_KEY        -> literally any other LLM, as long as it exposes an
                          OpenAI-compatible chat-completions endpoint -- which
                          covers almost all of them: OpenAI, Groq, Together,
                          Fireworks, DeepSeek, Mistral, a local Ollama/LM Studio
                          server, etc. Point LLM_BASE_URL at that provider's
                          endpoint and LLM_MODEL at its model name.
  - neither set        -> rule-based template, no network call at all.
"""
import os
from typing import List

from common import ScoredConnection, OutreachDraft

ANTHROPIC_MODEL = "claude-sonnet-5"
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")


def _template_draft(sc: ScoredConnection, target_company: str, target_role: str) -> str:
    name = sc.connection.first_name
    is_warm = sc.strength_score >= 0.7

    if is_warm:
        return (
            f"Hi {name}, hope you've been well! I saw {target_company} has an opening "
            f"for {target_role} and immediately thought of you since you're on the inside. "
            f"Would you be open to a quick chat about the team, and possibly pointing me "
            f"toward a referral if it seems like a fit? No worries at all if not!"
        )
    else:
        return (
            f"Hi {name}, it's been a while since we connected ({sc.reasoning.split('--')[0].strip()}) "
            f"-- hope things are going well at {sc.connection.company}. I'm exploring a "
            f"{target_role} role there and would love to reconnect and hear about your "
            f"experience on the team, if you have a few minutes."
        )


def _build_prompt(sc: ScoredConnection, target_company: str, target_role: str) -> str:
    return (
        f"Draft a short (3-4 sentence), specific, non-generic LinkedIn outreach message "
        f"asking {sc.connection.first_name} for help with a referral.\n"
        f"Context: {sc.reasoning}\n"
        f"They work at {target_company} as a {sc.connection.position}.\n"
        f"I'm interested in a {target_role} role there.\n"
        f"Match the tone to the relationship warmth described above -- warm and direct "
        f"for a strong tie, a re-introduction framing for a dormant one. "
        f"Return only the message text, nothing else."
    )


def _anthropic_draft(sc: ScoredConnection, target_company: str, target_role: str) -> str:
    import json
    import urllib.request

    api_key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": _build_prompt(sc, target_company, target_role)}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"].strip()


def _generic_llm_draft(sc: ScoredConnection, target_company: str, target_role: str) -> str:
    """Works with any LLM provider exposing an OpenAI-compatible chat-completions
    endpoint -- OpenAI itself, Groq, Together, Fireworks, DeepSeek, Mistral, a
    local Ollama/LM Studio server, etc. Point LLM_BASE_URL at that provider's
    endpoint and LLM_MODEL at its model name."""
    import json
    import urllib.request

    api_key = os.environ["LLM_API_KEY"]
    body = json.dumps({
        "model": LLM_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": _build_prompt(sc, target_company, target_role)}],
    }).encode()

    req = urllib.request.Request(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def _pick_llm_draft_fn():
    """First configured provider wins. Returns None if no key is set anywhere."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic_draft
    if os.environ.get("LLM_API_KEY"):
        return _generic_llm_draft
    return None


def draft_outreach(
    matches: List[ScoredConnection], target_company: str, target_role: str
) -> List[OutreachDraft]:
    drafts = []
    llm_draft_fn = _pick_llm_draft_fn()

    for sc in matches:
        if llm_draft_fn:
            try:
                message = llm_draft_fn(sc, target_company, target_role)
            except Exception as e:
                message = _template_draft(sc, target_company, target_role)
                message += f"\n[Note: LLM call failed ({e}), used template fallback]"
        else:
            message = _template_draft(sc, target_company, target_role)
        drafts.append(OutreachDraft(scored_connection=sc, message=message))

    return drafts


if __name__ == "__main__":
    from parser_agent import parse_connections
    from strength_agent import score_all
    from company_match_agent import match_company

    conns = parse_connections("../data/mock_connections.csv")
    scored = score_all(conns)
    matches = match_company(scored, "Google")
    drafts = draft_outreach(matches, "Google", "Software Engineer")

    for d in drafts:
        print(f"\n=== {d.scored_connection.connection.full_name} (score={d.scored_connection.strength_score}) ===")
        print(d.message)
