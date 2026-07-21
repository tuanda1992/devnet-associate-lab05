#!/usr/bin/env python3
"""Collect and parse show ip interface brief with Netmiko/TextFSM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import connect


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with connect() as connection:
        parsed = connection.send_command(
            "show ip interface brief",
            use_textfsm=True,
        )

    if not isinstance(parsed, list) or any(not isinstance(row, dict) for row in parsed):
        raise RuntimeError(
            "TextFSM did not return structured records. Check ntc-templates and NET_TEXTFSM."
        )

    if parsed:
        print("TextFSM keys:", ", ".join(sorted(parsed[0])))
    for row in parsed:
        interface = row.get("intf", row.get("interface", "unknown"))
        address = row.get("ipaddr", row.get("ip_address", "unknown"))
        status = row.get("status", "unknown")
        protocol = row.get("proto", row.get("protocol", "unknown"))
        print(f"{interface:<24} {address:<16} {status:<20} {protocol}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {len(parsed)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

