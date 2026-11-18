"""Approval queue. Pending proposals do not run. A decision is single-use."""

import hashlib
from copy import deepcopy
from typing import Any

from atrium.agents import ProposalDraft
from atrium.roster import Seat
from atrium.validate import (
    ValidationError,
    validate_actor,
    validate_decision,
    validate_draft_text,
    validate_note,
)


def fingerprint(action: str, target: str) -> str:
    raw = f"{action}|{target.strip().lower()}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


class Queue:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._seq = 0

    @property
    def seq(self) -> int:
        return self._seq

    def add(
        self,
        *,
        seat: Seat,
        draft: ProposalDraft,
        request: str,
        created_at: str,
    ) -> dict[str, Any]:
        if draft.action not in seat.actions:
            raise ValidationError(
                "action_not_allowed",
                f"{seat.department} cannot propose {draft.action}.",
            )
        if not isinstance(draft.payload, dict):
            raise ValidationError("bad_payload", "A proposal payload must be an object.")
        validate_draft_text(draft.summary, draft.detail, draft.target, draft.risk)
        digest = fingerprint(draft.action, draft.target)
        for existing in self._items.values():
            if existing["fingerprint"] == digest and existing["status"] in {"pending", "executed"}:
                raise ValidationError(
                    "duplicate",
                    (
                        f"A {existing['status']} proposal already covers this action "
                        f"({existing['id']})."
                    ),
                )
        self._seq += 1
        item = {
            "id": f"APR-{self._seq:03d}",
            "fingerprint": digest,
            "department": seat.department,
            "seat_id": seat.id,
            "seat_name": seat.name,
            "action": draft.action,
            "target": draft.target,
            "summary": draft.summary,
            "detail": draft.detail,
            "risk": draft.risk,
            "status": "pending",
            "created_at": created_at,
            "decided_at": None,
            "decided_by": None,
            "decision_note": "",
            "execution": None,
            "payload": deepcopy(draft.payload),
            "request_excerpt": request[:240],
        }
        self._items[item["id"]] = item
        return deepcopy(item)

    def decide(
        self,
        proposal_id: str,
        decision: object,
        actor: object,
        note: object,
        decided_at: str,
    ) -> dict[str, Any]:
        item = self._items.get(proposal_id)
        if item is None:
            raise ValidationError("missing_proposal", "No proposal with that id is in the queue.")
        if item["status"] != "pending":
            raise ValidationError(
                "not_pending",
                f"{proposal_id} is already {item['status']}. It cannot be decided again.",
            )
        chosen = validate_decision(decision)
        owner = validate_actor(actor)
        comment = validate_note(note)
        item["decided_at"] = decided_at
        item["decided_by"] = owner
        item["decision_note"] = comment
        item["status"] = "rejected" if chosen == "reject" else "approved"
        if chosen == "reject":
            item["execution"] = None
        return deepcopy(item)

    def mark_executed(self, proposal_id: str, execution: dict[str, Any]) -> dict[str, Any]:
        item = self._items.get(proposal_id)
        if item is None:
            raise ValidationError("missing_proposal", "No proposal with that id is in the queue.")
        if item["status"] != "approved":
            raise ValidationError(
                "not_approved",
                "Execution requires an owner approval in this same decision.",
            )
        item["status"] = "executed"
        item["execution"] = deepcopy(execution)
        return deepcopy(item)

    def items(self) -> list[dict[str, Any]]:
        order = {"pending": 0, "approved": 1, "executed": 2, "rejected": 3}
        values = list(self._items.values())
        values.sort(key=lambda item: (order.get(str(item["status"]), 9), str(item["id"])))
        return deepcopy(values)

    def load(self, seq: int, items: list[dict[str, Any]]) -> None:
        self._seq = seq
        self._items = {str(item["id"]): deepcopy(item) for item in items}
