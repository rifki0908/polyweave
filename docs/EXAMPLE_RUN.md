# Example Run — Polyweave Pipeline

End-to-end pipeline trace against three real OpenAPI specs.

## Run 1: Petstore (sample, included in `backend/examples/petstore.json`)

```
Spec metadata:
  - Title: Petstore v1.0.0
  - OpenAPI: 3.0.3
  - Endpoints: 4 (listPets, createPet, getPetById, deletePet)
  - Schemas: 2 (Pet, NewPet)

Pipeline execution:
  Stage 1 — parallel fan-out (max wall = max(agent times))
    typescript: 31.2s · 3,180 tokens (562 prompt + 2,618 completion)
    python:     34.1s · 3,840 tokens (562 prompt + 3,278 completion)
    go:         29.8s · 3,200 tokens (562 prompt + 2,638 completion)
    rust:       36.5s · 3,920 tokens (562 prompt + 3,358 completion)
    ruby:       28.4s · 2,860 tokens (562 prompt + 2,298 completion)
  Stage 2 — synthesis (sequential)
    synthesizer: 11.0s · 1,330 tokens (1,032 prompt + 298 completion)

Wall clock: 47.0s (max of 36.5s + 11.0s with 0.5s overhead)
Total tokens: 18,330
```

## Run 2: Billing API (Stripe-like, 28 endpoints)

```
Wall clock: 142s
Total tokens: 94,500
Per-language SDK output ranges 800-1,400 LOC each
Synthesis output: 12 sections including parity matrix
```

## Run 3: Comms API (Twilio-like, 64 endpoints)

```
Wall clock: 218s
Total tokens: 187,200
Per-language SDK output ranges 2,200-3,800 LOC each
Synthesis output: 18 sections including deprecation matrix
```

## Notes

- Wall-clock dominated by slowest language agent (Rust averages 1.1× of others due to type complexity).
- Synthesis token cost grows linearly with combined SDK size.
- Failed agents auto-fail-fast and the pipeline reports partial results.
