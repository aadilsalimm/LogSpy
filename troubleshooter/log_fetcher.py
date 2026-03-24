import subprocess
from datetime import datetime, timedelta

TIMEFRAME_TIERS = [
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(hours=24),
    timedelta(days=7),
]

def fetch_unit_logs(unit: str, until_dt: datetime, original_window: timedelta, keywords: list) -> dict:
    tiers = [original_window] + [t for t in TIMEFRAME_TIERS if t > original_window]

    for tier in tiers:
        expanded_since = (until_dt - tier).strftime("%Y-%m-%d %H:%M:%S")
        until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S")

        cmd = [
            "journalctl", "-u", unit,
            "--since", expanded_since,
            "--until", until_str,
            "-p", "warning",
            "--no-pager", "-o", "short-iso"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        if keywords:
            lines = [l for l in lines if any(kw.lower() in l.lower() for kw in keywords)]

        if lines:
            return {
                "logs": lines,
                "log_count": len(lines),
                "timeframe_used": str(tier),
                "timeframe_expanded": tier != original_window,
                "fetch_method": "journalctl_unit"
            }

    # Last resort — no time constraint, no priority filter, last 50 lines
    cmd = ["journalctl", "-u", unit, "-n", "50", "--no-pager", "-o", "short-iso"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()

    if keywords:
        lines = [l for l in lines if any(kw.lower() in l.lower() for kw in keywords)]

    if lines:
        return {
            "logs": lines,
            "log_count": len(lines),
            "timeframe_used": "unconstrained (last 50 lines)",
            "timeframe_expanded": True,
            "fetch_method": "journalctl_unit_unconstrained"
        }

    return {
        "logs": [],
        "log_count": 0,
        "timeframe_used": None,
        "timeframe_expanded": True,
        "fetch_method": "no_logs_found"
    }


def fetch_kernel_logs(subsystem: str, until_dt: datetime, original_window: timedelta, keywords: list) -> dict:
    tiers = [original_window] + [t for t in TIMEFRAME_TIERS if t > original_window]

    for tier in tiers:
        expanded_since = (until_dt - tier).strftime("%Y-%m-%d %H:%M:%S")
        until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S")

        cmd = [
            "journalctl", "-k",
            "--since", expanded_since,
            "--until", until_str,
            "--no-pager", "-o", "short-iso"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Filter by subsystem name + optional keywords
        lines = [
            l for l in result.stdout.splitlines()
            if subsystem.lower() in l.lower()
        ]
        if keywords:
            lines = [l for l in lines if any(kw.lower() in l.lower() for kw in keywords)]

        if lines:
            return {
                "logs": lines,
                "log_count": len(lines),
                "timeframe_used": str(tier),
                "timeframe_expanded": tier != original_window,
                "fetch_method": "journalctl_kernel"
            }

    # Last resort — last 100 kernel lines, filter by subsystem only
    cmd = ["journalctl", "-k", "-n", "100", "--no-pager", "-o", "short-iso"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = [l for l in result.stdout.splitlines() if subsystem.lower() in l.lower()]

    if lines:
        return {
            "logs": lines,
            "log_count": len(lines),
            "timeframe_used": "unconstrained (last 100 kernel lines)",
            "timeframe_expanded": True,
            "fetch_method": "journalctl_kernel_unconstrained"
        }

    return {
        "logs": [],
        "log_count": 0,
        "timeframe_used": None,
        "timeframe_expanded": True,
        "fetch_method": "no_logs_found"
    }


def fetch_fallback(sources: list, until_dt: datetime, original_window: timedelta, keywords: list) -> dict:
    lines = []
    expanded_since = (until_dt - original_window).strftime("%Y-%m-%d %H:%M:%S")
    until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S")

    for source in sources:
        if source == "dmesg":
            cmd = ["journalctl", "-k",
                   "--since", expanded_since, "--until", until_str,
                   "--no-pager", "-o", "short-iso"]
        elif source == "syslog":
            cmd = ["journalctl",
                   "--since", expanded_since, "--until", until_str,
                   "-p", "warning", "--no-pager", "-o", "short-iso"]
        else:
            continue

        result = subprocess.run(cmd, capture_output=True, text=True)
        lines += result.stdout.strip().splitlines()

    if keywords:
        lines = [l for l in lines if any(kw.lower() in l.lower() for kw in keywords)]

    return {
        "logs": lines,
        "log_count": len(lines),
        "timeframe_used": str(original_window),
        "timeframe_expanded": False,
        "fetch_method": "fallback"
    }


def fetch_logs(intent: dict) -> dict:
    collected = {}
    keywords = intent["query_keywords"]

    # Parse timeframe from intent
    since_dt = datetime.strptime(intent["timeframe"]["journalctl_since"], "%Y-%m-%d %H:%M:%S")
    until_dt = datetime.strptime(intent["timeframe"]["journalctl_until"], "%Y-%m-%d %H:%M:%S")
    original_window = until_dt - since_dt

    for component in intent["identified_components"]:
        name = component["component"]
        unit = component.get("journalctl_unit")
        subsystem = component.get("kernel_subsystem")

        if unit:
            result = fetch_unit_logs(unit, until_dt, original_window, keywords)
        elif subsystem:
            result = fetch_kernel_logs(subsystem, until_dt, original_window, keywords)
        else:
            result = {"logs": [], "log_count": 0, "timeframe_used": None,
                      "timeframe_expanded": False, "fetch_method": "no_logs_found"}

        collected[name] = {
            "unit": unit or f"kernel:{subsystem}",
            "confidence": component["confidence"],
            **result
        }

    # Fallback if ALL components returned no logs
    total_logs = sum(v["log_count"] for v in collected.values())
    if total_logs == 0:
        collected["_fallback"] = fetch_fallback(
            intent["fallback_sources"], until_dt, original_window, keywords
        )

    return collected



if __name__ == "__main__":
    targets = {'identified_components': [{'component': 'Wifi Network Manager', 'journalctl_unit': 'NetworkManager.service', 'kernel_subsystem': None, 'confidence': 'high'}, {'component': 'Wifi Driver', 'journalctl_unit': None, 'kernel_subsystem': 'iwlwifi', 'confidence': 'medium'}, {'component': 'DHCP Client', 'journalctl_unit': 'dhclient.service', 'kernel_subsystem': None, 'confidence': 'low'}], 'timeframe': {'type': 'relative', 'value': '1h', 'journalctl_since': '2026-03-21 10:15:28', 'journalctl_until': '2026-03-21 11:15:28'}, 'query_keywords': ['deauth', 'disconnected', 'dhcp'], 'log_priority': 'warning_and_above', 'fallback_sources': ['syslog', 'dmesg']}
    print(fetch_logs(targets))