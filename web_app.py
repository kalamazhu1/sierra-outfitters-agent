import os
import uuid

from flask import Flask, jsonify, render_template, request, session

from sierra_agent.agent import SierraAgent


app = Flask(__name__)
app.secret_key = os.getenv("SIERRA_UI_SECRET_KEY", "sierra-outfitters-local-dev")
agents = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "error": "Please enter a message."}), 400

    session_id = session.setdefault("session_id", str(uuid.uuid4()))

    try:
        agent = agents.get(session_id)
        if agent is None:
            agent = SierraAgent()
            agents[session_id] = agent

        reply = agent.respond(message)
        artifacts = build_artifacts(agent.last_tool_outputs)
        return jsonify(
            {
                "ok": True,
                "reply": build_display_reply(reply, artifacts),
                "artifacts": artifacts,
            }
        )
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.post("/api/reset")
def reset():
    session_id = session.get("session_id")
    if session_id:
        agents.pop(session_id, None)
    return jsonify({"ok": True})


def build_artifacts(tool_outputs):
    artifacts = {}

    for tool_call in tool_outputs:
        if tool_call["name"] != "search_product_catalog":
            continue

        output = tool_call["output"]
        results = output.get("results") or []
        if results:
            artifacts["products"] = results

    return artifacts


def build_display_reply(reply, artifacts):
    if artifacts.get("products"):
        return "Here are the best trail-ready matches I found:"

    return reply


if __name__ == "__main__":
    app.run(debug=True, port=5001)
