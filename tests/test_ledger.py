import tempfile
import unittest
from datetime import datetime, timezone

try:
    from deltalake import DeltaTable
except ImportError:  # pragma: no cover
    DeltaTable = None

from ledger.records import EvidencePointer, ProofLedgerRecord, record_from_chat_response, sha256_text
from ledger.delta_append import append_proof_records


@unittest.skipUnless(DeltaTable, "deltalake not installed; pip install -r requirements-ledger.txt")
class TestProofLedger(unittest.TestCase):
    def test_sha256_text_stable(self) -> None:
        self.assertEqual(
            sha256_text("hello"),
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        )

    def test_evidence_json_sorting(self) -> None:
        e1 = EvidencePointer(kind="delta_table", identifier="main.metrics")
        e2 = EvidencePointer(kind="job_run", identifier="run-123", query_id="q-9")
        r = ProofLedgerRecord(assistant_reply="ok", evidence=(e2, e1))
        self.assertIn('"identifier": "main.metrics"', r.evidence_json())

    def test_append_proof_records_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ev = EvidencePointer(
                kind="delta_table",
                identifier="catalog.schema.orders",
                delta_version=42,
            )
            r1 = ProofLedgerRecord(
                assistant_reply="First reply",
                evidence=[ev],
                correlation_id="c1",
                user_prompt_sha256=sha256_text("q1"),
                source="test",
                model="llama-test",
                extra={"k": 1},
            )
            r2 = ProofLedgerRecord(
                assistant_reply="Second reply",
                evidence=[ev],
                occurred_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
                source="test",
            )
            append_proof_records(tmp, [r1])
            append_proof_records(tmp, [r2])

            dt = DeltaTable(tmp)
            table = dt.to_pyarrow_table()
            self.assertEqual(table.num_rows, 2)
            cols = set(table.column_names)
            self.assertTrue(
                {
                    "occurred_at",
                    "correlation_id",
                    "user_prompt_sha256",
                    "assistant_reply",
                    "evidence_json",
                    "source",
                    "model",
                    "extra_json",
                }.issubset(cols)
            )

    def test_record_from_chat_response_hashes_prompt(self) -> None:
        ev = EvidencePointer(kind="sql", identifier="SELECT 1")
        r = record_from_chat_response(
            assistant_reply="hi",
            evidence=[ev],
            user_message="secret question",
            source="vercel",
        )
        self.assertEqual(r.user_prompt_sha256, sha256_text("secret question"))
        self.assertEqual(r.source, "vercel")


if __name__ == "__main__":
    unittest.main()
