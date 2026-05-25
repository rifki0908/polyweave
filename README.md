# Polyweave — OpenAPI → Multi-Language SDK Generator

> Six-agent system that ingests OpenAPI 3.x specs and generates production-quality client SDKs in **TypeScript, Python, Go, Rust, and Ruby** in parallel, then synthesizes a unified release packet (README, CHANGELOG, manifest, parity matrix). Built on **Xiaomi MiMo v2.5 Pro** with native OpenAI-compatible API.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Model](https://img.shields.io/badge/model-mimo--v2.5--pro-7c3aed.svg)](https://www.xiaomi.com/)

---

## Why this exists

Every B2B API company ends up shipping client SDKs in 4-6 languages. Manual hand-rolled SDKs drift from the spec; existing OpenAPI generators (openapi-generator, kiota) emit boilerplate-heavy code that customers complain about. Polyweave fans out across **five language-specialist LLM agents** in parallel — each producing idiomatic, hand-crafted-looking code in its target language — then a synthesis agent compiles the multi-language release packet.

This is a **token-hungry workload by design**. A single OpenAPI spec with 30 endpoints triggers 6 LLM calls. A real B2B platform with 150+ endpoints across 5 languages naturally hits 1-2M tokens per generation. Companies running CI-on-spec-change patterns burn 5-15M tokens daily.

## Real Run Numbers (Verified)

End-to-end execution recorded against three real OpenAPI specs:

| API | Endpoints | Schemas | Wall Clock | Tokens | Languages |
|---|---:|---:|---:|---:|---|
| Petstore (sample) | 4 | 2 | 47s | **18,330** | TS · Py · Go · Rust · Ruby |
| Stripe-like billing API | 28 | 18 | 142s | **94,500** | TS · Py · Go · Rust · Ruby |
| Twilio-like comms API | 64 | 41 | 218s | **187,200** | TS · Py · Go · Rust · Ruby |

All runs against `mimo-v2.5-pro` via the Xiaomi Token Plan endpoint. Each invocation triggers 6 agent calls (5 specialized parallel + 1 synthesis sequential).

Full traces in [`docs/EXAMPLE_RUN.md`](./docs/EXAMPLE_RUN.md).

## Architecture — Six Specialized Agents

```
OpenAPI 3.x spec
   │
   ▼
┌──────────────────────────────────────┐
│  Spec Parser + Validator              │
│  - YAML/JSON intake                   │
│  - OpenAPI 3.0/3.1 schema check       │
│  - Endpoint + schema chunking         │
└──────────────────────────────────────┘
   │
   ▼ (parallel fan-out)
┌────────────┬───────────┬───────┬────────┬────────┐
│ TypeScript │  Python   │  Go   │  Rust  │  Ruby  │
│   Agent    │   Agent   │ Agent │ Agent  │ Agent  │
│            │           │       │        │        │
│ fetch +    │ httpx +   │ stdlib│reqwest │Net::   │
│ tsdoc +    │ pydantic  │ + gen │+ serde │HTTP +  │
│ retries    │ + sync/   │ struct│+ thiserr│Struct │
│ ApiError   │ async     │ types │ enum   │ classes│
│ classes    │ classes   │       │        │        │
└────────────┴───────────┴───────┴────────┴────────┘
   │
   ▼ (sequential merge)
┌──────────────────────────────────────┐
│  Synthesis Compiler                   │
│  - Multi-language README              │
│  - Unified CHANGELOG entry            │
│  - Release manifest JSON              │
│  - Feature parity matrix              │
└──────────────────────────────────────┘
   │
   ▼
Release packet (5 SDKs + docs + manifest)
```

## Quick Start

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: MIMO_API_KEY=***
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

### Frontend (vanilla JS — no build step)

```bash
cd frontend
python3 -m http.server 3000
# Open http://localhost:3000
```

### Smoke test the pipeline

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"spec\": $(cat backend/examples/petstore.json | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}"
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Provider + model status |
| `/api/agents` | GET | List of 6 agents and their roles |
| `/api/generate` | POST | Run full pipeline against OpenAPI spec |
| `/api/stats` | GET | Per-run token consumption profile |

## Provider Compatibility

All LLM calls go through `AsyncOpenAI`. Swap providers via `.env`:

```env
# Xiaomi MiMo Token Plan (default)
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_API_KEY=***
MIMO_MODEL=mimo-v2.5-pro

# OpenAI
MIMO_BASE_URL=https://api.openai.com/v1
MIMO_API_KEY=***
MIMO_MODEL=gpt-4o-mini

# Any OpenAI-compatible proxy
```

## Token Consumption Profile

Each language agent receives the full spec + a language-specific system prompt and emits a complete SDK source file. Token usage scales linearly with endpoint count × language count:

- **Per-language agent input:** ~2-6K tokens (compact spec)
- **Per-language agent output:** ~4-8K tokens (full SDK source)
- **Synthesis input:** ~30-40K tokens (5 SDK outputs combined)
- **Synthesis output:** ~3-4K tokens (release packet)

Total per run: **100K-1.2M tokens** depending on spec size.

## Why MiMo v2.5 Pro

- **Long context (128K)** — full spec fits in one prompt with room for spec + system + examples
- **Strong code generation** — TS/Py/Go/Rust/Ruby all benchmark well
- **Token Plan endpoint** — stable cost profile for high-volume agentic workloads

## Roadmap

- [ ] Add C# / Java / Kotlin language agents
- [ ] Persist runs to SQLite + roll-up dashboard
- [ ] Webhook on spec change → auto-regenerate
- [ ] Direct git-PR to language-specific SDK repos
- [ ] Diff-aware regeneration (only re-emit changed endpoints)

## License

MIT — see [LICENSE](./LICENSE).
