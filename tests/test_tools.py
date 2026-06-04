from datetime import datetime
from zoneinfo import ZoneInfo

from sierra_agent.tools import (
    lookup_order,
    request_early_risers_promotion,
    search_product_catalog,
)


PACIFIC_TIME = ZoneInfo("America/Los_Angeles")


def test_lookup_order_succeeds_with_valid_email_and_order_number():
    result = lookup_order("john.doe@example.com", "W001")

    assert result["ok"] is True
    assert result["status"] == "delivered"
    assert result["tracking_number"] == "TRK123456789"
    assert result["tracking_url"].endswith("TRK123456789")


def test_lookup_order_fails_cleanly_for_unknown_order():
    result = lookup_order("nobody@example.com", "#W999")

    assert result["ok"] is False
    assert "No order matched" in result["error"]


def test_tracking_link_is_included_for_in_transit_order():
    result = lookup_order("jane.smith@example.com", "#W002")

    assert result["status"] == "in-transit"
    assert result["tracking_url"] == (
        "https://tools.usps.com/go/TrackConfirmAction?tLabels=TRK987654321"
    )


def test_tracking_link_is_not_invented_when_tracking_is_missing():
    result = lookup_order("alice.johnson@example.com", "#W003")

    assert result["status"] == "fulfilled"
    assert result["tracking_number"] is None
    assert result["tracking_url"] is None
    assert "not available" in result["tracking_message"]


def test_missing_catalog_skus_do_not_break_order_lookup():
    result = lookup_order("bob.brown@example.com", "#W004")

    missing_products = [
        product for product in result["products_ordered"] if not product["details_available"]
    ]
    assert result["ok"] is True
    assert {product["sku"] for product in missing_products} == {"SOCH010"}


def test_catalog_search_returns_relevant_products():
    result = search_product_catalog("winter snow skis", max_results=3)

    assert result["ok"] is True
    assert result["results"]
    assert result["results"][0]["sku"] == "SOTN002"


def test_promo_code_is_generated_during_valid_window():
    now = datetime(2026, 6, 4, 8, 30, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion("jane.smith@example.com", now=now)

    assert result["eligible"] is True
    assert result["discount_percent"] == 10
    assert result["code"].startswith("EARLY-")


def test_promo_is_denied_outside_valid_window():
    now = datetime(2026, 6, 4, 10, 0, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion(None, now=now)

    assert result["eligible"] is False
    assert result["code"] is None
    assert result["discount_percent"] is None
