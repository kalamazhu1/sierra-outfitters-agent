from sierra_agent.agent import SYSTEM_PROMPT


def test_system_prompt_limits_agent_to_sierra_support_scope():
    assert "Stay in scope for Sierra Outfitters customer support" in SYSTEM_PROMPT
    assert "coding help" in SYSTEM_PROMPT
    assert "Do not answer the unrelated request" in SYSTEM_PROMPT
