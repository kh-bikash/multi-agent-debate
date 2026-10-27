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
3. Deliberation state lives for one invocation. Persist proposals, critiques, and votes in the host application when an audit trail is required.
4. Run `pytest -q` in CI before deployment.
5. Define workload specific evaluation cases, latency objectives, and rollback criteria before serving real users.

## Deliberation stages

The orchestrator requires at least two agents. It runs proposals concurrently, then critiques concurrently with each critic seeing the other proposals. Once all critiques are available, every agent votes for one registered name; malformed votes fall back to self votes. The winner is chosen by count with a deterministic name tie break. `consensus_threshold` controls whether the result claims agreement.

The synthesizer receives the question, proposals, critiques, votes, winner, and consensus flag. Its output is accompanied by a numeric confidence derived from vote share, and split votes are capped at low confidence. Vote share measures agreement only. It does not prove factual accuracy, so attach an independent evidence check for high stakes decisions.

## Product interfaces and trust boundary

The installed console command and local browser call the same product operation in `src/*/__main__.py`; the browser does not replace the engine's validation or state transitions. `src/*/web.py` serves HTML and a JSON action endpoint with a one-megabyte request limit and a per-process CSRF token. It binds to loopback by default. A non-loopback bind requires `AGENT_WEB_TOKEN` of at least 16 characters, checked on every action request. The page never embeds the access token; an operator enters it in the browser. Treat the browser as an operator interface and place TLS plus identity-aware access control in front of any public endpoint. The non-root container is described in `DEPLOYMENT.md`.
