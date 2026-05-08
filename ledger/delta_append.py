from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pyarrow as pa

from ledger.records import ProofLedgerRecord


def _records_to_table(records: Sequence[ProofLedgerRecord]) -> pa.Table:
    rows = list(records)
    if not rows:
        raise ValueError("records must be non-empty")

    occurred_at = pa.array([r.occurred_at for r in rows], type=pa.timestamp("us", tz="UTC"))
    assistant_reply = pa.array([r.assistant_reply for r in rows], type=pa.large_string())

    def opt_str(col: list[str | None]) -> pa.Array:
        return pa.array(col, type=pa.large_string())

    correlation_id = opt_str([r.correlation_id for r in rows])
    user_prompt_sha256 = opt_str([r.user_prompt_sha256 for r in rows])
    evidence_json = pa.array([r.evidence_json() for r in rows], type=pa.large_string())
    source = pa.array([r.source for r in rows], type=pa.large_string())
    model = opt_str([r.model for r in rows])
    extra_json = opt_str([r.extra_json() for r in rows])

    return pa.table(
        {
            "occurred_at": occurred_at,
            "correlation_id": correlation_id,
            "user_prompt_sha256": user_prompt_sha256,
            "assistant_reply": assistant_reply,
            "evidence_json": evidence_json,
            "source": source,
            "model": model,
            "extra_json": extra_json,
        }
    )


def _delta_table_exists(uri: str | Path) -> bool:
    from deltalake import DeltaTable

    try:
        DeltaTable(str(uri))
        return True
    except Exception:
        return False


def append_proof_records(
    table_uri: str | Path,
    records: Sequence[ProofLedgerRecord],
    *,
    storage_options: dict[str, str] | None = None,
) -> None:
    """Append rows to a Delta table (local path, ``dbfs:``, S3, Azure, GCS per ``deltalake``).

    First write creates the table (overwrite); later writes append.
    """

    if not records:
        return

    from deltalake import write_deltalake

    table = _records_to_table(records)
    uri_str = str(table_uri)
    mode = "append" if _delta_table_exists(uri_str) else "overwrite"
    write_deltalake(uri_str, table, mode=mode, storage_options=storage_options)
