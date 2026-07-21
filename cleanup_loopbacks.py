#!/usr/bin/env python3
"""Remove only the loopback interfaces defined by Lab 5 YAML."""

from __future__ import annotations

import argparse

from common import connect, load_lab


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    _, loopbacks = load_lab()
    commands = [f"no interface Loopback{item['id']}" for item in loopbacks]
    print("Cleanup commands:")
    print("\n".join(commands))
    if args.dry_run:
        return 0

    with connect() as connection:
        for item in loopbacks:
            interface_name = f"Loopback{item['id']}"
            running = connection.send_command(
                f"show running-config interface {interface_name}"
            )
            expected = f"description {item['description']}"
            if expected not in running:
                raise RuntimeError(
                    f"Refusing to remove {interface_name}: expected lab description not found"
                )
        output = connection.send_config_set(commands)
        print(output)
    print("Cleanup sent. Run show_interfaces.py to verify removal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
