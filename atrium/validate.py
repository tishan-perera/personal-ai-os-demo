"""Structural checks for requests, proposals, and owner decisions.

Labels such as the actor field are not credentials. Validation does not
prove that a person approved anything.
"""


class ValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


MAX_REQUEST = 2000
MAX_NOTE = 500
MAX_ACTOR = 80
MAX_SUMMARY = 240
MAX_DETAIL = 2000

ALLOWED_RISKS = frozenset({"medium", "high"})
ALLOWED_DECISIONS = frozenset({"approve", "reject"})


def validate_request(text: object) -> str:
    if not isinstance(text, str):
        raise ValidationError("bad_request", "The request must be text.")
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("empty_request", "Write a request before asking the team.")
    if len(cleaned) > MAX_REQUEST:
        raise ValidationError(
            "request_too_long",
            f"Keep a request under {MAX_REQUEST} characters.",
        )
    if "\x00" in cleaned:
        raise ValidationError("bad_request", "The request contains a null character.")
    return cleaned


def validate_decision(decision: object) -> str:
    if decision not in ALLOWED_DECISIONS:
        raise ValidationError("bad_decision", "Decision must be approve or reject.")
    return str(decision)


def validate_actor(actor: object) -> str:
    if not isinstance(actor, str) or not actor.strip():
        raise ValidationError(
            "actor_required",
            "An owner label is required to approve or reject.",
        )
    cleaned = actor.strip()
    if len(cleaned) > MAX_ACTOR:
        raise ValidationError("actor_too_long", "The owner label is too long.")
    return cleaned


def validate_note(note: object) -> str:
    if note is None:
        return ""
    if not isinstance(note, str):
        raise ValidationError("bad_note", "The note must be text.")
    if len(note) > MAX_NOTE:
        raise ValidationError("note_too_long", f"Keep a note under {MAX_NOTE} characters.")
    return note.strip()


def validate_draft_text(summary: str, detail: str, target: str, risk: str) -> None:
    if not summary.strip() or len(summary) > MAX_SUMMARY:
        raise ValidationError("bad_summary", "A proposal needs a short summary.")
    if not detail.strip() or len(detail) > MAX_DETAIL:
        raise ValidationError("bad_detail", "A proposal needs a detail block.")
    if not target.strip():
        raise ValidationError("bad_target", "A proposal needs a fixture target.")
    if risk not in ALLOWED_RISKS:
        raise ValidationError(
            "bad_risk",
            "Consequential proposals are medium or high risk. Low risk cannot skip the queue.",
        )
