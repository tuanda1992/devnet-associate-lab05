#!/usr/bin/env python3
"""Safely configure the ten YAML-defined Lab 5 loopbacks."""

from __future__ import annotations

import argparse
import ipaddress

from common import connect, interface_names, load_lab


def configuration(loopbacks: list[dict]) -> list[str]:
    """Generate IOS XE commands from validated loopback metadata."""
    commands: list[str] = []
    for loopback in loopbacks:
        interface_name = f"Loopback{loopback['id']}"
        address = ipaddress.ip_interface(loopback["ipv4"])
        commands.extend(
            [
                f"interface {interface_name}",
                f"description {loopback['description']}",
                f"ip address {address.ip} {address.netmask}",
                "no shutdown",
            ]
        )
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    _, loopbacks = load_lab()
    commands = configuration(loopbacks)
    print("Proposed commands:")
    print("\n".join(commands))
    if args.dry_run:
        return 0

    with connect() as connection:
        parsed = connection.send_command("show ip interface brief", use_textfsm=True)
        if not isinstance(parsed, list):
            raise RuntimeError("Pre-check requires structured TextFSM output")
        existing = {
            row.get("intf", row.get("interface"))
            for row in parsed
            if isinstance(row, dict)
        }
        conflicts = interface_names(loopbacks) & existing
        if conflicts:
            raise RuntimeError(f"Refusing to replace existing interfaces: {sorted(conflicts)}")
        output = connection.send_config_set(commands, cmd_verify=False)
        print(output)
    print("Configuration sent. Run the post-check before declaring success.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

