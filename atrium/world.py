"""In-memory fictional world. apply_action is the only mutator."""

from copy import deepcopy
from typing import Any

RECEIPTS: dict[str, str] = {
    "send_mail": "Simulated send. No email left this machine.",
    "record_payment": "Simulated ledger mark. No bank was contacted and no money moved.",
    "publish_post": "Simulated publish on the fictional board. No site was updated.",
    "submit_application": "Simulated submission. No employer was contacted.",
    "send_reminder": "Simulated reminder. No chat or SMS was sent.",
}

LANDLORD_DRAFT = (
    "Thanks for flagging the stain in 4B. Thursday 4-6pm works for a visit. - Harbor Lane Demo"
)

POST_TITLE = "A morning desk routine that fits in 20 minutes"


def fresh_world() -> dict[str, Any]:
    return {
        "inbox": [
            {
                "id": "MSG-1",
                "from": "building@harbor-lane.example",
                "subject": "Leak in 4B",
                "preview": "The ceiling stain is back. Can you confirm a visit window?",
                "unread": True,
            },
            {
                "id": "MSG-2",
                "from": "editor@lantern-weekly.example",
                "subject": "Desk-routine note",
                "preview": "The fictional Friday note still needs an outline.",
                "unread": True,
            },
            {
                "id": "MSG-3",
                "from": "hello@northwind-labs.example",
                "subject": "Interest form received",
                "preview": "Applications for the fictional program role close December 2.",
                "unread": False,
            },
        ],
        "sent": [],
        "budget": {
            "month": "November",
            "currency": "USD",
            "income": 4200,
            "unallocated": 880,
            "lines": [
                {"item": "Apartment rent", "planned": 1800, "status": "planned"},
                {
                    "item": "Harbor Studio desk (fictional)",
                    "planned": 900,
                    "status": "unpaid",
                },
                {"item": "Groceries", "planned": 500, "spent": 420, "status": "in progress"},
                {"item": "Transit", "planned": 120, "spent": 80, "status": "in progress"},
            ],
        },
        "post": {"title": POST_TITLE, "status": "outline"},
        "application": {
            "role": "Program Coordinator",
            "org": "Northwind Labs (fictional)",
            "status": "not_submitted",
            "closes": "December 2",
        },
        "reminder": {
            "name": "Friday building reminder",
            "status": "draft",
            "text": "Friday 5pm: hallway plants get a watering. Harbor Lane demo only.",
        },
        "checklist": [
            {"id": "passphrase", "label": "Rotate the demo passphrase note", "done": False},
            {"id": "receipts", "label": "Export last month's fictional receipts", "done": False},
            {
                "id": "reminder",
                "label": "Friday building reminder is still a draft",
                "done": False,
            },
        ],
        "flags": {
            "sent_messages": 0,
            "studio_rent": "unpaid",
            "post": "outline",
            "application": "not_submitted",
            "reminder": "draft",
        },
    }


def apply_action(world: dict[str, Any], action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Apply one already-approved fixture action. Unknown actions do not mutate."""
    if action not in RECEIPTS:
        raise ValueError(f"Unknown action: {action}")
    notice = RECEIPTS[action]
    if action == "send_mail":
        world["sent"].append(
            {
                "to": payload["to"],
                "subject": payload["subject"],
                "body": payload["body"],
                "simulated": True,
            }
        )
        world["flags"]["sent_messages"] += 1
    elif action == "record_payment":
        world["flags"]["studio_rent"] = "recorded-simulated"
        for line in world["budget"]["lines"]:
            if line["item"].startswith("Harbor Studio"):
                line["status"] = "recorded-simulated"
    elif action == "publish_post":
        world["flags"]["post"] = "published-simulated"
        world["post"]["status"] = "published-simulated"
    elif action == "submit_application":
        world["flags"]["application"] = "submitted-simulated"
        world["application"]["status"] = "submitted-simulated"
    elif action == "send_reminder":
        world["flags"]["reminder"] = "sent-simulated"
        world["reminder"]["status"] = "sent-simulated"
        for item in world["checklist"]:
            if item["id"] == "reminder":
                item["done"] = True
                item["label"] = "Friday building reminder marked sent-simulated"
    return {"simulated": True, "action": action, "notice": notice}


def copy_world(world: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(world)
