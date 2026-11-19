"""Department planners. Replies and payloads come from fixtures, not from the request."""

from dataclasses import dataclass
from typing import Any

from atrium.roster import SEAT_BY_ID
from atrium.router import tokens
from atrium.world import LANDLORD_DRAFT


@dataclass(frozen=True)
class ProposalDraft:
    action: str
    target: str
    summary: str
    detail: str
    risk: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class Plan:
    reply: str
    proposal: ProposalDraft | None = None


def plan_for(seat_id: str, text: str, world: dict[str, Any]) -> Plan:
    planners = {
        "chief": plan_chief,
        "mail": plan_mail,
        "finance": plan_finance,
        "content": plan_content,
        "career": plan_career,
        "ops": plan_ops,
    }
    planner = planners.get(seat_id)
    if planner is None:
        raise KeyError(seat_id)
    return planner(text, world)


def plan_chief(text: str, world: dict[str, Any]) -> Plan:
    del text, world
    return Plan(
        "Mara Quinn · Chief of Staff\n\n"
        "I route work. I do not send, pay, publish, submit, or notify.\n\n"
        "Desks: Mail (Piper Hale), Finance (Ellis Ward), Content (Sable Ortiz), "
        "Career (Noah Ives), and Ops (Remy Cho).\n\n"
        "If two desks match, I keep the request. Name one desk, or pick a prompt. "
        "Anything consequential waits on the approval queue until you decide."
    )


def plan_mail(text: str, world: dict[str, Any]) -> Plan:
    words = tokens(text)
    if "send" in words or "forward" in words:
        draft = ProposalDraft(
            action="send_mail",
            target="building@harbor-lane.example",
            summary="Send a reply to building@harbor-lane.example about the leak.",
            detail=LANDLORD_DRAFT,
            risk="medium",
            payload={
                "to": "building@harbor-lane.example",
                "subject": "Re: Leak in 4B",
                "body": LANDLORD_DRAFT,
            },
        )
        reply = (
            "Piper Hale · Mail\n\n"
            "I drafted a reply to the fictional building desk. I did not send it.\n\n"
            f"Draft: {LANDLORD_DRAFT}"
        )
        return Plan(reply, draft)
    if "draft" in words or "reply" in words:
        return Plan(
            "Piper Hale · Mail\n\n"
            "Here is a reply, left in the draft pile. It has not been sent.\n\n"
            f"Draft: {LANDLORD_DRAFT}\n\n"
            "Ask me to send it if you want an approval card."
        )
    lines = [
        "Piper Hale · Mail",
        "",
        "Fictional Harbor Lane inbox. No mailbox provider is connected.",
        "",
    ]
    for message in world["inbox"]:
        mark = "unread" if message["unread"] else "read"
        lines.append(f"- {message['from']} — {message['subject']} ({mark})")
        lines.append(f"  {message['preview']}")
    sent = world["flags"]["sent_messages"]
    lines.append("")
    lines.append(f"Simulated messages sent: {sent}.")
    return Plan("\n".join(lines))


def plan_finance(text: str, world: dict[str, Any]) -> Plan:
    words = tokens(text)
    if "pay" in words or "transfer" in words:
        if world["flags"]["studio_rent"] == "recorded-simulated":
            return Plan(
                "Ellis Ward · Finance\n\n"
                "The fictional studio rent is already marked recorded-simulated. "
                "I did not open another payment."
            )
        draft = ProposalDraft(
            action="record_payment",
            target="harbor-studio-november",
            summary="Record the fictional Harbor Studio rent of 900 dollars.",
            detail=(
                "Payee: Harbor Studio (fictional). Amount: 900 USD. "
                "Memo: November studio desk. No account number is stored."
            ),
            risk="high",
            payload={
                "payee": "Harbor Studio (fictional)",
                "amount_usd": 900,
                "memo": "November studio desk",
            },
        )
        return Plan(
            "Ellis Ward · Finance\n\n"
            "I can mark 900 dollars of fictional studio rent in the demo ledger. "
            "No bank is connected, and I have not recorded it yet.",
            draft,
        )
    return Plan(_budget_reply(world))


