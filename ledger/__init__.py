"""Proof ledger: append-only Delta records that tie assistant text to evidence pointers."""

from ledger.records import EvidencePointer, ProofLedgerRecord, record_from_chat_response, sha256_text
from ledger.delta_append import append_proof_records

__all__ = [
    "EvidencePointer",
    "ProofLedgerRecord",
    "append_proof_records",
    "record_from_chat_response",
    "sha256_text",
]
