import io
import json

import pytest

from src.faq_service import PaymentEvent, embed_text, suggest


def test_high_risk_payment_routes_to_review_with_audit_note():
    result = suggest(PaymentEvent("evt_42", "please help", 9000, "USD", 0.91))
    assert result.action == "start_review"
    assert result.question == "How do I dispute a payment?"
    assert "evt_42" in result.audit_note


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_embed_text_returns_embedding(monkeypatch):
    envelope = {"ok": True, "data": {"data": [{"embedding": [0.25, -0.5]}]}}
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: FakeResponse(json.dumps(envelope).encode()),
    )

    assert embed_text("pending payment") == [0.25, -0.5]


@pytest.mark.parametrize(
    "envelope",
    [
        {"ok": True},
        {"ok": True, "data": {}},
        {"ok": True, "data": {"data": []}},
        {"ok": True, "data": {"data": [{}]}},
        {"ok": True, "data": {"data": [{"embedding": []}]}},
    ],
)
def test_embed_text_rejects_malformed_success_response(monkeypatch, envelope):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: FakeResponse(json.dumps(envelope).encode()),
    )

    with pytest.raises(ValueError, match="malformed embeddings response"):
        embed_text("pending payment")