def _budget_reply(world: dict[str, Any]) -> str:
    budget = world["budget"]
    lines = [
        "Ellis Ward · Finance",
        "",
        f"Fictional {budget['month']} household budget. Nothing here is a bank.",
        "",
        f"Income: {budget['income']} {budget['currency']}",
    ]
    for line in budget["lines"]:
        if "spent" in line:
            lines.append(f"{line['item']}: {line['spent']} spent of {line['planned']} planned")
        else:
            status = line["status"]
            if line["item"].startswith("Harbor Studio"):
                status = world["flags"]["studio_rent"]
            lines.append(f"{line['item']}: {line['planned']} {status}")
    lines.append(f"Left to assign: {budget['unallocated']} {budget['currency']}")
    lines.append("")
    lines.append("Paying the studio desk opens an approval card. This demo cannot move money.")
    return "\n".join(lines)


def plan_content(text: str, world: dict[str, Any]) -> Plan:
    words = tokens(text)
    title = world["post"]["title"]
    if "publish" in words:
        if world["flags"]["post"] == "published-simulated":
            return Plan(
                "Sable Ortiz · Content\n\nThe fictional post is already marked published-simulated."
            )
        draft = ProposalDraft(
            action="publish_post",
            target="morning-desk-routine",
            summary="Publish the fictional morning desk routine post.",
            detail=f"Title: {title}. Board: the in-memory demo board only.",
            risk="medium",
            payload={"title": title},
        )
        return Plan(
            "Sable Ortiz · Content\n\n"
            f'I can mark "{title}" published on the in-memory board. '
            "No site is connected, and I have not published it.",
            draft,
        )
    return Plan(
        "Sable Ortiz · Content\n\n"
        f'Outline for "{title}":\n'
        "1. Clear the desk before opening the fictional inbox.\n"
        "2. One 15-minute writing block, then stop.\n"
        "3. Leave a one-line note for the next morning.\n\n"
        "This is an outline only. Publishing waits for a separate approval."
    )


def plan_career(text: str, world: dict[str, Any]) -> Plan:
    words = tokens(text)
    application = world["application"]
    if "submit" in words or "apply" in words:
        if world["flags"]["application"] == "submitted-simulated":
            return Plan(
                "Noah Ives · Career\n\n"
                "The fictional application is already marked submitted-simulated."
            )
        draft = ProposalDraft(
            action="submit_application",
            target="northwind-labs-program-coordinator",
            summary="Submit the fictional Northwind Labs application.",
            detail=(
                f"Role: {application['role']} at {application['org']}. "
                f"Closes {application['closes']}. No employer is contacted."
            ),
            risk="high",
            payload={
                "org": application["org"],
                "role": application["role"],
            },
        )
        return Plan(
            "Noah Ives · Career\n\n"
            "I can mark the fictional Program Coordinator application as submitted. "
            "No employer is connected, and I have not submitted it.",
            draft,
        )
    return Plan(
        "Noah Ives · Career\n\n"
        "Two fictional roles, for a program-coordinator kind of background:\n"
        f"- {application['role']} at {application['org']}. "
        "Fit notes: process notes and stakeholder updates. "
        f"Status: {world['flags']['application']}. Closes {application['closes']}.\n"
        "- Editorial coordinator at Lantern Weekly (fictional). "
        "Fit notes: a small calendar of made-up assignments.\n\n"
        "Nothing has been submitted."
    )


def plan_ops(text: str, world: dict[str, Any]) -> Plan:
    words = tokens(text)
    reminder = world["reminder"]
    if "send" in words or "notify" in words or "ping" in words:
        if world["flags"]["reminder"] == "sent-simulated":
            return Plan(
                "Remy Cho · Ops\n\nThe fictional Friday reminder is already marked sent-simulated."
            )
        draft = ProposalDraft(
            action="send_reminder",
            target="friday-building-reminder",
            summary="Send the fictional Friday building reminder.",
            detail=reminder["text"],
            risk="medium",
            payload={"name": reminder["name"], "text": reminder["text"]},
        )
        return Plan(
            "Remy Cho · Ops\n\n"
            "I can mark the Friday building reminder as sent inside this demo. "
            "No chat is connected, and I have not sent it.\n\n"
            f"Draft: {reminder['text']}",
            draft,
        )
    lines = ["Remy Cho · Ops", "", "Fictional checklist. Nothing here runs on a timer.", ""]
    for item in world["checklist"]:
        mark = "done" if item["done"] else "open"
        lines.append(f"- [{mark}] {item['label']}")
    lines.append("")
    lines.append(f"Reminder status: {world['flags']['reminder']}.")
    return Plan("\n".join(lines))


def seat_label(seat_id: str) -> str:
    seat = SEAT_BY_ID[seat_id]
    return f"{seat.department} · {seat.name}"
