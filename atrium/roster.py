"""Fictional seats. These are not a real person's staff."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Seat:
    id: str
    name: str
    title: str
    department: str
    mandate: str
    keywords: tuple[str, ...]
    actions: tuple[str, ...]


SEATS: tuple[Seat, ...] = (
    Seat(
        id="chief",
        name="Mara Quinn",
        title="Chief of Staff",
        department="Chief of Staff",
        mandate=(
            "Routes each request to one department. Does not send, pay, publish, submit, or notify."
        ),
        keywords=(),
        actions=(),
    ),
    Seat(
        id="mail",
        name="Piper Hale",
        title="Mail clerk",
        department="Mail",
        mandate="Reads the fictional inbox and drafts replies. Sending waits for the owner.",
        keywords=(
            "inbox",
            "email",
            "e-mail",
            "mailbox",
            "landlord",
            "leak",
            "reply",
            "message",
        ),
        actions=("send_mail",),
    ),
    Seat(
        id="finance",
        name="Ellis Ward",
        title="Finance clerk",
        department="Finance",
        mandate="Explains a fictional household budget. Recording a payment waits for the owner.",
        keywords=(
            "budget",
            "rent",
            "invoice",
            "ledger",
            "payment",
            "pay",
            "dollars",
            "unpaid",
            "spend",
        ),
        actions=("record_payment",),
    ),
    Seat(
        id="content",
        name="Sable Ortiz",
        title="Content clerk",
        department="Content",
        mandate="Outlines a fictional post. Publishing waits for the owner.",
        keywords=("outline", "publish", "blog", "newsletter", "desk routine", "post"),
        actions=("publish_post",),
    ),
    Seat(
        id="career",
        name="Noah Ives",
        title="Career clerk",
        department="Career",
        mandate="Compares fictional roles. Submitting an application waits for the owner.",
        keywords=(
            "career",
            "role",
            "roles",
            "application",
            "northwind",
            "hiring",
            "resume",
            "job",
        ),
        actions=("submit_application",),
    ),
    Seat(
        id="ops",
        name="Remy Cho",
        title="Ops clerk",
        department="Ops",
        mandate="Reads a fictional checklist. Sending a reminder waits for the owner.",
        keywords=("checklist", "reminder", "ops", "friday", "notify"),
        actions=("send_reminder",),
    ),
)

SEAT_BY_ID: dict[str, Seat] = {seat.id: seat for seat in SEATS}
DEPARTMENTS: tuple[Seat, ...] = tuple(seat for seat in SEATS if seat.id != "chief")


def seat_public(seat: Seat) -> dict[str, str]:
    return {
        "id": seat.id,
        "name": seat.name,
        "title": seat.title,
        "department": seat.department,
        "mandate": seat.mandate,
    }
