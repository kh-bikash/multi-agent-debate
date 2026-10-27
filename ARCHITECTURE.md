# Architecture

## Goal

Collect independent proposals, cross critiques, votes, and a synthesis with explicit consensus and confidence.

## Request path

Question -> independent proposals -> critique of alternatives -> bounded vote -> deterministic winner -> synthesis and reported consensus.

## Components

- `src/multi_agent_debate/engine.py`: policy and state transitions for this project.
- `src/multi_agent_debate/llm.py`: injected model protocol and HTTPS OpenAI-compatible adapter with timeouts and retry for transient transport failures.
- `tests/test_engine.py`: deterministic behavior and failure tests.
- `.github/workflows/ci.yml`: install and test gate.


## State and failure behavior

Model agreement is not independent factual verification. For higher diversity, configure different providers or prompts for each participant, and evaluate factual claims against external evidence.

The LLM adapter times out after 30 seconds and retries transient HTTP failures twice. Model output is untrusted input and is parsed or validated at the project boundary.

## Operations checklist

1. Set secrets through a secret manager and rotate them regularly.
2. Put the service or integrating application behind TLS and authentication.
3. Persist SQLite files on durable storage and back them up; migrate to a managed database for high write volume or multiple replicas.
4. Run `pytest -q` in CI before deployment.
5. Define workload specific evaluation cases, latency objectives, and rollback criteria before serving real users.
