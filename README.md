# Sierra Outfitters Agent

A terminal-based customer support agent for Sierra Outfitters. It uses OpenAI's Responses API with local function tools for order tracking, product recommendations, and the Early Risers Promotion.

## Setup

Fast path:

```bash
make install
```

Manual setup:

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
make chat
```

Web chat UI:

```bash
make web
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
make test
```

The tests cover deterministic local behavior: order lookup, tracking links, missing catalog SKUs, catalog search, and promotion eligibility.

## Design Notes

- The agent uses OpenAI for conversation and tool selection, but all business facts come from local JSON files in `data/`.
- The code does not hardcode API keys. It reads `OPENAI_API_KEY` from `.env` or the environment.
- Product recommendation responses are grounded in the catalog search tool.
- Orders can reference SKUs that are not in the product catalog. Those SKUs are returned as unavailable details instead of causing failures.
- Promo code uniqueness is maintained in memory for the running session.

## Agent
Flow:
User asks something
        ↓
LLM reads prompt + conversation + tool schemas
        ↓
LLM decides:
  - answer directly, OR
  - ask for missing info, OR
  - call a tool
        ↓
If tool call, API returns structured function_call item

## Tools
Order Lookup:

Normalize inputs (email, order #)
build product lookup: sku to product
loop through orders
build response and return structured data

at scale we'd move the orders into a db so we wouldn't need to loop through orders

Product Recommendations:

Tool tokenizes inputs
Tool searches the catalog
Sorts and returns results

at scale build an inverted index. 
also vector index for fuzzy matching

Promos:
Tool checks time and sees if it's within 8am - 10am
generates a random code and stores it in a set to guarantee uniqueness

At scale store in a db to guarantee uniqueness. Can also validate things like one use per user or expired promos etc.
