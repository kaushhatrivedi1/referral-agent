"""
Job Posting Parser (optional helper agent)

Job: take a raw job posting title as a human would paste it -- e.g. copied
from LinkedIn Jobs, Indeed, or a company careers page -- and split it into
(company, role). This does NOT search for jobs, recommend jobs, or know
anything about the job market. It only saves the user from manually typing
--company and --role separately when they already have a specific posting
in mind.

Supported formats (most common real-world patterns):
    "Software Engineer at Google"
    "Software Engineer - Google"
    "Software Engineer | Google"
    "Google - Software Engineer"
    "Google is hiring a Software Engineer"

If the format can't be confidently split, it returns (None, None) and the
caller should fall back to asking the user for --company/--role explicitly.
"""
import re
from typing import Optional, Tuple

PATTERNS = [
    # "Software Engineer at Google"
    re.compile(r"^(?P<role>.+?)\s+at\s+(?P<company>.+)$", re.IGNORECASE),
    # "Software Engineer - Google"  /  "Software Engineer | Google"
    re.compile(r"^(?P<role>.+?)\s*[-|]\s*(?P<company>.+)$"),
    # "Google is hiring a Software Engineer" / "Google is hiring a(n) Software Engineer"
    re.compile(r"^(?P<company>.+?)\s+is\s+hiring\s+(?:an?\s+)?(?P<role>.+)$", re.IGNORECASE),
]


def _clean(text: str) -> str:
    return text.strip().strip(",.;:").strip()


def parse_job_posting(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns (company, role), or (None, None) if it can't be confidently parsed."""
    text = raw_text.strip()
    if not text:
        return None, None

    for pattern in PATTERNS:
        match = pattern.match(text)
        if match:
            groups = match.groupdict()
            company = _clean(groups["company"])
            role = _clean(groups["role"])
            if company and role:
                return company, role

    return None, None


if __name__ == "__main__":
    tests = [
        "Software Engineer at Google",
        "Software Engineer - Google",
        "Software Engineer | Google",
        "Google is hiring a Software Engineer",
        "Senior Backend Engineer at Meta",
        "just some random text",
    ]
    for t in tests:
        company, role = parse_job_posting(t)
        print(f"{t!r:45s} -> company={company!r}, role={role!r}")
