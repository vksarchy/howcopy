"""Game state: level ladder, running stats, session commands."""

from dataclasses import dataclass, field

from .grader import Grade
from .scenarios import Scenario, ScenarioDeck

CATEGORY_KEYS = ("radio_procedure", "brevity", "terminology", "clarity")
CATEGORY_LABELS = {
    "radio_procedure": "Radio Procedure",
    "brevity": "Brevity",
    "terminology": "Terminology",
    "clarity": "Clarity & Mission Fit",
}


def level_for(scenario_number: int) -> int:
    """Scenarios 1-3 -> L1, 4-6 -> L2, 7-9 -> L3, 10-12 -> L4, 13+ -> L5."""
    return min(5, (scenario_number - 1) // 3 + 1)


@dataclass
class Session:
    deck: ScenarioDeck = field(default_factory=ScenarioDeck)
    scenario_number: int = 0
    grades: list[Grade] = field(default_factory=list)
    max_level: int = 5

    def next_scenario(self) -> Scenario:
        self.scenario_number += 1
        return self.deck.draw(min(level_for(self.scenario_number), self.max_level))

    def redraw(self) -> Scenario:
        """AUDIBLE: swap current scenario, same level."""
        return self.deck.draw(min(level_for(self.scenario_number), self.max_level))

    def record(self, grade: Grade):
        self.grades.append(grade)

    @property
    def level(self) -> int:
        return min(level_for(max(1, self.scenario_number)), self.max_level)

    def stats(self) -> dict:
        if not self.grades:
            return {}
        n = len(self.grades)
        totals = [g.total for g in self.grades]
        by_cat = {k: sum(getattr(g, k) for g in self.grades) / n for k in CATEGORY_KEYS}
        strongest = max(by_cat, key=by_cat.get)
        weakest = min(by_cat, key=by_cat.get)
        if n < 2:
            trend = "holding steady"
        else:
            half = n // 2
            early = sum(totals[:half]) / half
            late = sum(totals[half:]) / (n - half)
            trend = "climbing" if late > early + 0.5 else \
                    "slipping" if late < early - 0.5 else "holding steady"
        return {
            "graded": n,
            "average": sum(totals) / n,
            "last": totals[-1],
            "best": max(totals),
            "by_category": by_cat,
            "strongest": CATEGORY_LABELS[strongest],
            "weakest": CATEGORY_LABELS[weakest],
            "trend": trend,
        }

    def final_grade(self) -> str:
        s = self.stats()
        if not s:
            return "No transmissions graded. Net closed without traffic."
        avg = s["average"]
        if avg >= 18:
            return "Operator-level comms. You're cleared for the net."
        if avg >= 14:
            return "Solid station. Polish the rough edges and you're there."
        if avg >= 10:
            return "Readable traffic. Drill the skeleton until it's reflex."
        return "Rough net day. Re-read the lexicon and come back — TOC will be here."
