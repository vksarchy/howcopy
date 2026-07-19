# howcopy

Terminal drill game: an LLM drill instructor (TOC ACTUAL) feeds you everyday
civilian situations — dead coffee makers, traffic jams, surprise-party
logistics — and you send them back as tight tactical radio traffic, SEAL Team
style. Every transmission is graded on a 20-point rubric and coached with a
model version.

```
[LEVEL 1 — SCENARIO 1]  (logistics)

You're driving to meet Bravo 2 for lunch. Highway traffic is
stopped dead — accident two miles ahead. You'll be about 15
minutes late.

Transmit to: Bravo 2
Mission: Report the delay and give a new ETA.

Bravo 1 > Bravo 2, this is Bravo 1. Be advised, currently static
on the highway due to an accident. ETA delayed 15 mikes. Over.

📡 TRANSMISSION REVIEW — SCORE: 19/20  Solid copy, operator-level.
```

## Run it

```sh
nix run github:vksarchy/howcopy
```

Or from a clone: `nix run .` — or anywhere with Python:

```sh
pip install . && howcopy
```

## Grading backends

Auto-detected in this order (force with `--backend`):

| Backend | Needs | Notes |
|---|---|---|
| `anthropic` | `ANTHROPIC_API_KEY` (or an `ant auth login` profile) | Full experience: levels 1–5 including dynamic net traffic where TOC and Bravo 2 talk back. Model via `HOWCOPY_MODEL` (default `claude-opus-4-8`). |
| `ollama` | Local Ollama server (`OLLAMA_HOST`, default `localhost:11434`) | Free, local. Model via `HOWCOPY_OLLAMA_MODEL` (default `llama3.1`). |
| `offline` | Nothing | Heuristic pattern grading, levels 1–3 only. |

Legacy `PLAINSPEAK_*` environment variables still work as a deprecated
fallback (with a warning) — the project was renamed from `plainspeak`.

## Gameplay

- **Difficulty ladder** — climbs every 3 scenarios: basic SITREP → report with
  options → multi-phase plans → dynamic back-and-forth traffic → full
  multi-station net discipline with garbled transmissions.
- **Rubric** — Radio Procedure, Brevity, Terminology, Clarity & Mission Fit,
  each /5.
- **Commands**
  - `SITREP` — your running stats
  - `AUDIBLE` — swap the current scenario
  - `STAND DOWN` — end the session with a final debrief
- Performance summary every 5 scenarios.

## Packaging note

The flake overrides nixpkgs' `anthropic` package with `doCheck = false`: its
check phase depends on `inline-snapshot`, which currently has 3 failing tests
in nixpkgs-unstable. Runtime behavior is unaffected; drop the override once
upstream is fixed.

Fictional and lighthearted — a language-style game about daily life, not
tactical instruction.
