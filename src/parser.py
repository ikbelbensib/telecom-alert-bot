"""
parser.py
Reads telecom log files and detects P1/P2 incidents based on keywords and patterns.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Priority(Enum):
    P1 = "P1"
    P2 = "P2"


INCIDENT_PATTERNS = {
    Priority.P1: [
        r"CRITICAL",
        r"SERVICE_DOWN",
        r"OUTAGE",
        r"SLA_BREACH",
        r"CORE_FAILURE",
    ],
    Priority.P2: [
        r"ERROR",
        r"DEGRADED",
        r"TIMEOUT",
        r"HIGH_LATENCY",
        r"PROVISIONING_FAIL",
    ],
}

LOG_PATTERN = re.compile(
    r"\[(?P<timestamp>[^\]]+)\]\s+"
    r"\[(?P<level>[^\]]+)\]\s+"
    r"\[(?P<component>[^\]]+)\]\s+"
    r"(?P<message>.+)"
)


@dataclass
class Incident:
    timestamp: str
    priority: Priority
    component: str
    message: str
    raw_line: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_slack_block(self) -> dict:
        emoji = "🔴" if self.priority == Priority.P1 else "🟠"
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{emoji} *{self.priority.value} Incident Detected*\n"
                    f"*Time:* {self.timestamp}\n"
                    f"*Component:* `{self.component}`\n"
                    f"*Message:* {self.message}"
                ),
            },
        }


def parse_log_line(line: str) -> dict | None:
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    return match.groupdict()


def detect_incident(parsed: dict, raw_line: str) -> "Incident | None":
    message = parsed["message"].upper()
    for priority in [Priority.P1, Priority.P2]:
        for pattern in INCIDENT_PATTERNS[priority]:
            if re.search(pattern, message):
                return Incident(
                    timestamp=parsed["timestamp"],
                    priority=priority,
                    component=parsed["component"],
                    message=parsed["message"],
                    raw_line=raw_line,
                )
    return None


def parse_log_file(filepath: str) -> list:
    incidents = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            parsed = parse_log_line(line)
            if parsed is None:
                print(f"[WARN] Line {line_num} skipped — bad format.")
                continue
            incident = detect_incident(parsed, line.strip())
            if incident:
                incidents.append(incident)
    return incidents