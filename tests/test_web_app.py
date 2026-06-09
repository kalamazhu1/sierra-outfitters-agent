from web_app import (
    app,
    agents,
    build_artifacts,
    build_display_reply,
    ensure_product_artifacts,
    is_product_recommendation_message,
)


def test_index_renders_chat_shell():
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Trail Support Agent" in response.data
    assert b"Order status" in response.data


def test_chat_rejects_empty_message():
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Please enter a message."


def test_reset_clears_current_session_agent():
    app.config.update(TESTING=True)
    client = app.test_client()

    with client.session_transaction() as session:
        session["session_id"] = "test-session"
    agents["test-session"] = object()

    response = client.post("/api/reset")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert "test-session" not in agents


def test_build_artifacts_returns_product_cards_from_catalog_search():
    products = [
        {
            "product_name": "Crain's Summit Pro X Skis",
            "sku": "SOTN002",
            "inventory": 75,
            "description": "Skis for snow.",
            "tags": ["Skis", "Snow"],
        }
    ]

    artifacts = build_artifacts(
        [
            {
                "name": "search_product_catalog",
                "output": {"ok": True, "results": products},
            }
        ]
    )

    assert artifacts == {"products": products}


def test_build_artifacts_ignores_order_lookup_outputs():
    artifacts = build_artifacts(
        [
            {
                "name": "lookup_order",
                "output": {"ok": True, "status": "delivered"},
            }
        ]
    )

    assert artifacts == {}


def test_build_display_reply_collapses_recommendation_text_when_cards_exist():
    artifacts = {
        "products": [
            {
                "product_name": "Crain's Summit Pro X Skis",
                "sku": "SOTN002",
            }
        ]
    }

    reply = build_display_reply("Long product description from the model.", artifacts)

    assert reply == "Here are the best trail-ready matches I found:"


def test_build_display_reply_keeps_non_product_responses():
    reply = "Your order is still on the trail."

    assert build_display_reply(reply, {}) == reply


def test_recommendation_detection_matches_follow_up_product_requests():
    assert is_product_recommendation_message("how about something lightweight") is True
    assert is_product_recommendation_message("Can you recommend winter gear?") is True


def test_recommendation_detection_ignores_order_and_promo_requests():
    assert is_product_recommendation_message("where is my order?") is False
    assert is_product_recommendation_message("can I get the early risers promotion?") is False


def test_ensure_product_artifacts_falls_back_to_catalog_search():
    artifacts = ensure_product_artifacts("how about something lightweight", {})

    assert artifacts["products"]
    assert artifacts["products"][0]["sku"] == "SOSB006"


def test_ensure_product_artifacts_preserves_existing_products():
    existing = {"products": [{"sku": "SOTN002"}]}

    assert ensure_product_artifacts("Can you recommend winter gear?", existing) == existing
