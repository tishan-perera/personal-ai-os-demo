import unittest

from atrium.agents import ProposalDraft
from atrium.queue import Queue
from atrium.roster import SEAT_BY_ID
from atrium.validate import ValidationError


class QueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = Queue()
        self.mail = SEAT_BY_ID["mail"]

    def _draft(self, risk: str = "medium", action: str = "send_mail") -> ProposalDraft:
        return ProposalDraft(
            action=action,
            target="building@harbor-lane.example",
            summary="Send the fixture reply.",
            detail="A fixture draft that does not leave the machine.",
            risk=risk,
            payload={"to": "building@harbor-lane.example", "subject": "Re", "body": "Hello"},
        )

    def test_low_risk_cannot_enter_the_queue(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            self.queue.add(
                seat=self.mail,
                draft=self._draft(risk="low"),
                request="send it",
                created_at="2026-11-18T15:00:00Z",
            )
        self.assertEqual(caught.exception.code, "bad_risk")

    def test_pending_proposal_cannot_execute(self) -> None:
        item = self.queue.add(
            seat=self.mail,
            draft=self._draft(),
            request="send it",
            created_at="2026-11-18T15:00:00Z",
        )
        with self.assertRaises(ValidationError) as caught:
            self.queue.mark_executed(item["id"], {"notice": "nope"})
        self.assertEqual(caught.exception.code, "not_approved")
        self.assertEqual(self.queue.items()[0]["status"], "pending")

    def test_wrong_department_cannot_propose_an_action(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            self.queue.add(
                seat=self.mail,
                draft=self._draft(action="record_payment"),
                request="pay",
                created_at="2026-11-18T15:00:00Z",
            )
        self.assertEqual(caught.exception.code, "action_not_allowed")

    def test_bad_actor_does_not_change_status(self) -> None:
        item = self.queue.add(
            seat=self.mail,
            draft=self._draft(),
            request="send it",
            created_at="2026-11-18T15:00:00Z",
        )
        with self.assertRaises(ValidationError) as caught:
            self.queue.decide(item["id"], "approve", "  ", "", "2026-11-18T15:00:01Z")
        self.assertEqual(caught.exception.code, "actor_required")
        self.assertEqual(self.queue.items()[0]["status"], "pending")

    def test_duplicate_pending_is_rejected_and_rejected_can_be_reopened(self) -> None:
        first = self.queue.add(
            seat=self.mail,
            draft=self._draft(),
            request="send it",
            created_at="2026-11-18T15:00:00Z",
        )
        with self.assertRaises(ValidationError) as caught:
            self.queue.add(
                seat=self.mail,
                draft=self._draft(),
                request="send it again",
                created_at="2026-11-18T15:00:01Z",
            )
        self.assertEqual(caught.exception.code, "duplicate")
        self.queue.decide(first["id"], "reject", "owner", "", "2026-11-18T15:00:02Z")
        second = self.queue.add(
            seat=self.mail,
            draft=self._draft(),
            request="send it once more",
            created_at="2026-11-18T15:00:03Z",
        )
        self.assertEqual(second["status"], "pending")
        self.assertNotEqual(second["id"], first["id"])


if __name__ == "__main__":
    unittest.main()
