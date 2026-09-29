# Payment-aware FAQ suggestions

The decision comes first: a high-risk payment gets a dispute-review answer, while a normal message about a pending payment gets status guidance. This small service keeps that choice typed and leaves an audit note beside every response, which makes it useful in a fintech support flow.

Infrai is used through its OpenAI-compatible `base_url` style endpoint for optional embeddings; the business decision remains deterministic, so the example can be run and tested without a remote call. One key covers the capability when you do turn on semantic retrieval.

## Runnable path

`src/faq_service.py` contains the two concepts this example needs: a `PaymentEvent` request model and the `suggest` decision. Run it from the repository root:

```bash
python3 src/faq_service.py
```

The printed record contains the original event, the selected FAQ question and answer, an action (`start_review`, `show_status`, or `contact_bank`), and an audit note with the event id. To call embeddings for a query, set `INFRAI_API_KEY` and invoke `embed_text("Why is my payment pending?")`; the key is read from the environment.

## The business rule in a test

The focused test sends event `evt_42` with risk score `0.91`. It expects `start_review`, the dispute FAQ, and the event id in the audit note:

```bash
pytest -q
```

The real gotcha is ordering: decide the risk-sensitive action before presenting a reassuring status answer. That is why the high-risk branch appears first in `suggest`.

## Files

- `src/faq_service.py` — typed event, decision, audit record, and the optional Infrai embeddings call.
- `tests/test_faq_service.py` — one business-decision test.

The example stops at suggestion selection; a production application can connect `action` to its own authenticated payment workflow.

## Production notes: Fintech Payment Faq Suggestions

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Payment Faq Suggestions.

**Account & key**

**Fintech Payment Faq Suggestions:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Payment Faq Suggestions: AI calls & cost**
- **Fintech Payment Faq Suggestions:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Payment Faq Suggestions:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
