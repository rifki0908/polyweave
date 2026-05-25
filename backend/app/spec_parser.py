"""Spec validation + endpoint chunking for parallel agent fan-out."""
from __future__ import annotations
from typing import Any
import json

import yaml


SUPPORTED_OPENAPI = ("3.0", "3.1")


def parse_spec(raw: str) -> dict[str, Any]:
    """Parse OpenAPI 3.x spec from JSON or YAML."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty spec")
    if raw[0] in "{[":
        return json.loads(raw)
    return yaml.safe_load(raw)


def validate_spec(spec: dict) -> dict:
    """Lightweight check — enforce OpenAPI 3.0/3.1 + presence of paths/info."""
    version = str(spec.get("openapi", ""))
    if not any(version.startswith(v) for v in SUPPORTED_OPENAPI):
        raise ValueError(
            f"Unsupported OpenAPI version: {version!r} "
            f"(need 3.0.x or 3.1.x)"
        )
    if "paths" not in spec or not isinstance(spec["paths"], dict):
        raise ValueError("Spec missing required 'paths' object")
    if "info" not in spec:
        raise ValueError("Spec missing required 'info' block")
    return {
        "title": spec["info"].get("title", "Untitled API"),
        "version": spec["info"].get("version", "0.0.0"),
        "openapi": version,
        "endpoint_count": _count_endpoints(spec),
        "schema_count": len(spec.get("components", {}).get("schemas", {})),
    }


def _count_endpoints(spec: dict) -> int:
    methods = {"get", "post", "put", "patch", "delete", "head", "options"}
    n = 0
    for path_item in spec.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        n += sum(1 for m in path_item if m.lower() in methods)
    return n


def summarize_for_prompt(spec: dict, max_chars: int = 18_000) -> str:
    """Compact spec for LLM prompt: keep essentials, truncate examples."""
    compact = {
        "openapi": spec.get("openapi"),
        "info": spec.get("info", {}),
        "servers": spec.get("servers", []),
        "paths": {},
        "components": {"schemas": spec.get("components", {}).get("schemas", {})},
    }
    for path, item in spec.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        compact["paths"][path] = {
            method: _strip_op(op)
            for method, op in item.items()
            if isinstance(op, dict)
        }
    text = yaml.safe_dump(compact, sort_keys=False, allow_unicode=True)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n# ... (truncated for prompt budget)"
    return text


def _strip_op(op: dict) -> dict:
    out = {
        "operationId": op.get("operationId"),
        "summary": op.get("summary"),
        "parameters": op.get("parameters", []),
        "requestBody": op.get("requestBody"),
        "responses": {
            code: {"description": resp.get("description")}
            for code, resp in (op.get("responses") or {}).items()
        },
    }
    return {k: v for k, v in out.items() if v}
