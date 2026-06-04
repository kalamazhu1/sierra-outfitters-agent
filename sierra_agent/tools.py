import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sierra_agent.data import load_orders, load_products


PACIFIC_TIME = ZoneInfo("America/Los_Angeles")
USPS_TRACKING_URL = "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
_GENERATED_CODES = set()


def lookup_order(email: str, order_number: str) -> Dict[str, Any]:
    normalized_email = email.strip().lower()
    normalized_order_number = _normalize_order_number(order_number)

    product_by_sku = {product["SKU"]: product for product in load_products()}
    for order in load_orders():
        if (
            order["Email"].strip().lower() == normalized_email
            and _normalize_order_number(order["OrderNumber"]) == normalized_order_number
        ):
            products = [_format_order_product(sku, product_by_sku) for sku in order["ProductsOrdered"]]
            tracking_number = order["TrackingNumber"]
            tracking_url = (
                USPS_TRACKING_URL.format(tracking_number=tracking_number)
                if tracking_number
                else None
            )
            return {
                "ok": True,
                "customer_name": order["CustomerName"],
                "email": order["Email"],
                "order_number": order["OrderNumber"],
                "status": order["Status"],
                "products_ordered": products,
                "tracking_number": tracking_number,
                "tracking_url": tracking_url,
                "tracking_message": (
                    "Tracking is available."
                    if tracking_number
                    else "Tracking is not available yet for this order."
                ),
            }

    return {
        "ok": False,
        "error": "No order matched that email and order number.",
    }


def search_product_catalog(query: str, max_results: int = 3) -> Dict[str, Any]:
    max_results = max(1, min(int(max_results), 5))
    query_terms = _tokenize(query)

    scored_products = []
    for product in load_products():
        if product["Inventory"] <= 0:
            continue

        searchable_text = " ".join(
            [
                product["ProductName"],
                product["SKU"],
                product["Description"],
                " ".join(product["Tags"]),
            ]
        )
        score = _score_product(query_terms, searchable_text, product["Tags"])
        if score > 0:
            scored_products.append((score, product))

    scored_products.sort(key=lambda item: (-item[0], item[1]["ProductName"]))
    results = [_format_catalog_product(product) for _, product in scored_products[:max_results]]

    return {
        "ok": True,
        "query": query,
        "results": results,
        "message": "Found matching products." if results else "No matching in-stock products found.",
    }


def request_early_risers_promotion(
    email: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    current_time = now.astimezone(PACIFIC_TIME) if now else datetime.now(PACIFIC_TIME)
    eligible = 8 <= current_time.hour < 10

    response = {
        "ok": True,
        "eligible": eligible,
        "discount_percent": 10 if eligible else None,
        "valid_window": "8:00 AM - 10:00 AM Pacific Time",
        "current_pacific_time": current_time.strftime("%Y-%m-%d %I:%M %p %Z"),
        "email": email,
    }

    if eligible:
        response["code"] = _generate_unique_code()
        response["message"] = "Early Risers Promotion code generated."
    else:
        response["code"] = None
        response["message"] = "Early Risers Promotion is not available right now."

    return response


def _normalize_order_number(order_number: str) -> str:
    value = order_number.strip().upper()
    return value if value.startswith("#") else f"#{value}"


def _format_order_product(sku: str, product_by_sku: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    product = product_by_sku.get(sku)
    if not product:
        return {
            "sku": sku,
            "name": None,
            "details_available": False,
        }

    return {
        "sku": sku,
        "name": product["ProductName"],
        "details_available": True,
    }


def _format_catalog_product(product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "product_name": product["ProductName"],
        "sku": product["SKU"],
        "inventory": product["Inventory"],
        "description": product["Description"],
        "tags": product["Tags"],
    }


def _tokenize(text: str) -> List[str]:
    return [token for token in "".join(char.lower() if char.isalnum() else " " for char in text).split() if token]


def _score_product(query_terms: List[str], searchable_text: str, tags: List[str]) -> int:
    normalized_text = searchable_text.lower()
    normalized_tags = {tag.lower() for tag in tags}
    score = 0

    for term in query_terms:
        if term in normalized_text:
            score += 1
        if any(term in tag for tag in normalized_tags):
            score += 2

    return score


def _generate_unique_code() -> str:
    while True:
        code = f"EARLY-{secrets.token_hex(3).upper()}"
        if code not in _GENERATED_CODES:
            _GENERATED_CODES.add(code)
            return code
