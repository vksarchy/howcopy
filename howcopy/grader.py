"""Grading backends: Anthropic API (default), Ollama (local), offline heuristic."""

import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field

from . import prompts

def _env(name: str, default: str) -> str:
    """Read HOWCOPY_* env var; fall back to the deprecated PLAINSPEAK_* name."""
    value = os.environ.get(f"HOWCOPY_{name}")
    if value is not None:
        return value
    legacy = os.environ.get(f"PLAINSPEAK_{name}")
    if legacy is not None:
        print(f"warning: PLAINSPEAK_{name} is deprecated, use HOWCOPY_{name}",
              file=sys.stderr)
        return legacy
    return default


DEFAULT_MODEL = _env("MODEL", "claude-opus-4-8")
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "llama3.1")
DEEPSEEK_MODEL = _env("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.environ.get("HOWCOPY_DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")


def _deepseek_api_key() -> str:
    """Resolve the DeepSeek key without ever requiring it live in the repo.

    Checked in order: HOWCOPY_DEEPSEEK_API_KEY (raw value), then
    HOWCOPY_DEEPSEEK_API_KEY_FILE (path to a secret file — e.g. an
    agenix-decrypted /run/agenix/<name>), then bare DEEPSEEK_API_KEY.
    """
    key = os.environ.get("HOWCOPY_DEEPSEEK_API_KEY")
    if key:
        return key
    key_file = os.environ.get("HOWCOPY_DEEPSEEK_API_KEY_FILE")
    if key_file:
        with open(key_file) as f:
            return f.read().strip()
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    raise RuntimeError(
        "No DeepSeek key found. Set HOWCOPY_DEEPSEEK_API_KEY, or "
        "HOWCOPY_DEEPSEEK_API_KEY_FILE pointing at a decrypted secret file "
        "(agenix and friends), or DEEPSEEK_API_KEY."
    )


@dataclass
class Grade:
    radio_procedure: int
    brevity: int
    terminology: int
    clarity: int
    what_worked: list[str]
    needs_work: list[str]
    model_version: str
    why_it_works: str
    instructor_note: str = ""

    @property
    def total(self) -> int:
        clamp = lambda v: max(0, min(5, int(v)))
        return (clamp(self.radio_procedure) + clamp(self.brevity)
                + clamp(self.terminology) + clamp(self.clarity))

    @property
    def band(self) -> str:
        t = self.total
        if t >= 18:
            return "Solid copy, operator-level."
        if t >= 14:
            return "Good traffic, minor discipline issues."
        if t >= 10:
            return "Readable but sloppy — tighten up."
        return "Say again your last, that transmission needs work."


@dataclass
class NetReply:
    reply: str
    speaker: str
    exchange_complete: bool


class Backend:
    name = "base"
    supports_dynamic = False

    def grade(self, scenario, transcript) -> Grade:
        raise NotImplementedError

    def net_reply(self, scenario, transcript, turn) -> NetReply:
        raise NotImplementedError


class AnthropicBackend(Backend):
    name = "anthropic"
    supports_dynamic = True

    def __init__(self, model: str = DEFAULT_MODEL):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def _json_call(self, prompt: str, schema: dict) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": prompts.INSTRUCTOR_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }],
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError("Instructor declined that transmission. Keep it in the game, Bravo 1.")
        text = next(b.text for b in resp.content if b.type == "text")
        return json.loads(text)

    def grade(self, scenario, transcript) -> Grade:
        data = self._json_call(prompts.grade_prompt(scenario, transcript), prompts.GRADE_SCHEMA)
        return Grade(**data)

    def net_reply(self, scenario, transcript, turn) -> NetReply:
        data = self._json_call(prompts.net_reply_prompt(scenario, transcript, turn),
                               prompts.NET_REPLY_SCHEMA)
        return NetReply(**data)


class DeepSeekBackend(Backend):
    """DeepSeek V4, via its Anthropic-API-compatible endpoint.

    Uses forced tool-use (not output_config json_schema) for structured
    output: DeepSeek's compat layer documents json_schema support as
    partial, but tool_choice-forced tool calls are fully supported.
    """
    name = "deepseek"
    supports_dynamic = True

    def __init__(self, model: str = DEEPSEEK_MODEL):
        import anthropic
        self.client = anthropic.Anthropic(api_key=_deepseek_api_key(), base_url=DEEPSEEK_BASE_URL)
        self.model = model

    def _tool_call(self, prompt: str, schema: dict, attempts: int = 3) -> dict:
        last_empty = False
        for _ in range(attempts):
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                # deepseek-v4-pro defaults to thinking mode, which rejects a
                # forced tool_choice ("Thinking mode does not support this
                # tool_choice"). Structured output here doesn't need reasoning.
                thinking={"type": "disabled"},
                system=prompts.INSTRUCTOR_SYSTEM,
                tools=[{
                    "name": "submit_result",
                    "description": "Submit the structured result for this turn.",
                    "input_schema": schema,
                }],
                tool_choice={"type": "tool", "name": "submit_result"},
                messages=[{"role": "user", "content": prompt}],
            )
            block = next((b for b in resp.content if b.type == "tool_use"), None)
            if block is None:
                raise RuntimeError("DeepSeek didn't return structured output. Say again.")
            # DeepSeek's tool-call arguments occasionally arrive empty even
            # on stop_reason="tool_use" (observed ~40% on deepseek-v4-pro,
            # not reproduced on deepseek-v4-flash). Retry rather than crash.
            if block.input:
                return block.input
            last_empty = True
        raise RuntimeError("DeepSeek returned empty tool arguments repeatedly. Say again."
                           if last_empty else "DeepSeek didn't return structured output.")

    def grade(self, scenario, transcript) -> Grade:
        data = self._tool_call(prompts.grade_prompt(scenario, transcript), prompts.GRADE_SCHEMA)
        data = {k: data.get(k) for k in prompts.GRADE_SCHEMA["required"]}
        return Grade(**data)

    def net_reply(self, scenario, transcript, turn) -> NetReply:
        data = self._tool_call(prompts.net_reply_prompt(scenario, transcript, turn),
                               prompts.NET_REPLY_SCHEMA)
        complete = data.get("exchange_complete")
        return NetReply(
            reply=data["reply"],
            speaker=data.get("speaker", "Bravo 2"),
            exchange_complete=complete is True or str(complete).lower() == "true",
        )


