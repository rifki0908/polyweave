"""Five language-agent prompts + one synthesis-agent prompt.

Each language agent generates a full SDK in its target language.
The synthesizer rolls per-language docs + a release manifest.

Why each agent is large: full client class, model classes per schema,
auth handling, retry logic, error types, tests. Real APIs with 30+
endpoints emit 2-5K LOC per language.
"""
from __future__ import annotations

LANG_AGENTS = {
    "typescript": {
        "label": "TypeScript SDK",
        "system": (
            "You are a senior TypeScript SDK author. Generate a production-quality "
            "TypeScript client for the given OpenAPI 3.x spec. Requirements:\n"
            "- Single-file output, plain TypeScript (no bundler-specific syntax).\n"
            "- Use native fetch + AbortController for cancellation.\n"
            "- Generate strict TypeScript types/interfaces from components.schemas.\n"
            "- Generate one method per operationId on a single Client class.\n"
            "- Include retry-with-exponential-backoff for 429 and 5xx (configurable).\n"
            "- Include typed error classes (ApiError, ValidationError, NetworkError).\n"
            "- Include JSDoc on each method pulled from summary/description.\n"
            "- Provide a usage example at the bottom in a /* USAGE */ comment block.\n"
            "Output ONLY the .ts source code in a single fenced block."
        ),
    },
    "python": {
        "label": "Python SDK",
        "system": (
            "You are a senior Python SDK author. Generate a production-quality Python "
            "package layout for the given OpenAPI 3.x spec. Requirements:\n"
            "- Use httpx for sync + async clients (Client and AsyncClient).\n"
            "- Use Pydantic v2 BaseModel for every component schema.\n"
            "- Type-hint every parameter and return value.\n"
            "- Include retry-with-exponential-backoff for 429 and 5xx via tenacity-style "
            "  built-in helper (no external dep beyond httpx + pydantic).\n"
            "- Include typed exception hierarchy (ApiError, ValidationError, NetworkError, "
            "  AuthError).\n"
            "- Generate one method per operationId on Client and AsyncClient.\n"
            "- Provide docstrings pulled from summary/description.\n"
            "Output the full module as one .py file in a single fenced block."
        ),
    },
    "go": {
        "label": "Go SDK",
        "system": (
            "You are a senior Go SDK author. Generate idiomatic Go for the given OpenAPI "
            "3.x spec. Requirements:\n"
            "- Single package, no external deps (stdlib only: net/http, encoding/json, "
            "  context, time, errors).\n"
            "- Define struct types for every component schema with json tags.\n"
            "- One method per operationId on Client struct, accepting context.Context.\n"
            "- Implement retry-with-backoff via a configurable RoundTripper.\n"
            "- Define typed errors (ApiError struct implementing error).\n"
            "- Include doc comments on every exported symbol.\n"
            "- End with a //go:build example block showing usage.\n"
            "Output the .go source in a single fenced block."
        ),
    },
    "rust": {
        "label": "Rust SDK",
        "system": (
            "You are a senior Rust SDK author. Generate a Rust crate skeleton for the "
            "given OpenAPI 3.x spec. Requirements:\n"
            "- Use reqwest (async, default features) + serde + serde_json + thiserror.\n"
            "- Generate strongly-typed structs with serde derives for every schema.\n"
            "- One async method per operationId on a Client struct.\n"
            "- Implement retry-with-backoff for 429 and 5xx via internal helper.\n"
            "- Define a thiserror-based Error enum (ApiError, ValidationError, "
            "  NetworkError, AuthError).\n"
            "- Include rustdoc on every public item, pulled from summary/description.\n"
            "- Append a #[cfg(test)] usage example.\n"
            "Output the lib.rs source in a single fenced block."
        ),
    },
    "ruby": {
        "label": "Ruby SDK",
        "system": (
            "You are a senior Ruby SDK author. Generate a single-file Ruby gem source "
            "for the given OpenAPI 3.x spec. Requirements:\n"
            "- Use Net::HTTP (stdlib) — zero external runtime deps.\n"
            "- Define Struct or Data classes for every component schema.\n"
            "- One instance method per operationId on a Client class.\n"
            "- Include retry-with-backoff for 429 and 5xx via a private helper.\n"
            "- Define a typed exception hierarchy (ApiError, ValidationError, "
            "  NetworkError, AuthError) inheriting from StandardError.\n"
            "- Include YARD-style comments on each method.\n"
            "- End with a `# Usage` comment block.\n"
            "Output the .rb source in a single fenced block."
        ),
    },
}


SYNTHESIZER_SYSTEM = (
    "You are a senior release engineer producing a multi-language SDK release packet.\n"
    "Inputs: per-language SDK source code generated by five language-specialist agents.\n"
    "Tasks:\n"
    "1. For each language, list installation, auth setup, and one minimal usage example.\n"
    "2. Generate a unified CHANGELOG.md entry for this release.\n"
    "3. Generate a release manifest JSON with file paths, language versions, and SDK "
    "   feature parity matrix.\n"
    "4. Flag any feature that is implemented in some languages but missing in others.\n"
    "Output sections in this exact order:\n"
    "## README\n## CHANGELOG\n## MANIFEST (json codeblock)\n## PARITY_NOTES\n"
)


def build_user_prompt(spec_text: str, lang: str) -> str:
    return (
        f"Generate the {LANG_AGENTS[lang]['label']} for this OpenAPI 3.x spec.\n\n"
        f"Spec follows this fence:\n```yaml\n{spec_text}\n```\n\n"
        "Be exhaustive. Do not skip operations. Output only the source file."
    )


def build_synthesis_prompt(per_lang_outputs: dict[str, str], spec_meta: dict) -> str:
    parts = [
        f"API: {spec_meta['title']} v{spec_meta['version']}",
        f"Endpoints: {spec_meta['endpoint_count']}",
        f"Schemas: {spec_meta['schema_count']}",
        "",
        "Per-language SDK outputs follow. Build the release packet from these.",
        "",
    ]
    for lang, out in per_lang_outputs.items():
        excerpt = out[:6000] + ("\n... (truncated)" if len(out) > 6000 else "")
        parts.append(f"### {lang.upper()}\n```\n{excerpt}\n```\n")
    return "\n".join(parts)
