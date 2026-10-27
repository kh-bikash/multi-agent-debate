from multi_agent_debate.__main__ import execute


def test_product_runs_configured_models(monkeypatch):
    class FakeLLM:
        def __init__(self, key, base_url, model):
            self.model = model

        def complete(self, messages, *, model=None):
            prompt = messages[0]["content"]
            if prompt.startswith("Vote"):
                return "agent-1-a"
            if prompt.startswith("Synthesize"):
                return "Use a managed database after validating load."
            return "Proposal or critique from " + self.model

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr("multi_agent_debate.__main__.OpenAICompatibleLLM", FakeLLM)
    result = execute(
        "debate", {"question": "Which database?"}, models=["a", "b"], synthesizer="c"
    )
    assert result["winner"] == "agent-1-a"
    assert "managed database" in result["answer"]
