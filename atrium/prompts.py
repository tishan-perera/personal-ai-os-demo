"""Scripted requests used by the UI, the CLI demo, and the tests."""

# label, request text, expected seat id, whether a proposal should open
DEMO_PROMPTS: tuple[tuple[str, str, str, bool], ...] = (
    ("Inbox", "Summarize the fictional inbox", "mail", False),
    (
        "Send reply",
        "Draft a reply to the landlord about the leak, and send it",
        "mail",
        True,
    ),
    ("Budget", "How does the November household budget look?", "finance", False),
    ("Pay rent", "Pay the fictional studio rent of 900 dollars", "finance", True),
    ("Outline", "Outline a short post about a morning desk routine", "content", False),
    ("Publish", "Publish the morning desk routine post", "content", True),
    (
        "Roles",
        "Which fictional roles fit a program coordinator background?",
        "career",
        False,
    ),
    ("Apply", "Submit the application to Northwind Labs", "career", True),
    ("Checklist", "What is left on the checklist?", "ops", False),
    ("Reminder", "Send the Friday building reminder", "ops", True),
)
