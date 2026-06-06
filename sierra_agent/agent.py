import json
import os
from typing import Any, Callable, Dict, List

try:
    from openai import AuthenticationError, OpenAI, OpenAIError
except ImportError:  # pragma: no cover - exercised manually before dependencies are installed
    AuthenticationError = None
    OpenAI = None
    OpenAIError = None

from sierra_agent.config import load_env_file
from sierra_agent.tools import (
    lookup_order,
    request_early_risers_promotion,
    search_product_catalog,
)


SYSTEM_PROMPT = """
You are the Sierra Outfitters customer support agent.

Sierra Outfitters is an emerging outdoor retailer. Speak in a helpful, upbeat,
concise voice with light outdoor flavor. Occasional phrases like "onward into
the unknown" are welcome, but do not overdo it.

Use tools whenever a customer asks about order status, tracking, product
recommendations, or the Early Risers Promotion. Never invent order details,
tracking numbers, promo eligibility, or products. If an order lookup needs an
email address or order number, ask for the missing detail before using the tool.
If product results are limited, recommend only from the returned catalog data.
""".strip()


TOOLS = [
    {
        "type": "function",
        "name": "lookup_order",
        "description": "Look up a Sierra Outfitters order by customer email and order number.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The customer's email address.",
                },
                "order_number": {
                    "type": "string",
                    "description": "The order number, such as #W001 or W001.",
                },
            },
            "required": ["email", "order_number"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_product_catalog",
        "description": "Search Sierra Outfitters product catalog for grounded recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The customer's product need or search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of products to return.",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "request_early_risers_promotion",
        "description": "Check eligibility and generate a 10% Early Risers discount code.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": ["string", "null"],
                    "description": "Customer email if provided. Optional.",
                }
            },
            "required": ["email"],
            "additionalProperties": False,
        },
    },
]


class SierraAgent:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        load_env_file()

        if OpenAI is None:
            raise RuntimeError("the OpenAI SDK is not installed. Run `pip install -r requirements.txt`.")

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to a local `.env` file or export it before starting the chat."
            )

        self.client = OpenAI()
        self.model = model
        self.history: List[Dict[str, Any]] = []
        self.tool_handlers: Dict[str, Callable[..., Dict[str, Any]]] = {
            "lookup_order": lookup_order,
            "search_product_catalog": search_product_catalog,
            "request_early_risers_promotion": request_early_risers_promotion,
        }

    def respond(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        response = self._safe_create_response(self.history)

        while self._has_function_call(response):
            self.history.extend(response.output)
            for item in response.output:
                if item.type == "function_call":
                    tool_output = self._execute_tool_call(item)
                    self.history.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(tool_output),
                        }
                    )
            response = self._safe_create_response(self.history)

        final_text = response.output_text.strip()
        self.history.extend(response.output)
        return final_text

    def _safe_create_response(self, input_items: List[Dict[str, Any]]) -> Any:
        try:
            return self._create_response(input_items)
        except Exception as exc:
            if AuthenticationError is not None and isinstance(exc, AuthenticationError):
                raise RuntimeError(
                    "OpenAI rejected the API key. Check that your local `.env` contains a valid "
                    "OPENAI_API_KEY and that your shell is not overriding it with an old value."
                ) from exc
            if OpenAIError is not None and isinstance(exc, OpenAIError):
                raise RuntimeError(f"OpenAI API request failed: {exc}") from exc
            raise

    def _create_response(self, input_items: List[Dict[str, Any]]) -> Any:
        return self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=input_items,
            tools=TOOLS,
        )

    def _execute_tool_call(self, item: Any) -> Dict[str, Any]:
        handler = self.tool_handlers.get(item.name)
        if not handler:
            return {"ok": False, "error": f"Unknown tool: {item.name}"}

        try:
            args = json.loads(item.arguments or "{}")
        except json.JSONDecodeError:
            return {"ok": False, "error": "Tool arguments were not valid JSON."}

        try:
            return handler(**args)
        except TypeError as exc:
            return {"ok": False, "error": f"Invalid tool arguments: {exc}"}

    @staticmethod
    def _has_function_call(response: Any) -> bool:
        return any(item.type == "function_call" for item in response.output)
