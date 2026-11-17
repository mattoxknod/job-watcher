"""The mechanical engineering title rule, and the entry-level rule.

These feed the "For Colton" page, which watches mechanical engineering work in
Arkansas, weighted towards internships and entry-level roles. Like the title
rule in :mod:`jobwatcher.role` they read the title only, so they give the same
answer for every day of the history.

The hard part is that "engineer" on its own means very little: these boards are
full of software, data and security engineers. So a posting has to name a
mechanical or manufacturing discipline **and** avoid the software wording that
would otherwise sweep half a tech board into the page.
"""

from __future__ import annotations

import re

#: Disciplines that count as mechanical engineering work.
MECHANICAL_PATTERNS = [
    r"\bmechanical\b",
    r"\bmechatronic",
    r"\bmanufacturing\s+engineer",
    r"\bindustrial\s+engineer",
    r"\bprocess\s+engineer",
    r"\bdesign\s+engineer",
    r"\bproduct\s+engineer",
    r"\bproject\s+engineer",
    r"\bplant\s+engineer",
    r"\bfacilities\s+engineer",
    r"\bmaintenance\s+engineer",
    r"\breliability\s+engineer",
    r"\bcontrols\s+engineer",
    r"\bautomation\s+engineer",
    r"\brobotics\s+engineer",
    r"\bquality\s+engineer",
    r"\bpackaging\s+engineer",
    r"\btooling\s+engineer",
    r"\bwelding\s+engineer",
    r"\bthermal\s+engineer",
    r"\bstructural\s+engineer",
    r"\bmaterials\s+engineer",
    r"\bmetallurg",
    r"\bhvac\b",
    r"\bcad\b",
    r"\bsolidworks\b",
    r"\bautocad\b",
    r"\bdrafter\b",
    r"\bdrafting\b",
    r"\bmachine\s+design\b",
    r"\btool\s+and\s+die\b",
    r"\bengineering\s+(?:intern|co-?op)",
    r"\b(?:intern|co-?op)[^a-z]*engineering\b",
    r"\bengineering\s+(?:development|leadership|rotational)\s+program\b",
    # A bare "Engineer I/II" on a manufacturer's board is nearly always a
    # plant engineering role, and the software exclusions below still apply.
    r"\bengineer\s+(?:i{1,3}|iv|v|[1-5])\b",
    r"\bmanufacturing\s+technolog",
    r"\bcontinuous\s+improvement\s+engineer",
]

#: Wording that means the posting is a software, data or IT job. "Site
#: Reliability Engineer" and "Quality Engineer" on a tech board both look
#: mechanical to the patterns above until these rule them out.
SOFTWARE_PATTERNS = [
    r"\bsoftware\b",
    r"\bdata\s+engineer",
    r"\bdata\s+scien",
    r"\bmachine\s+learning\b",
    r"\bfull[\s-]?stack\b",
    r"\bfront[\s-]?end\b",
    r"\bback[\s-]?end\b",
    r"\bweb\b",
    r"\bcloud\b",
    r"\bdevops\b",
    r"\bsite\s+reliability\b",
    r"\bnetwork\s+engineer",
    r"\bsecurity\s+engineer",
    r"\bcyber",
    r"\bsystems?\s+engineer",
    r"\bsystems?\s+administrator\b",
    r"\bsales\s+engineer",
    r"\bsolutions?\s+engineer",
    r"\bsupport\s+engineer",
    r"\bplatform\s+engineer",
    r"\bqa\s+engineer",
    r"\btest\s+automation\b",
    r"\bsap\b",
    r"\bsalesforce\b",
    r"\bjava\b",
    r"\bpython\b",
    r"\b\.net\b",
    r"\bfirmware\b",
    r"\bapplication\s+engineer",
    r"\bit\s+engineer",
    r"\binformation\s+technology\b",
    r"\banalytics\s+engineer",
    r"\bendpoint\b",
    r"\bhelp\s?desk\b",
]

#: Teaching and research posts. "Assistant Professor in Mechanical Engineering"
#: is mechanical engineering, but it is not the kind of job this page is for.
ACADEMIC_PATTERNS = [
    r"\bprofessor\b",
    r"\bfaculty\b",
    r"\blecturer\b",
    r"\binstructor\b",
    r"\badjunct\b",
    r"\bpost[\s-]?doc",
    r"\bteaching\b",
    r"\bresearch\s+assistant\b",
    r"\bgraduate\s+assistant\b",
]

#: Skilled trades. These sit beside engineering in a plant and share its
#: vocabulary, but they are not engineering roles.
TRADE_PATTERNS = [
    r"\btechnician\b",
    r"\bmechanic\b",
    r"\btradesman\b",
    r"\bskilled\s+trade",
    r"\bmillwright\b",
    r"\belectrician\b",
    r"\bwelder\b",
    r"\bmachinist\b",
    r"\boperator\b",
    r"\bassembler\b",
    r"\binstaller\b",
    r"\bfitter\b",
]

#: Wording that marks a posting as entry level or a student placement.
ENTRY_PATTERNS = [
    r"\binterns?\b",
    r"\binternship\b",
    r"\bco-?op\b",
    r"\bentry[\s-]?level\b",
    r"\bnew\s+grad(?:uate)?\b",
    r"\buniversity\s+(?:grad|hire|recruit|program)",
    r"\bcampus\b",
    r"\bjunior\b",
    r"\bjr\.?\b",
    r"\bassociate\b",
    r"\btrainee\b",
    r"\bapprentice",
    r"\bearly\s+career\b",
    r"\bgraduate\s+(?:engineer|program|scheme)\b",
    r"\b(?:development|leadership|rotational)\s+program\b",
    r"\brotational\b",
    # "Engineer I" and "Engineer 1" are the first rung; II and up are not.
    r"\bengineer\s+(?:i|1)\b",
    r"\blevel\s+(?:i|1)\b",
    r"\bi{1}\b(?=\s*$)",
]

#: Levels above the first rung. These beat the entry wording above, so
#: "Senior Associate Engineer" does not read as entry level.
SENIOR_PATTERNS = [
    r"\bsenior\b",
    r"\bsr\.?\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\bstaff\b",
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bsupervisor\b",
    r"\bhead\s+of\b",
    r"\bchief\b",
    r"\bvice\s+president\b",
    r"\bvp\b",
    r"\bexpert\b",
    r"\badvanced\b",
    r"\bmaster\b",
    r"\bengineer\s+(?:ii|iii|iv|v|[2-5])\b",
    r"\blevel\s+(?:ii|iii|iv|v|[2-5])\b",
]

_MECHANICAL = re.compile("|".join(MECHANICAL_PATTERNS), re.I)
_NOT_MECHANICAL = re.compile(
    "|".join(SOFTWARE_PATTERNS + ACADEMIC_PATTERNS + TRADE_PATTERNS), re.I
)
_ENTRY = re.compile("|".join(ENTRY_PATTERNS), re.I)
_SENIOR = re.compile("|".join(SENIOR_PATTERNS), re.I)


def is_mechanical(title: str) -> bool:
    """Return True when a title is mechanical or manufacturing engineering."""
    if not title:
        return False
    text = title.strip()
    if _NOT_MECHANICAL.search(text):
        return False
    return bool(_MECHANICAL.search(text))


def is_entry_level(title: str) -> bool:
    """Return True when a title reads as entry level, an internship or a co-op."""
    if not title:
        return False
    text = title.strip()
    if _SENIOR.search(text):
        return False
    return bool(_ENTRY.search(text))
