from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidencePointer:
    """Structured pointer so Delta rows stay auditable without dumping full warehouse state."""

    kind: str
    """e.g. ``delta_table``, ``unity_table``, ``sql``, ``notebook``, ``job_run``."""

    identifier: str
    """Table name, path, job id, or other stable id."""

    delta_version: int | None = None
    snapshot_id: str | None = None
    query_id: str | None = None
    notes: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


@dataclass(frozen=True)
class ProofLedgerRecord:
    """One assistant interaction plus receipts-style metadata for the lakehouse."""

    assistant_reply: str
    evidence: Sequence[EvidencePointer]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
    user_prompt_sha256: str | None = None
    source: str = "unknown"
    model: str | None = None
    extra: Mapping[str, Any] | None = None

    def evidence_json(self) -> str:
        return json.dumps([e.to_json_dict() for e in self.evidence], sort_keys=True)

    def extra_json(self) -> str | None:
        if not self.extra:
            return None
        return json.dumps(dict(self.extra), sort_keys=True)


def record_from_chat_response(
    *,
    assistant_reply: str,
    evidence: Sequence[EvidencePointer],
    user_message: str | None = None,
    hash_user_prompt: bool = True,
    correlation_id: str | None = None,
    source: str = "vercel",
    model: str | None = None,
    extra: Mapping[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> ProofLedgerRecord:
    """Build a ledger row after calling ``POST /api/chat`` (or any other assistant surface)."""

    prompt_hash: str | None = None
    if user_message is not None and hash_user_prompt:
        prompt_hash = sha256_text(user_message)

    kwargs: dict[str, Any] = {
        "assistant_reply": assistant_reply,
        "evidence": evidence,
        "correlation_id": correlation_id,
        "user_prompt_sha256": prompt_hash,
        "source": source,
        "model": model,
        "extra": extra,
    }
    if occurred_at is not None:
        kwargs["occurred_at"] = occurred_at
    return ProofLedgerRecord(**kwargs)
