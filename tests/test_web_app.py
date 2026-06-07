from web_app import app, agents


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
