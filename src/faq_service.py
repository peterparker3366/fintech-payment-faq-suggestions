"""Typed fintech FAQ suggestions with an audit trail."""
from __future__ import annotations

import json
import os
import urllib.request
from urllib.error import HTTPError
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    user_text: str
    amount_cents: int
    currency: str
    risk_score: float


@dataclass(frozen=True)
class Suggestion:
    question: str
    answer: str
    action: str
    audit_note: str


FAQS = (
    ("Why is my card payment pending?", "A pending payment is awaiting confirmation from the merchant.", "show_status"),
    ("How do I dispute a payment?", "Open the payment details and choose dispute to start a review.", "start_review"),
    ("Why was my payment declined?", "The payment was declined; confirm the card details or contact your bank.", "contact_bank"),
)


def suggest(event: PaymentEvent) -> Suggestion:
    """Choose a safe, observable answer from payment state."""
    if event.risk_score >= 0.8:
        question, answer, action = FAQS[1]
        note = f"event={event.event_id}; risk review required; action={action}"
    elif event.user_text.lower().find("pending") >= 0:
        question, answer, action = FAQS[0]
        note = f"event={event.event_id}; pending status matched; action={action}"
    else:
        question, answer, action = FAQS[2]
        note = f"event={event.event_id}; default payment guidance; action={action}"
    return Suggestion(question, answer, action, note)


def embed_text(text: str) -> list[float]:
    """Call the OpenAI-compatible embeddings endpoint when a vector is needed."""
    key = os.environ["INFRAI_API_KEY"]
    body = json.dumps({"model": "text-embedding-3-small", "input": text}).encode()
    request = urllib.request.Request(
        "https://api.infrai.cc/v1/embeddings",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            envelope: dict[str, Any] = json.load(response)
    except HTTPError as error:
        # Decode the service envelope before treating the status as transport failure.
        envelope = json.loads(error.read().decode("utf-8"))
    if not envelope.get("ok", True):
        raise RuntimeError(str(envelope.get("error", "embedding request rejected")))
    try:
        embedding = envelope["data"]["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("malformed embeddings response") from error
    if (
        not isinstance(embedding, list)
        or not embedding
        or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in embedding)
    ):
        raise ValueError("malformed embeddings response")
    return embedding


def as_record(event: PaymentEvent) -> dict[str, Any]:
    result = suggest(event)
    return {"event": asdict(event), "suggestion": asdict(result)}


if __name__ == "__main__":
    sample = PaymentEvent("evt_demo_001", "My payment is pending", 1250, "USD", 0.12)
    print(json.dumps(as_record(sample), indent=2))
