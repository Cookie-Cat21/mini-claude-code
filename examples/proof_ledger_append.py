#!/usr/bin/env python3
"""Call your deployed ``POST /api/chat`` then append an audit row to a Delta table.

Runs locally or inside Databricks (use ``dbfs:`` / cloud URIs with credentials).

Example::

    export VERCEL_CHAT_URL=https://your-app.vercel.app/api/chat
    pip install -r requirements.txt -r requirements-ledger.txt
    python examples/proof_ledger_append.py \\
        --delta-path /tmp/proof_ledger \\
        --messages-json '[]' \\
        --new-message "Summarize pipeline failures from bronze.orders_load."

Evidence pointers should describe warehouse objects your organization trusts
(Unity Catalog names, Delta versions, job run ids). Supply JSON via ``--evidence``.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


def _post_chat(base_chat_url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_chat_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Request failed: {e}") from e
    return json.loads(body)


def main() -> None:
    from ledger import EvidencePointer, append_proof_records, record_from_chat_response

    parser = argparse.ArgumentParser(description="Post /api/chat and append proof ledger row.")
    parser.add_argument(
        "--chat-url",
        default=None,
        help="Full URL to POST /api/chat (default env VERCEL_CHAT_URL)",
    )
    parser.add_argument("--delta-path", required=True, help="Local path or cloud Delta URI")
    parser.add_argument(
        "--messages-json",
        default="[]",
        help='Prior turns JSON array [{"role":"user|assistant","content":"..."}]',
    )
    parser.add_argument("--new-message", required=True)
    parser.add_argument(
        "--evidence",
        default="[]",
        help='JSON array of objects with keys kind, identifier, optional delta_version, snapshot_id, query_id, notes',
    )
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    chat_url = args.chat_url or os.environ.get("VERCEL_CHAT_URL")
    if not chat_url:
        raise SystemExit("Pass --chat-url or set VERCEL_CHAT_URL")

    messages = json.loads(args.messages_json)
    evidence_raw = json.loads(args.evidence)
    evidence = [
        EvidencePointer(
            kind=e["kind"],
            identifier=e["identifier"],
            delta_version=e.get("delta_version"),
            snapshot_id=e.get("snapshot_id"),
            query_id=e.get("query_id"),
            notes=e.get("notes"),
        )
        for e in evidence_raw
    ]

    chat = _post_chat(chat_url, {"messages": messages, "new_message": args.new_message})
    reply = chat.get("response") or ""

    record = record_from_chat_response(
        assistant_reply=reply,
        evidence=evidence,
        user_message=args.new_message,
        correlation_id=args.correlation_id,
        source="proof_ledger_example",
        model=args.model,
        extra={"vercel_messages_returned": len(chat.get("messages") or [])},
    )

    append_proof_records(args.delta_path, [record])
    print(reply)


if __name__ == "__main__":
    main()
