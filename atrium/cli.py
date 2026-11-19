"""Command line for the fictional desk."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from atrium.llm import brain_from_env
from atrium.office import Office
from atrium.server import make_server
from atrium.validate import ValidationError


def run_demo() -> str:
    office = Office(brain=brain_from_env({"ATRIUM_LLM": "off"}))
    lines = [
        "ATRIUM · fictional demo · deterministic · no API key",
        "Seats and requests are invented. Nothing here is a real account.",
        "",
    ]

    def ask(text: str) -> dict[str, Any]:
        result = office.handle(text)
        lines.append(f"You    {text}")
        lines.append(result["turn"]["reply"])
        lines.append(f"Route  {result['turn']['department']} · {result['turn']['reason']}")
        lines.append("")
        return result

    ask("Summarize the fictional inbox")
    pay = ask("Pay the fictional studio rent of 900 dollars")
    mail = ask("Draft a reply to the landlord about the leak, and send it")
    lines.append(
        f"World before decisions: studio rent {office.world['flags']['studio_rent']}, "
        f"sent messages {office.world['flags']['sent_messages']}."
    )
    lines.append("")
    rejected = office.decide(mail["proposal"]["id"], "reject", actor="owner")
    lines.append(f"You    reject {rejected['proposal']['id']}")
    lines.append(rejected["proposal"]["detail"])
    lines.append("Result rejected. No email left this machine. Studio rent is still unpaid.")
    lines.append("")
    approved = office.decide(pay["proposal"]["id"], "approve", actor="owner")
    lines.append(f"You    approve {approved['proposal']['id']}")
    lines.append(str(approved["proposal"]["execution"]["notice"]))
    lines.append(
        f"World after decisions: studio rent {office.world['flags']['studio_rent']}, "
        f"sent messages {office.world['flags']['sent_messages']}."
    )
    lines.append("")
    lines.append("Audit")
    for event in office.audit:
        lines.append(f"  {event['id']}  {event['kind']:9}  {event['summary']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"
    try:
        if command == "demo":
            print(run_demo())
            return 0
        office = _load_office(args.state)
        if command == "serve":
            return _serve(office, args.host, args.port)
        if command == "ask":
            result = office.handle(args.text)
            print(result["turn"]["reply"])
            print()
            print(f"Route  {result['turn']['department']} · {result['turn']['reason']}")
            return 0
        if command == "queue":
            _print_queue(office)
            return 0
        if command == "audit":
            _print_audit(office)
            return 0
        if command == "decide":
            result = office.decide(args.proposal_id, args.decision, actor="owner", note=args.note)
            proposal = result["proposal"]
            print(f"{proposal['id']}  {proposal['status']}")
            if proposal["status"] == "executed":
                print(proposal["execution"]["notice"])
            else:
                print("No-op. The demo world was left unchanged.")
            return 0
    except ValidationError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"Could not use that state file: {exc}", file=sys.stderr)
        return 2
    print(f"Unknown command: {command}", file=sys.stderr)
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atrium",
        description=(
            "Fictional personal AI team. A chief of staff routes work, "
            "and consequential actions wait for the owner."
        ),
    )
    parser.add_argument(
        "--state",
        help="Optional JSON file. CLI commands share a queue when you pass the same path.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="Open the local web desk (the default).")
    sub.add_parser("demo", help="Print a scripted approve-and-reject session.")
    ask = sub.add_parser("ask", help="Send one request.")
    ask.add_argument("text")
    sub.add_parser("queue", help="List proposals.")
    sub.add_parser("audit", help="Print the audit log.")
    decide = sub.add_parser("decide", help="Approve or reject one proposal.")
    decide.add_argument("proposal_id")
    decide.add_argument("decision", choices=("approve", "reject"))
    decide.add_argument("--note", default="")
    return parser


def _load_office(path: str | None) -> Office:
    brain = brain_from_env()
    if not path:
        return Office(brain=brain)
    file = Path(path)
    if file.exists():
        data = json.loads(file.read_text(encoding="utf-8"))
        office = Office.from_snapshot(data, brain=brain)
    else:
        office = Office(brain=brain)

    def on_change(current: Office) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        blob = json.dumps(current.snapshot(), indent=2) + "\n"
        file.write_text(blob, encoding="utf-8")

    office.on_change = on_change
    return office


def _serve(office: Office, host: str, port: int) -> int:
    server = make_server(office, host, port, quiet=False)
    bound_host, bound_port = server.server_address[:2]
    print(
        f"Atrium demo at http://{bound_host}:{bound_port}  "
        "(fictional data, deterministic demo, no API key required)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


def _print_queue(office: Office) -> None:
    items = office.queue.items()
    if not items:
        print("Queue is empty.")
        return
    for item in items:
        print(f"{item['id']}  {item['status']:9}  {item['risk']:6}  {item['summary']}")


def _print_audit(office: Office) -> None:
    if not office.audit:
        print("Audit log is empty.")
        return
    for event in office.audit:
        print(f"{event['id']}  {event['kind']:9}  {event['summary']}")


if __name__ == "__main__":
    raise SystemExit(main())
