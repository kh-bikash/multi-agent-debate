from multi_agent_debate.engine import Debate


class Stub:
    def __init__(self, name):
        self.name = name
        self.calls = 0

    def complete(self, messages, *, model=None):
        self.calls += 1
        return "a" if self.calls == 3 else self.name + " says check the evidence"


def test_debate_votes_and_synthesis():
    result = Debate({"a": Stub("a"), "b": Stub("b")}, Stub("synth")).run("What should we do?")
    assert result.winner == "a" and result.consensus == 1
    assert len(result.critiques) == 2 and result.answer
