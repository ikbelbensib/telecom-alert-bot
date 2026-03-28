"""
alerter.py
Sends incident alerts to a Slack channel via Incoming Webhooks.
"""

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass

from .parser import Incident, Priority



SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


@dataclass
class AlertSummary:
    total: int
    p1_count: int
    p2_count: int
    sent: int
    failed: int


def send_slack_alert(incident: Incident, webhook_url: str = SLACK_WEBHOOK_URL) -> bool:
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL is not set. Check your .env file.")

    payload = {"blocks": [incident.to_slack_block(), {"type": "divider"}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Slack HTTP error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"[ERROR] Slack connection error: {e.reason}")
        return False


def send_summary(incidents: list, webhook_url: str = SLACK_WEBHOOK_URL) -> None:
    if not incidents:
        return
    p1 = sum(1 for i in incidents if i.priority == Priority.P1)
    p2 = len(incidents) - p1
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📋 Incident Scan Summary"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total:* {len(incidents)}"},
                    {"type": "mrkdwn", "text": f"*🔴 P1:* {p1}   *🟠 P2:* {p2}"},
                ],
            },
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[WARN] Could not send summary: {e}")


def dispatch_incidents(
    incidents: list,
    webhook_url: str = SLACK_WEBHOOK_URL,
    p1_only: bool = False,
) -> AlertSummary:
    sent, failed = 0, 0
    targets = [i for i in incidents if not p1_only or i.priority == Priority.P1]

    for incident in targets:
        success = send_slack_alert(incident, webhook_url)
        if success:
            sent += 1
            print(f"[OK]   {incident.priority.value} alert sent — {incident.component}")
        else:
            failed += 1
            print(f"[FAIL] Could not send: {incident.raw_line[:60]}...")

    send_summary(incidents, webhook_url)

    return AlertSummary(
        total=len(incidents),
        p1_count=sum(1 for i in incidents if i.priority == Priority.P1),
        p2_count=sum(1 for i in incidents if i.priority == Priority.P2),
        sent=sent,
        failed=failed,
    )