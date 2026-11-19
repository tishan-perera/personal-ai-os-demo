"""Chief-of-staff router. Keyword scores only. Ties stay with the chief."""

import re
from dataclasses import dataclass

from atrium.roster import DEPARTMENTS

_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Route:
    seat_id: str
    score: int
    reason: str
    matched: tuple[str, ...]


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def keyword_hits(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    lowered = text.lower()
    words = tokens(text)
    hits: list[str] = []
    for keyword in keywords:
        if " " in keyword or "-" in keyword:
            if keyword in lowered:
                hits.append(keyword)
        elif keyword in words:
            hits.append(keyword)
    return tuple(hits)


def _tie_phrase(labels: list[str]) -> str:
    ordered = sorted(labels)
    if len(ordered) == 2:
        joined = f"{ordered[0]} and {ordered[1]}"
    else:
        joined = ", ".join(ordered[:-1]) + f", and {ordered[-1]}"
    return f"{joined} tied, so Mara Quinn kept the request."


def route_request(text: str) -> Route:
    rows: list[tuple[int, str, str, tuple[str, ...]]] = []
    for seat in DEPARTMENTS:
        matched = keyword_hits(text, seat.keywords)
        rows.append((len(matched), seat.department, seat.id, matched))
    rows.sort(key=lambda row: row[0], reverse=True)
    best_score = rows[0][0]
    leaders = [row for row in rows if row[0] == best_score and best_score > 0]
    if best_score == 0:
        return Route(
            "chief",
            0,
            "No department keyword matched, so Mara Quinn kept the request.",
            (),
        )
    if len(leaders) > 1:
        return Route(
            "chief",
            best_score,
            _tie_phrase([row[1] for row in leaders]),
            (),
        )
    score, department, seat_id, matched = leaders[0]
    return Route(
        seat_id,
        score,
        f"Matched {department} on {', '.join(matched)}.",
        matched,
    )
