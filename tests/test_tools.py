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
    assert result["status_guidance"]["headline"] == "Delivered to basecamp"
    assert result["tracking_number"] == "TRK123456789"
    assert result["tracking_url"].endswith("TRK123456789")


def test_lookup_order_normalizes_email_order_number_and_whitespace():
    result = lookup_order("  JANE.SMITH@EXAMPLE.COM  ", "  w002  ")

    assert result["ok"] is True
    assert result["order_number"] == "#W002"
    assert result["status"] == "in-transit"


def test_lookup_order_fails_cleanly_for_unknown_order():
    result = lookup_order("nobody@example.com", "#W999")

    assert result["ok"] is False
    assert "No order matched" in result["error"]


def test_lookup_order_rejects_mismatched_email_and_order_number():
    result = lookup_order("john.doe@example.com", "#W002")

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


def test_error_status_order_does_not_create_tracking_link():
    result = lookup_order("fiona.clark@example.com", "#W008")

    assert result["ok"] is True
    assert result["status"] == "error"
    assert result["status_guidance"]["headline"] == "Needs a trail check"
    assert result["tracking_number"] is None
    assert result["tracking_url"] is None


def test_missing_catalog_skus_do_not_break_order_lookup():
    result = lookup_order("bob.brown@example.com", "#W004")

    missing_products = [
        product for product in result["products_ordered"] if not product["details_available"]
    ]
    assert result["ok"] is True
    assert {product["sku"] for product in missing_products} == {"SOCH010"}


def test_order_with_multiple_missing_catalog_skus_returns_all_missing_skus():
    result = lookup_order("george.hill@example.com", "#W009")

    missing_products = [
        product for product in result["products_ordered"] if not product["details_available"]
    ]
    assert result["ok"] is True
    assert {product["sku"] for product in missing_products} == {"SOGK009"}


def test_catalog_search_returns_relevant_products():
    result = search_product_catalog("winter snow skis", max_results=3)

    assert result["ok"] is True
    assert result["results"]
    assert result["results"][0]["sku"] == "SOTN002"


def test_catalog_search_matches_sku_case_insensitively():
    result = search_product_catalog("sosb006", max_results=1)

    assert result["results"][0]["sku"] == "SOSB006"


def test_catalog_search_clamps_result_count_to_five():
    result = search_product_catalog("adventure", max_results=99)

    assert len(result["results"]) <= 5


def test_catalog_search_returns_empty_results_for_no_match():
    result = search_product_catalog("ultralight waterproof tent", max_results=3)

    assert result["ok"] is True
    assert result["results"] == []
    assert result["message"] == "No matching in-stock products found."


def test_promo_code_is_generated_during_valid_window():
    now = datetime(2026, 6, 4, 8, 30, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion("jane.smith@example.com", now=now)

    assert result["eligible"] is True
    assert result["discount_percent"] == 10
    assert result["code"].startswith("EARLY-")


def test_promo_is_available_at_exactly_8am():
    now = datetime(2026, 6, 4, 8, 0, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion(None, now=now)

    assert result["eligible"] is True
    assert result["code"].startswith("EARLY-")


def test_promo_is_available_at_959am():
    now = datetime(2026, 6, 4, 9, 59, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion(None, now=now)

    assert result["eligible"] is True
    assert result["code"].startswith("EARLY-")


def test_promo_is_denied_outside_valid_window():
    now = datetime(2026, 6, 4, 10, 0, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion(None, now=now)

    assert result["eligible"] is False
    assert result["code"] is None
    assert result["discount_percent"] is None


def test_promo_is_denied_before_8am():
    now = datetime(2026, 6, 4, 7, 59, tzinfo=PACIFIC_TIME)
    result = request_early_risers_promotion(None, now=now)

    assert result["eligible"] is False
    assert result["code"] is None


def test_promo_generates_unique_codes_within_session():
    now = datetime(2026, 6, 4, 8, 30, tzinfo=PACIFIC_TIME)

    first = request_early_risers_promotion(None, now=now)
    second = request_early_risers_promotion(None, now=now)

    assert first["code"] != second["code"]
