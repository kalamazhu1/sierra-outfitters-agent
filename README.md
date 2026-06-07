# Sierra Outfitters Agent

A terminal-based customer support agent for Sierra Outfitters. It uses OpenAI's Responses API with local function tools for order tracking, product recommendations, and the Early Risers Promotion.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and replace the placeholder with your API key:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

The assignment-provided key supports `gpt-4o` and `gpt-4o-mini`. This project defaults to `gpt-4o-mini`. The `.env` file is ignored by git so the key is not committed.

## Run

Terminal chat:

```bash
python main.py
```

Web chat UI:

```bash
python web_app.py
```

Then open `http://127.0.0.1:5001`.

In the terminal chat, type `exit` or `quit` to end the chat.

## Demo Prompts

```text
Where is my order?
```

Then provide:

```text
john.doe@example.com and #W001
```

Other useful prompts:

```text
Can you recommend gear for winter snow?
Can I get the Early Risers Promotion?
What happened to order #W004 for bob.brown@example.com?
```

## Tests

```bash
pytest
```

The tests cover deterministic local behavior: order lookup, tracking links, missing catalog SKUs, catalog search, and promotion eligibility.

## Design Notes

- The agent uses OpenAI for conversation and tool selection, but all business facts come from local JSON files in `data/`.
- The code does not hardcode API keys. It reads `OPENAI_API_KEY` from `.env` or the environment.
- Product recommendation responses are grounded in the catalog search tool.
- Orders can reference SKUs that are not in the product catalog. Those SKUs are returned as unavailable details instead of causing failures.
- Promo code uniqueness is maintained in memory for the running session.
