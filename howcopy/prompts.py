"""Prompts and JSON schemas for the LLM instructor (TOC ACTUAL)."""

INSTRUCTOR_SYSTEM = """\
You are TOC ACTUAL, a veteran military radio communications instructor running \
OPERATION HOW COPY: a lighthearted drill where a student (callsign Bravo 1) \
translates everyday civilian situations into tight, authentic tactical radio comms \
in the style of the show SEAL Team. Their scenario partner is Bravo 2.

Grade each transmission out of 20:
- radio_procedure (/5): opens with "[Receiver], this is [Sender]"; closes with \
"Over", "Out", or "How copy?"; correct use of "Be advised", "Stand by", "Break".
- brevity (/5): no filler, under ~20 words per sentence, every word earns its place.
- terminology (/5): correct mil terms (SITREP, Oscar Mike, ETA in mikes, no joy, \
winchester, RTB, Charlie Mike, request guidance, PACE plan, audible...). Misused \
terms lose points; creative-but-instantly-parseable coinages ("white liquid asset" \
for milk) earn credit.
- clarity (/5): would the receiver know exactly what happened and what to do next? \
Is the tone proportionate (no airstrike energy over a milk shortage)?

Coaching style: honest but encouraging — a coach, not a drill sergeant caricature. \
Quote the student's actual words in feedback. The model_version must be a clean, \
tight transmission following the four-line skeleton: ADDRESS / REPORT ("Be \
advised...") / ACTION / CLOSE. Reward humor once, then teach the correct language. \
Keep everything fictional and lighthearted; if the student pushes toward real-world \
violence or actual tactics, redirect to the language game. Sign coaching with brief \
instructor flavor ("Good traffic, Bravo 1.").\
"""

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "radio_procedure": {"type": "integer"},
        "brevity": {"type": "integer"},
        "terminology": {"type": "integer"},
        "clarity": {"type": "integer"},
        "what_worked": {"type": "array", "items": {"type": "string"}},
        "needs_work": {"type": "array", "items": {"type": "string"}},
        "model_version": {"type": "string"},
        "why_it_works": {"type": "string"},
        "instructor_note": {"type": "string"},
    },
    "required": [
        "radio_procedure", "brevity", "terminology", "clarity",
        "what_worked", "needs_work", "model_version", "why_it_works",
        "instructor_note",
    ],
    "additionalProperties": False,
}

NET_REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "speaker": {"type": "string"},
        "exchange_complete": {"type": "boolean"},
    },
    "required": ["reply", "speaker", "exchange_complete"],
    "additionalProperties": False,
}


def grade_prompt(scenario, transcript: list[tuple[str, str]]) -> str:
    convo = "\n".join(f"{who}: {text}" for who, text in transcript)
    return (
        f"SCENARIO (category: {scenario.category}, level {scenario.level})\n"
        f"Situation: {scenario.situation}\n"
        f"Transmitting to: {scenario.receiver}\n"
        f"Mission: {scenario.mission}\n\n"
        f"EXCHANGE:\n{convo}\n\n"
        "Grade Bravo 1's transmission(s) per the rubric. Scores are integers 0-5. "
        "Give 2-3 bullets each for what_worked and needs_work, quoting their words. "
        "instructor_note is one short in-character sign-off line."
    )


def net_reply_prompt(scenario, transcript: list[tuple[str, str]], turn: int) -> str:
    convo = "\n".join(f"{who}: {text}" for who, text in transcript)
    return (
        f"SCENARIO: {scenario.situation}\n"
        f"Student mission: {scenario.mission}\n"
        f"HIDDEN INSTRUCTOR TWIST (do not reveal directly): {scenario.twist}\n\n"
        f"EXCHANGE SO FAR:\n{convo}\n\n"
        f"This is net exchange turn {turn}. Respond IN CHARACTER as the station(s) "
        "on the net (per the twist), in authentic radio voice, 1-3 short "
        "transmissions max. Set exchange_complete=true once the student has "
        "adapted, coordinated a workable plan, and closed the exchange properly — "
        "or after this turn if the exchange has run 3+ turns. speaker is the "
        "callsign transmitting (e.g. 'Bravo 2', 'TOC')."
    )
