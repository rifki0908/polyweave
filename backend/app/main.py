"""FastAPI surface for Polyweave."""
from __future__ import annotations
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agents.orchestrator import run_pipeline
from .agents.prompts import LANG_AGENTS
from .config import settings
from .spec_parser import parse_spec, validate_spec, summarize_for_prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Polyweave",
    description="Multi-agent OpenAPI → multi-language SDK generator powered by MiMo v2.5",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    spec: str = Field(..., description="OpenAPI 3.x spec as YAML or JSON string")


@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "model": settings.mimo_model,
        "base_url": settings.mimo_base_url,
        "agents": list(LANG_AGENTS.keys()) + ["synthesizer"],
    }


@app.get("/api/agents")
async def agents_info() -> dict:
    return {
        "languages": [
            {"id": k, "label": v["label"]} for k, v in LANG_AGENTS.items()
        ],
        "synthesizer": "Aggregates 5 language outputs into release packet (README, CHANGELOG, manifest, parity notes)",
        "execution": "5 language agents run in parallel, then synthesizer runs sequentially",
    }


@app.post("/api/generate")
async def generate(req: GenerateRequest) -> JSONResponse:
    try:
        spec = parse_spec(req.spec)
        meta = validate_spec(spec)
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI spec: {e}") from e

    spec_text = summarize_for_prompt(spec)
    if not settings.mimo_api_key:
        raise HTTPException(
            status_code=500,
            detail="MIMO_API_KEY missing in environment. Set it in backend/.env",
        )

    result = await run_pipeline(spec_text, meta)
    return JSONResponse(result)


@app.get("/api/stats")
async def stats() -> dict:
    """Stub. Real implementation would persist to SQLite + roll-up by run_id."""
    return {
        "note": "Per-run stats are returned inline by /api/generate — see summary block",
        "expected_token_range_per_run": "100k – 1.2M depending on spec size",
        "agent_count": len(LANG_AGENTS) + 1,
    }
