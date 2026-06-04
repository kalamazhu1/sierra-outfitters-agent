# Sierra Outfitters Agent

A terminal-based customer support agent for Sierra Outfitters. It uses OpenAI's Responses API with local function tools for order tracking, product recommendations, and the Early Risers Promotion.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
```

The assignment-provided key supports `gpt-4o` and `gpt-4o-mini`. This project defaults to `gpt-4o-mini`.

## Run

```bash
python main.py
```

Type `exit` or `quit` to end the chat.

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
- The code does not hardcode API keys. It reads `OPENAI_API_KEY` from the environment.
- Product recommendation responses are grounded in the catalog search tool.
- Orders can reference SKUs that are not in the product catalog. Those SKUs are returned as unavailable details instead of causing failures.
- Promo code uniqueness is maintained in memory for the running session.