class OllamaBackend(Backend):
    name = "ollama"
    supports_dynamic = True

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = self._resolve_model(model)

    @staticmethod
    def _resolve_model(wanted: str) -> str:
        """Use the requested model if pulled; otherwise fall back to whatever is."""
        try:
            with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
                installed = [m["name"] for m in json.load(r)["models"]]
        except Exception:
            return wanted  # server will report its own error later
        if not installed:
            raise RuntimeError(
                "Ollama is running but has no models. Pull one first: ollama pull llama3.1")
        for name in installed:
            if name == wanted or name.split(":")[0] == wanted.split(":")[0]:
                return name
        fallback = installed[0]
        print(f"warning: Ollama model '{wanted}' not installed; using '{fallback}'. "
              f"Override with HOWCOPY_OLLAMA_MODEL.", file=sys.stderr)
        return fallback

    def _json_call(self, prompt: str, schema: dict) -> dict:
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": prompts.INSTRUCTOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        return json.loads(data["message"]["content"])

    def grade(self, scenario, transcript) -> Grade:
        data = self._json_call(prompts.grade_prompt(scenario, transcript), prompts.GRADE_SCHEMA)
        data = {k: data.get(k) for k in prompts.GRADE_SCHEMA["required"]}
        return Grade(**data)

    def net_reply(self, scenario, transcript, turn) -> NetReply:
        data = self._json_call(prompts.net_reply_prompt(scenario, transcript, turn),
                               prompts.NET_REPLY_SCHEMA)
        complete = data.get("exchange_complete")
        return NetReply(
            reply=data["reply"],
            speaker=data.get("speaker", "Bravo 2"),
            exchange_complete=complete is True or str(complete).lower() == "true",
        )


