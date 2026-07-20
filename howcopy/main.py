"""OPERATION HOW COPY — terminal front-end."""

import argparse
import sys

from .engine import CATEGORY_LABELS, Session
from .grader import Grade, pick_backend
from .scenarios import Scenario

# ANSI helpers -----------------------------------------------------------------
USE_COLOR = sys.stdout.isatty()


def c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if USE_COLOR else s


bold = lambda s: c("1", s)
dim = lambda s: c("2", s)
green = lambda s: c("32", s)
yellow = lambda s: c("33", s)
red = lambda s: c("31", s)
cyan = lambda s: c("36", s)
amber = lambda s: c("38;5;214", s)

RULE = dim("─" * 62)

BANNER = r"""
  _  _  _____      __  ___ ___  _____   __ ___
 | || |/ _ \ \    / / / __/ _ \| _ \ \ / /|__ \
 | __ | (_) \ \/\/ / | (_| (_) |  _/\ V /   /_/
 |_||_|\___/ \_/\_/   \___\___/|_|   |_|   (_)
        O P E R A T I O N   H O W   C O P Y
"""

WELCOME = """\
TOC ACTUAL on the net. Drill is simple: I feed you a civilian situation,
you send it back as clean tactical radio traffic. I grade, I coach, next
tasking drops. Difficulty climbs every three scenarios.

Commands:  SITREP  — your running stats
           AUDIBLE — swap the current scenario
           STAND DOWN — end session with final debrief
"""


def score_color(v: int, out_of: int = 5):
    frac = v / out_of
    return green if frac >= 0.8 else yellow if frac >= 0.5 else red


def print_scenario(s: Scenario, number: int, level: int):
    print(RULE)
    print(amber(bold(f"[LEVEL {level} — SCENARIO {number}]")) + dim(f"  ({s.category})"))
    print()
    print(s.situation)
    print()
    print(f"{bold('Transmit to:')} {s.receiver}")
    print(f"{bold('Mission:')} {s.mission}")
    if s.dynamic:
        print(dim("Dynamic traffic: the net will come back at you. Adapt."))
    print()
    print(cyan("Send your transmission, Bravo 1. TOC standing by. Over."))


def print_grade(g: Grade, scenario_name: str):
    print()
    print(RULE)
    print(bold(f"📡 TRANSMISSION REVIEW — {scenario_name}"))
    print()
    total_col = score_color(g.total, 20)
    print(bold("SCORE: ") + total_col(bold(f"{g.total}/20")) + "  " + dim(g.band))
    for key in ("radio_procedure", "brevity", "terminology", "clarity"):
        v = max(0, min(5, int(getattr(g, key))))
        bar = "█" * v + dim("░" * (5 - v))
        print(f"  {CATEGORY_LABELS[key]:<22} {score_color(v)(str(v))}/5  {bar}")
    print()
    print(green(bold("✅ WHAT WORKED")))
    for w in g.what_worked:
        print(f"  • {w}")
    print()
    print(yellow(bold("⚠️  WHAT NEEDS WORK")))
    for w in g.needs_work:
        print(f"  • {w}")
    print()
    print(cyan(bold("🎯 MODEL VERSION")))
    print(f'  "{g.model_version}"')
    print()
    print(bold("📖 WHY IT WORKS"))
    print(f"  {g.why_it_works}")
    if g.instructor_note:
        print()
        print(dim(f"  — TOC: {g.instructor_note}"))
    print(RULE)


def print_sitrep(session: Session):
    s = session.stats()
    print()
    if not s:
        print(dim("TOC: No graded traffic yet, Bravo 1. Nothing to report."))
        return
    print(bold("📊 SITREP"))
    print(f"  Scenarios graded : {s['graded']}   Level: {session.level}")
    print(f"  Average score    : {s['average']:.1f}/20   Last: {s['last']}   Best: {s['best']}")
    print(f"  Strongest        : {s['strongest']}")
    print(f"  Weakest          : {s['weakest']}")
    print(f"  Trend            : {s['trend']}")


def print_summary_block(session: Session):
    s = session.stats()
    print()
    print(amber(bold("═══ PERFORMANCE SUMMARY — LAST BLOCK ═══")))
    print(f"  Average: {s['average']:.1f}/20 ({s['trend']})")
    print(f"  Strongest category: {s['strongest']}")
    print(f"  Weakest category:  {s['weakest']}")
    print(f"  Focus point: drill your {s['weakest']} on the next block.")


def read_transmission(prompt: str = "Bravo 1 > ") -> str:
    try:
        return input(cyan(prompt)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "STAND DOWN"


def run():
    parser = argparse.ArgumentParser(prog="howcopy",
                                     description="Tactical radio comms drill for everyday life")
    parser.add_argument("--backend", choices=["auto", "deepseek", "anthropic", "ollama", "offline"],
                        default=None, help="grading backend (default: auto-detect)")
    args = parser.parse_args()

    backend = pick_backend(args.backend)
    session = Session()
    if not backend.supports_dynamic:
        session.max_level = 3

    print(amber(BANNER))
    print(WELCOME)
    print(dim(f"Grading backend: {backend.name}"
              + ("" if backend.supports_dynamic else " (levels 1-3 only)")))

    scenario = session.next_scenario()
    print_scenario(scenario, session.scenario_number, session.level)

    while True:
        tx = read_transmission()
        if not tx:
            continue
        cmd = tx.upper()

        if cmd == "STAND DOWN":
            print()
            print(amber(bold("═══ FINAL DEBRIEF ═══")))
            print_sitrep(session)
            print()
            print(bold(f"TOC: {session.final_grade()}"))
            print(dim("Net closed. Good hunting, Bravo 1. Out."))
            return
        if cmd == "SITREP":
            print_sitrep(session)
            print()
            print(cyan("Scenario still active. Send your traffic. Over."))
            continue
        if cmd == "AUDIBLE":
            scenario = session.redraw()
            print(dim("TOC: Audible acknowledged. New tasking inbound."))
            print_scenario(scenario, session.scenario_number, session.level)
            continue

        # It's a transmission.
        transcript: list[tuple[str, str]] = [("Bravo 1", tx)]
        try:
            if scenario.dynamic and backend.supports_dynamic:
                turn = 1
                while turn <= 4:
                    nr = backend.net_reply(scenario, transcript, turn)
                    print()
                    print(bold(f"  {nr.speaker}: ") + f'"{nr.reply}"')
                    transcript.append((nr.speaker, nr.reply))
                    if nr.exchange_complete:
                        break
                    reply = read_transmission()
                    if reply.upper() == "STAND DOWN":
                        transcript.append(("Bravo 1", "[left the net]"))
                        break
                    transcript.append(("Bravo 1", reply))
                    turn += 1
            grade = backend.grade(scenario, transcript)
        except Exception as e:
            print(red(f"TOC: Lost comms with the grading net ({e}). Say again or "
                      "restart with --backend offline."))
            continue

        session.record(grade)
        print_grade(grade, scenario.name)

        if session.scenario_number % 5 == 0:
            print_summary_block(session)

        scenario = session.next_scenario()
        print()
        print(dim("TOC: Next tasking inbound."))
        print_scenario(scenario, session.scenario_number, session.level)


if __name__ == "__main__":
    run()
