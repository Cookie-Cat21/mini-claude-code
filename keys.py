"""Collect and dedupe API keys from the environment (single or comma-separated lists)."""

import os


def collect_api_keys(single_var: str, multi_var: str) -> list[str]:
    seen: set[str] = set()
    keys: list[str] = []
    raw = os.environ.get(single_var, "").strip()
    if raw and raw not in seen:
        seen.add(raw)
        keys.append(raw)
    bulk = os.environ.get(multi_var, "")
    for part in bulk.replace("\n", ",").split(","):
        k = part.strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    return keys
