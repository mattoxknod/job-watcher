"""The title rule.

A posting is "in role" when its title names one of the analyst tracks below and
does not name a job above the analyst/associate level. The rule reads the title
only, so it gives the same answer for every day of the history.

The tracks follow the roles this watch list is aimed at: financial analysis and
FP&A, data and business intelligence, credit and risk, investment banking and
capital markets, the supply-chain and merchandising analyst roles that sit
alongside them, and the one-to-three year rotational and development programs
that hire into all of the above.
"""

from __future__ import annotations

import re

#: Titles that put a posting in role, grouped only to keep the list readable.
INCLUDE_PATTERNS = [
    # Financial analysis, FP&A, corporate finance
    r"\bfinanc(?:e|ial)\s+analy",
    r"\bfp\s*&\s*a\b",
    r"\bfinancial\s+planning\b",
    r"\bcorporate\s+finance\b",
    r"\btreasury\b",
    r"\bvaluation\b",
    r"\baccounting\s+analy",
    # Data, analytics, business intelligence
    r"\bdata\s+analy",
    r"\bbusiness\s+intelligence\b",
    r"\banalytics\s+analy",
    r"\breporting\s+analy",
    r"\bbusiness\s+analy",
    r"\bquantitative\s+analy",
    # Credit and risk
    r"\bcredit\s+analy",
    r"\bcredit\s+risk\b",
    r"\brisk\s+analy",
    r"\bunderwrit",
    r"\bportfolio\s+analy",
    r"\bfraud\s+analy",
    # Investment banking and markets
    r"\binvestment\s+bank",
    r"\bcapital\s+markets\b",
    r"\bequity\s+research\b",
    r"\binvestment\s+analy",
    r"\bresearch\s+analy",
    # Supply chain, merchandising, pricing - the analyst roles next door
    r"\bsupply\s+chain\s+analy",
    r"\breplenishment\b",
    r"\bmerchandis\w*\s+analy",
    r"\bpricing\s+analy",
    r"\bprocurement\s+analy",
    r"\bsourcing\s+analy",
    r"\boperations\s+analy",
    # Early-career and rotational programs
    r"\banalyst\s+program\b",
    r"\brotational?\b",
    r"\bdevelopment\s+program\b",
    r"\bleadership\s+program\b",
    r"\bsummer\s+analyst\b",
    r"\bnew\s+grad(?:uate)?\b",
    r"\bcampus\b",
    r"\binterns?\b",
    r"\bintern\s*-",
]

#: Titles above the analyst/associate level this watch list is aimed at. A
#: program posting keeps its place even when it also carries one of these words.
EXCLUDE_PATTERNS = [
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bvice\s+president\b",
    r"\bvp\b",
    r"\bhead\s+of\b",
    r"\bchief\b",
    r"\bprincipal\b",
    r"\bpartner\b",
    r"\blead\b",
    r"\bsupervisor\b",
    r"\bexecutive\b",
]

#: Program wording that survives the seniority exclusion above.
PROGRAM_PATTERNS = [
    r"\banalyst\s+program\b",
    r"\bdevelopment\s+program\b",
    r"\bleadership\s+program\b",
    r"\brotational?\b",
    r"\bsummer\s+analyst\b",
    r"\binterns?\b",
]

_INCLUDE = re.compile("|".join(INCLUDE_PATTERNS), re.I)
_EXCLUDE = re.compile("|".join(EXCLUDE_PATTERNS), re.I)
_PROGRAM = re.compile("|".join(PROGRAM_PATTERNS), re.I)


def in_role(title: str) -> bool:
    """Return True when ``title`` is one of the roles being watched."""
    if not title:
        return False
    text = title.strip()
    if not _INCLUDE.search(text):
        return False
    if _EXCLUDE.search(text) and not _PROGRAM.search(text):
        return False
    return True
