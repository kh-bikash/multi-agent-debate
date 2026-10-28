# Deployment

## Hosted Vercel application

Connect this Vercel project to the shared Supabase integration for `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` (or `SUPABASE_ANON_KEY`). Configure `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` as server-side Vercel environment variables. Deploy with `vercel deploy --prod`. The hosted app verifies the Supabase user token, uses Secure HttpOnly cookies and same-origin checks, and makes seven model requests per debate for two participants. A free model tier can be exhausted quickly. Set per-user quotas and capacity before unrestricted public use.

Run `scripts/smoke_hosted.py` from a trusted machine with `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `HOSTED_URL` in its process environment. The script creates then deletes its temporary user and checks the live model path.

## Local product

Install with `python -m pip install -e .`, then run the command shown in README. The browser binds to `127.0.0.1:8080` by default. `GET /healthz` is a lightweight health endpoint.

## Container

Copy `.env.example` to `.env`, replace every example secret, and keep that file outside Git. Build and run from this repository:

```bash
docker build -t multi-agent-debate .
docker run --rm -p 127.0.0.1:8080:8080 --env-file .env multi-agent-debate --model actual-model-a --model actual-model-b --synthesizer-model actual-model-c serve --port 8080
```

The image runs as a non-root user. It binds inside the container to `0.0.0.0`; the example publishes only to host loopback. A non-loopback bind requires `AGENT_WEB_TOKEN` of at least 16 characters. The browser asks for that token and sends it to the action endpoint. Put TLS and an authenticated reverse proxy in front of any public deployment.

Replace the model IDs with models available at the configured provider. Set OPENAI_API_KEY. Results are not persisted by this product.

## Release checks

Run `ruff check src tests`, `ruff format --check src tests`, and `pytest -q`. Test the browser action path and `/healthz` after deployment. Keep secrets in the deployment platform, monitor failed actions and model/provider errors, and set backups for any mounted data volume.
