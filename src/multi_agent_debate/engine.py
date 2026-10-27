from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
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
    consensus_reached: bool


class Debate:
    def __init__(
        self,
        agents: dict[str, LLM],
        synthesizer: LLM,
        *,
        consensus_threshold: float = 0.67,
        max_workers: int = 4,
    ):
        if len(agents) < 2:
            raise ValueError("At least two independent agents required")
        if not 0.5 <= consensus_threshold <= 1 or max_workers < 1:
            raise ValueError("invalid consensus threshold or worker count")
        self.agents, self.synthesizer = dict(agents), synthesizer
        self.consensus_threshold, self.max_workers = consensus_threshold, max_workers

    def run(self, question: str) -> DebateResult:
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(self.agents))
        ) as pool:
            futures = {
                name: pool.submit(
                    llm.complete,
                    [
                        {
                            "role": "system",
                            "content": "Propose a concise solution and name its main uncertainty.",
                        },
                        {"role": "user", "content": question},
                    ],
                )
                for name, llm in self.agents.items()
            }
            proposals = {name: future.result() for name, future in futures.items()}
        critiques: dict[str, str] = {}
        votes: dict[str, str] = {}
        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(self.agents))
        ) as pool:
            futures = {
                name: pool.submit(
                    llm.complete,
                    [
                        {
                            "role": "system",
                            "content": "Critique these alternatives for factual or reasoning gaps. Do not introduce new claims without support.",
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    other: proposal
                                    for other, proposal in proposals.items()
                                    if other != name
                                }
                            ),
                        },
                    ],
                )
                for name, llm in self.agents.items()
            }
            critiques = {name: future.result() for name, future in futures.items()}
        for name, llm in self.agents.items():
            raw_vote = llm.complete(
                [
                    {
                        "role": "system",
                        "content": "Vote for one proposal. Return only its agent name. Candidates: "
                        + ", ".join(sorted(proposals)),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"proposals": proposals, "critiques": critiques}
                        ),
                    },
                ]
            ).strip()
            votes[name] = raw_vote if raw_vote in proposals else name
        counts = {name: sum(v == name for v in votes.values()) for name in proposals}
        winner = min(counts, key=lambda name: (-counts[name], name))
        consensus = counts[winner] / len(votes)
        consensus_reached = consensus >= self.consensus_threshold
        answer = self.synthesizer.complete(
            [
                {
                    "role": "system",
                    "content": "Synthesize the debate. State uncertainties and do not claim consensus beyond the voting record. If consensus_reached is false, present the competing options.",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": question,
                            "proposals": proposals,
                            "critiques": critiques,
                            "votes": votes,
                            "winner": winner,
                            "consensus_reached": consensus_reached,
                        }
                    ),
                },
            ]
        )
        confidence = (
            min(1.0, 0.25 + 0.75 * consensus)
            if consensus_reached
            else min(0.5, consensus)
        )
        return DebateResult(
            answer,
            proposals,
            critiques,
            votes,
            winner,
            consensus,
            confidence,
            consensus_reached,
        )
