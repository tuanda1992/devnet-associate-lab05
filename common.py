"""Shared loading, validation, and connection helpers for Lab 5."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler


CONFIG_PATH = Path(__file__).with_name("device.yaml")
ENV_PATH = Path(__file__).with_name(".env")


def load_lab() -> tuple[dict, list[dict]]:
    """Load device and loopback metadata, then validate safe lab scope."""
    with CONFIG_PATH.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)

    if not isinstance(document, dict):
        raise ValueError("device.yaml must contain a mapping")
    device = document.get("device")
    loopbacks = document.get("loopbacks")
    if not isinstance(device, dict) or not isinstance(loopbacks, list):
        raise ValueError("device.yaml requires device and loopbacks sections")
    if device.get("host") == "REPLACE_WITH_RESERVED_ROUTER_ADDRESS":
        raise ValueError("Replace the router address in device.yaml")
    if device.get("device_type") != "cisco_ios":
        raise ValueError("This lab permits device_type cisco_ios only")
    if len(loopbacks) != 10:
        raise ValueError("This lab requires exactly ten loopbacks")

    ids: set[int] = set()
    addresses: set[ipaddress.IPv4Address] = set()
    for item in loopbacks:
        if not isinstance(item, dict):
            raise ValueError("Each loopback must be a mapping")
        interface_id = item.get("id")
        if not isinstance(interface_id, int) or not 501 <= interface_id <= 510:
            raise ValueError("Loopback IDs must be integers from 501 through 510")
        address = ipaddress.ip_interface(item.get("ipv4"))
        if address.version != 4 or address.network.prefixlen != 32:
            raise ValueError(f"Loopback{interface_id} must use an IPv4 /32")
        description = item.get("description")
        if not isinstance(description, str) or not description.startswith("LAB5_"):
            raise ValueError(f"Loopback{interface_id} requires a LAB5_ description")
        if interface_id in ids or address.ip in addresses:
            raise ValueError("Loopback IDs and addresses must be unique")
        ids.add(interface_id)
        addresses.add(address.ip)

    return device, loopbacks


def connection_parameters(device: dict) -> dict:
    """Combine non-secret YAML metadata with credentials loaded from .env."""
    load_dotenv(ENV_PATH)
    username = os.environ.get("LAB_USERNAME")
    password = os.environ.get("LAB_PASSWORD")
    if not username or not password:
        raise ValueError("Set LAB_USERNAME and LAB_PASSWORD in the local .env file")
    parameters = {
        "device_type": device["device_type"],
        "host": device["host"],
        "port": int(device.get("port", 22)),
        "username": username,
        "password": password,
        "conn_timeout": 10,
        "auth_timeout": 15,
        "banner_timeout": 20,
        "fast_cli": False,
    }
    secret = os.environ.get("LAB_SECRET")
    if secret:
        parameters["secret"] = secret
    return parameters


def connect():
    """Create a Netmiko connection to the validated lab device."""
    device, _ = load_lab()
    return ConnectHandler(**connection_parameters(device))


def interface_names(loopbacks: list[dict]) -> set[str]:
    """Return the exact interface names managed by this lab."""
    return {f"Loopback{item['id']}" for item in loopbacks}
