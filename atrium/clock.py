"""Time source for audit stamps. Tests can pass their own clock."""

from datetime import UTC, datetime


class SystemClock:
    def now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
