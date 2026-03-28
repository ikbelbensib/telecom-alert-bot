"""
main.py
Entry point for telecom-alert-bot.

Usage:
    python main.py --log ../logs/sample.log
    python main.py --log ../logs/sample.log --p1-only
    python main.py --log ../logs/sample.log --dry-run
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parser import parse_log_file
from alerter import dispatch_incidents


def main():
    parser = argparse.ArgumentParser(
        description="Telecom Alert Bot — detects P1/P2 incidents and sends Slack alerts."
    )
    parser.add_argument("--log", required=True, help="Path to the log file")
    parser.add_argument("--p1-only", action="store_true", help="Only alert on P1 incidents")
    parser.add_argument("--dry-run", action="store_true", help="Print incidents without sending to Slack")
    args = parser.parse_args()

    if not os.path.exists(args.log):
        print(f"[ERROR] Log file not found: {args.log}")
        sys.exit(1)

    print(f"\n📂 Parsing log file: {args.log}")
    incidents = parse_log_file(args.log)

    if not incidents:
        print("✅ No incidents detected.")
        return

    print(f"\n⚠️  {len(incidents)} incident(s) detected:")
    for inc in incidents:
        print(f"   [{inc.priority.value}] {inc.timestamp} | {inc.component} | {inc.message}")

    if args.dry_run:
        print("\n[DRY-RUN] Slack alerts not sent.")
        return

    print("\n📤 Sending alerts to Slack...")
    summary = dispatch_incidents(incidents, p1_only=args.p1_only)
    print(f"\n📋 Done — {summary.sent} sent, {summary.failed} failed.")


if __name__ == "__main__":
    main()