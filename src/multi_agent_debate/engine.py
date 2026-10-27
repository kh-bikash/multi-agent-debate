from __future__ import annotations

import json
from dataclasses import dataclass

from .llm import LLM


@dataclass(frozen=True)
class DebateResult:
    answer: str
    proposals: dict[str, str]
    critiques: dict[str, str]
    votes: dict[str, str]
    winner: str
    consensus: float
    confidence: float


class Debate:
    def __init__(self, agents: dict[str, LLM], synthesizer: LLM):
        if len(agents) < 2:
            raise ValueError("At least two independent agents required")
        self.agents, self.synthesizer = dict(agents), synthesizer

    def run(self, question: str) -> DebateResult:
        proposals = {name: llm.complete([{"role": "system", "content": "Propose a concise solution and name its main uncertainty."}, {"role": "user", "content": question}]) for name, llm in self.agents.items()}
        critiques: dict[str, str] = {}
        votes: dict[str, str] = {}
        for name, llm in self.agents.items():
            alternatives = {other: proposal for other, proposal in proposals.items() if other != name}
            critiques[name] = llm.complete([{"role": "system", "content": "Critique these alternatives for factual or reasoning gaps. Do not introduce new claims without support."}, {"role": "user", "content": json.dumps(alternatives)}])
        for name, llm in self.agents.items():
            raw_vote = llm.complete([{"role": "system", "content": "Vote for one proposal. Return only its agent name. Candidates: " + ", ".join(sorted(proposals))}, {"role": "user", "content": json.dumps({"proposals": proposals, "critiques": critiques})}]).strip()
            votes[name] = raw_vote if raw_vote in proposals else name
        counts = {name: sum(v == name for v in votes.values()) for name in proposals}
        winner = sorted(counts, key=lambda name: (-counts[name], name))[0]
        consensus = counts[winner] / len(votes)
        answer = self.synthesizer.complete([{"role": "system", "content": "Synthesize the debate. State uncertainties and do not claim consensus beyond the voting record."}, {"role": "user", "content": json.dumps({"question": question, "proposals": proposals, "critiques": critiques, "votes": votes, "winner": winner})}])
        confidence = min(1.0, 0.4 + 0.6 * consensus)
        return DebateResult(answer, proposals, critiques, votes, winner, consensus, confidence)
