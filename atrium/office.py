"""Office: route, propose, decide, then execute or no-op. The gate lives here."""

from copy import deepcopy
from typing import Any

from atrium import __version__
from atrium.agents import plan_for
from atrium.clock import SystemClock
from atrium.llm import DemoBrain, brain_from_env
from atrium.prompts import DEMO_PROMPTS
from atrium.queue import Queue
from atrium.roster import SEAT_BY_ID, SEATS, seat_public
from atrium.router import route_request
from atrium.validate import ValidationError, validate_request
from atrium.world import apply_action, fresh_world

GATE_LINE = "Queued {proposal_id}. Nothing runs until you approve it."


class Office:
    def __init__(self, brain: Any = None, clock: Any = None, on_change: Any = None) -> None:
        self.brain = brain if brain is not None else brain_from_env()
        self.clock = clock if clock is not None else SystemClock()
        self.on_change = on_change
        self.world = fresh_world()
        self.queue = Queue()
        self.audit: list[dict[str, Any]] = []
        self.turns: list[dict[str, Any]] = []
        self._turn_seq = 0
        self._audit_seq = 0

    def handle(self, text: str) -> dict[str, Any]:
        cleaned = validate_request(text)
        route = route_request(cleaned)
        seat = SEAT_BY_ID[route.seat_id]
        plan = plan_for(seat.id, cleaned, self.world)
        proposal = None
        duplicate_note = None
        if plan.proposal is not None:
            try:
                proposal = self.queue.add(
                    seat=seat,
                    draft=plan.proposal,
                    request=cleaned,
                    created_at=self.clock.now(),
                )
            except ValidationError as exc:
                if exc.code != "duplicate":
                    raise
                duplicate_note = str(exc)
        reply = plan.reply
        mode = "demo"
        if proposal is not None and self.brain.enabled:
            phrased = self.brain.phrase(
                seat_name=seat.name,
                mandate=seat.mandate,
                request=cleaned,
                scripted=plan.reply,
                pending=True,
            )
            if phrased:
                reply = phrased
                mode = "llm"
        if proposal is not None:
            reply = reply.rstrip() + "\n\n" + GATE_LINE.format(proposal_id=proposal["id"])
        elif duplicate_note:
            reply = reply.rstrip() + "\n\n" + duplicate_note
        proposal_id = None if proposal is None else proposal["id"]
        turn = self._append_turn(
            request=cleaned,
            seat_id=seat.id,
            seat_name=seat.name,
            department=seat.department,
            reason=route.reason,
            reply=reply,
            proposal_id=proposal_id,
            mode=mode,
        )
        self._audit(
            "routed",
            "mara-quinn",
            proposal_id,
            f"Routed to {seat.department} · {seat.name}. {route.reason}",
        )
        if proposal is not None:
            self._audit(
                "proposed",
                seat.id,
                proposal["id"],
                f"{seat.name} proposed {proposal['action']} ({proposal['id']}).",
            )
        self._touch()
        return {"turn": turn, "proposal": proposal}

    def decide(
        self,
        proposal_id: str,
        decision: object,
        actor: object = "owner",
        note: object = "",
    ) -> dict[str, Any]:
        item = self.queue.decide(
            proposal_id,
            decision,
            actor,
            note,
            self.clock.now(),
        )
        if item["status"] == "rejected":
            self._audit(
                "rejected",
                str(item["decided_by"]),
                item["id"],
                f"{item['decided_by']} rejected {item['id']}.",
            )
            self._audit(
                "noop",
                "mara-quinn",
                item["id"],
                f"Rejected {item['id']}. No-op: the demo world was left unchanged.",
            )
            chief = SEAT_BY_ID["chief"]
            self._append_turn(
                request=f"Reject {item['id']}",
                seat_id=chief.id,
                seat_name=chief.name,
                department=chief.department,
                reason="Owner rejected the proposal. Nothing ran.",
                reply=(
                    f"{chief.name} · {chief.department}\n\n"
                    f"You rejected {item['id']}. "
                    "No-op: the demo world was left unchanged."
                ),
                proposal_id=item["id"],
                mode="demo",
            )
            self._touch()
            return {"proposal": item, "world_flags": deepcopy(self.world["flags"])}
        self._audit(
            "approved",
            str(item["decided_by"]),
            item["id"],
            f"{item['decided_by']} approved {item['id']} before anything ran.",
        )
        execution = apply_action(self.world, item["action"], item["payload"])
        finished = self.queue.mark_executed(item["id"], execution)
        self._audit(
            "executed",
            str(finished["seat_id"]),
            finished["id"],
            str(execution["notice"]),
        )
        seat = SEAT_BY_ID[str(finished["seat_id"])]
        self._append_turn(
            request=f"Approve {finished['id']}",
            seat_id=seat.id,
            seat_name=seat.name,
            department=seat.department,
            reason="Owner approved the proposal, then the demo ran it.",
            reply=(
                f"{seat.name} · {seat.department}\n\n"
                f"You approved {finished['id']}. {execution['notice']}"
            ),
            proposal_id=finished["id"],
            mode="demo",
        )
        self._touch()
        return {"proposal": finished, "world_flags": deepcopy(self.world["flags"])}

    def _append_turn(
        self,
        *,
        request: str,
        seat_id: str,
        seat_name: str,
        department: str,
        reason: str,
        reply: str,
        proposal_id: str | None,
        mode: str,
    ) -> dict[str, Any]:
        self._turn_seq += 1
        turn = {
            "id": f"TURN-{self._turn_seq:03d}",
            "at": self.clock.now(),
            "request": request,
            "seat_id": seat_id,
            "seat_name": seat_name,
            "department": department,
            "reason": reason,
            "reply": reply,
            "proposal_id": proposal_id,
            "mode": mode,
        }
        self.turns.append(turn)
        return turn

    def state(self) -> dict[str, Any]:
        return {
            "product": "Atrium",
            "version": __version__,
            "fictional": True,
            "notice": (
                "Fictional demo. Invented seats and requests. "
                "Not a real inbox, ledger, or application."
            ),
            "mode": "llm" if self.brain.enabled else "demo",
            "llm_enabled": bool(self.brain.enabled),
            "roster": [seat_public(seat) for seat in SEATS],
            "prompts": [
                {"label": label, "text": text} for label, text, _seat, _proposal in DEMO_PROMPTS
            ],
            "turns": deepcopy(self.turns),
            "proposals": self.queue.items(),
            "audit": deepcopy(self.audit),
            "world": {
                "flags": deepcopy(self.world["flags"]),
                "checklist": deepcopy(self.world["checklist"]),
            },
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": 1,
            "world": deepcopy(self.world),
            "proposals": self.queue.items(),
            "proposal_seq": self.queue.seq,
            "audit": deepcopy(self.audit),
            "turns": deepcopy(self.turns),
            "turn_seq": self._turn_seq,
            "audit_seq": self._audit_seq,
        }

    @classmethod
    def from_snapshot(
        cls,
        data: dict[str, Any],
        brain: Any = None,
        clock: Any = None,
        on_change: Any = None,
    ) -> "Office":
        office = cls(brain=brain if brain is not None else DemoBrain(), clock=clock, on_change=None)
        office.world = deepcopy(data["world"])
        office.queue.load(int(data["proposal_seq"]), list(data["proposals"]))
        office.audit = deepcopy(data["audit"])
        office.turns = deepcopy(data["turns"])
        office._turn_seq = int(data["turn_seq"])
        office._audit_seq = int(data["audit_seq"])
        office.on_change = on_change
        return office

    def _audit(self, kind: str, actor: str, proposal_id: str | None, summary: str) -> None:
        self._audit_seq += 1
        self.audit.append(
            {
                "id": f"AUD-{self._audit_seq:03d}",
                "at": self.clock.now(),
                "kind": kind,
                "actor": actor,
                "proposal_id": proposal_id,
                "summary": summary,
            }
        )

    def _touch(self) -> None:
        if self.on_change is not None:
            self.on_change(self)