PROWORD_OPEN = re.compile(r"^\s*(bravo\s*\d|toc|all\s+stations|team)[,.]?\s+this\s+is\s+", re.I)
PROWORD_CLOSE = re.compile(r"\b(over|out|how copy)\W*$", re.I)
LEXICON = [
    "be advised", "sitrep", "oscar mike", "mikes", "rtb", "no joy", "winchester",
    "bingo", "static", "charlie mike", "request guidance", "request permission",
    "stand by", "roger", "wilco", "negative", "affirmative", "audible", "rally point",
    "eta", "eyes on", "good copy", "solid copy", "say again", "break", "lima charlie",
    "pace", "exfil", "infil", "time hack", "de-conflict", "wheels up",
]


class HeuristicBackend(Backend):
    """Offline fallback: regex scoring, canned coaching. Levels 1-3 only."""
    name = "offline"
    supports_dynamic = False

    def grade(self, scenario, transcript) -> Grade:
        text = " ".join(t for who, t in transcript if who == "Bravo 1")
        low = text.lower()

        proc = 1
        if PROWORD_OPEN.search(text):
            proc += 2
        if PROWORD_CLOSE.search(text.strip()):
            proc += 1
        if "be advised" in low or "stand by" in low:
            proc += 1

        words = len(text.split())
        sentences = max(1, len(re.findall(r"[.?!]+", text)))
        avg = words / sentences
        brev = 5 if avg <= 14 else 4 if avg <= 20 else 3 if avg <= 28 else 2 if avg <= 40 else 1
        fillers = sum(low.count(w) for w in (" just ", " really ", " like ", " maybe ", " um "))
        brev = max(0, brev - fillers)

        hits = [t for t in LEXICON if t in low]
        term = min(5, 1 + len(hits))

        clar = 3
        if any(k in low for k in ("eta", "mikes", "minutes")):
            clar += 1
        if "?" in text or "request" in low or "advise" in low:
            clar += 1

        worked, fix = [], []
        worked.append(f"Terminology on the net: {', '.join(hits[:3])}." if hits
                      else "You got a transmission out — that's the job.")
        if PROWORD_OPEN.search(text):
            worked.append("Correct address format — receiver first, then sender.")
        else:
            fix.append('Open with "[Receiver], this is Bravo 1." Address before message, always.')
        if not PROWORD_CLOSE.search(text.strip()):
            fix.append('Close the transmission: "Over" (reply expected) or "Out" (done).')
        if fillers:
            fix.append("Filler words detected. Every word earns its place.")
        if not fix:
            fix.append("Tighten sentences under 20 words; front-load the critical fact.")

        return Grade(
            radio_procedure=min(5, proc), brevity=brev, terminology=term,
            clarity=min(5, clar), what_worked=worked, needs_work=fix,
            model_version=(f"{scenario.receiver.title()}, this is Bravo 1. Be advised, "
                           "[situation in mil terms]. [Plan or request]. How copy? Over."),
            why_it_works="Four-line skeleton: address, report, action, close. The receiver "
                         "hears who, what, and what's needed — nothing else.",
            instructor_note="Offline mode: pattern-check only. Hook up an API key or Ollama "
                            "for full grading, Bravo 1.",
        )


def pick_backend(forced: str | None = None) -> Backend:
    choice = (forced or _env("BACKEND", "auto")).lower()
    if choice == "offline":
        return HeuristicBackend()
    if choice == "ollama":
        return OllamaBackend()
    if choice == "anthropic":
        return AnthropicBackend()
    if choice == "deepseek":
        return DeepSeekBackend()
    # auto-detect: DeepSeek creds -> Anthropic creds -> Ollama server -> offline
    try:
        return DeepSeekBackend()
    except Exception:
        pass
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") \
            or os.path.isdir(os.path.expanduser("~/.config/anthropic")):
        try:
            return AnthropicBackend()
        except Exception:
            pass
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
        return OllamaBackend()
    except Exception:
        return HeuristicBackend()
