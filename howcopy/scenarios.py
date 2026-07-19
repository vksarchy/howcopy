"""Scenario bank. Engine picks by level, rotating categories."""

from dataclasses import dataclass, field
import random

CATEGORIES = [
    "logistics",
    "domestic",
    "social",
    "workplace",
    "health",
    "contingency",
]


@dataclass
class Scenario:
    category: str
    level: int  # minimum level band (1, 2, 3, 4, 5)
    receiver: str  # who the student transmits to
    situation: str  # plain-language setup shown to the student
    mission: str  # what the transmission must accomplish
    dynamic: bool = False  # levels 4-5: instructor plays the net mid-exchange
    twist: str = ""  # hidden instruction for the instructor when dynamic
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = self.situation.split(".")[0][:48]


BANK: list[Scenario] = [
    # ---- Level 1: basic SITREP (one fact + one request) ----
    Scenario("logistics", 1, "Bravo 2",
             "You're driving to meet Bravo 2 for lunch. Highway traffic is stopped dead — "
             "accident two miles ahead. You'll be about 15 minutes late.",
             "Report the delay and give a new ETA."),
    Scenario("domestic", 1, "Bravo 2",
             "You went to make coffee. The coffee maker is dead — no lights, no response. "
             "There is instant coffee in the pantry as a backup.",
             "Report the equipment failure and state your backup plan."),
    Scenario("workplace", 1, "Bravo 2",
             "You overslept. The 9:00 team meeting starts in 10 minutes and you're still at home. "
             "You can join by phone from the car.",
             "Report your status and how you'll make the meeting."),
    Scenario("health", 1, "Bravo 2",
             "You're at the gym. You tweaked your lower back on the second set. Nothing serious, "
             "but you're cutting the workout short and heading home.",
             "Report the minor injury and your intention to return to base."),
    Scenario("social", 1, "Bravo 2",
             "Your neighbor's dog has been barking non-stop for two hours. You're going next door "
             "to talk to the neighbor about it.",
             "Report the situation and your intended action."),
    Scenario("contingency", 1, "Bravo 2",
             "Your phone battery is at 4 percent and you forgot your charger. You're about to go "
             "dark for the rest of the afternoon until you get home around 1800.",
             "Warn of imminent comms loss and give the time you'll be reachable again."),
    # ---- Level 2: report + request guidance between two options ----
    Scenario("logistics", 2, "Bravo 2",
             "You're at the grocery store for taco night supplies. They are completely out of "
             "ground beef. Options: ground turkey, or drive 10 minutes to the other store.",
             "Report the shortage and request guidance between the two options."),
    Scenario("social", 2, "Bravo 2",
             "You and Bravo 2 are invited to two parties on the same Saturday night: your cousin's "
             "birthday (family obligation, likely boring) and a friend's rooftop party (fun, but "
             "your cousin will notice the absence).",
             "Lay out both options with the key risk of each and request a decision."),
    Scenario("workplace", 2, "TOC",
             "Your laptop blue-screened an hour before a client presentation. IT says a fix takes "
             "two hours. Options: present from your phone, or borrow a coworker's laptop that "
             "doesn't have your slides synced yet.",
             "Report the tech failure and request guidance between the two courses of action."),
    Scenario("health", 2, "Bravo 2",
             "You woke up with a sore throat and a mild fever. You had plans to help Bravo 2 move "
             "furniture today. Options: push through and show up, or stay home and reschedule to "
             "Sunday.",
             "Report your condition and request a decision, noting the contamination risk."),
    Scenario("domestic", 2, "Bravo 2",
             "The washing machine stopped mid-cycle, full of water and soaked clothes. Options: "
             "call the repair service (arrives tomorrow), or watch a video and try to drain it "
             "yourself tonight.",
             "Report the failure and request guidance between repair service and self-help."),
    Scenario("contingency", 2, "Bravo 2",
             "You're locked out of the apartment. Keys are inside. Options: wait 90 minutes for "
             "Bravo 2 to come home with their key, or pay a locksmith about 120 dollars for entry "
             "in 20 minutes.",
             "Report the lockout and request a decision — time versus money."),
    # ---- Level 3: SITREP + multi-phase plan (primary and alternate) ----
    Scenario("logistics", 3, "the whole team",
             "You're coordinating the Saturday cookout. Weather says 60 percent rain from 1400. "
             "Primary plan: park pavilion at 1200, grill before the rain. Alternate: move "
             "everything to your garage, start 1300, rain or shine.",
             "Report the weather threat, brief primary and alternate plans with timings, and "
             "request confirmation."),
    Scenario("workplace", 3, "TOC",
             "The quarterly report is due at 1700. Your data source crashed and support says it's "
             "back in 2 hours. Primary: wait, then sprint the analysis for an on-time delivery. "
             "Alternate: build the report now from last week's cached data, flag it as "
             "provisional, and update Monday.",
             "Report the outage, brief both plans with the deadline math, recommend one, and "
             "request approval."),
    Scenario("domestic", 3, "Bravo 2",
             "Dinner guests arrive at 1900. It's 1750 and the oven just died with a raw lasagna "
             "inside. Primary: air fryer in batches, dinner slips to 1945. Alternate: pizza "
             "delivery ordered now, lasagna becomes tomorrow's lunch.",
             "Report the equipment casualty, brief primary and alternate with new timelines, and "
             "request a decision before guests arrive."),
    Scenario("contingency", 3, "the whole team",
             "Airport run tomorrow: flight at 0700, meaning wheels up from the house at 0430. "
             "Forecast shows possible ice. Primary: standard route, 45 minutes. Alternate: "
             "highway route, 60 minutes but treated roads. Decision point is 0400 based on "
             "the road report.",
             "Brief the movement plan: timings, both routes, and the 0400 decision criteria. "
             "Request acknowledgment from all stations."),
    # ---- Level 4: dynamic traffic (instructor plays the net) ----
    Scenario("logistics", 4, "Bravo 2",
             "You're picking up the birthday cake for tonight's party. The bakery says the order "
             "was never received. They can do a plain sheet cake in 30 minutes.",
             "Report the problem and your proposed fix; be ready to adapt to new information "
             "from Bravo 2.",
             dynamic=True,
             twist="After the first transmission, respond as Bravo 2: the party moved up one "
                   "hour, so 30 minutes is too long. There is a second bakery across town. "
                   "Force the student to re-plan and confirm timings."),
    Scenario("workplace", 4, "TOC",
             "Big demo in 20 minutes. The staging server just went down. You can restart it "
             "(10 minutes, might not work) or run the demo from your laptop (works, but no "
             "client data loaded).",
             "Report and propose a course of action; TOC will come back with complications.",
             dynamic=True,
             twist="Respond as TOC: the client just arrived early and is in the room in 10 "
                   "minutes. Restart window is gone. Push the student to commit to the laptop "
                   "demo and brief a talking-point workaround for the missing data."),
    Scenario("contingency", 4, "Bravo 2",
             "Road trip. Low-fuel light just came on in the middle of nowhere. GPS shows one "
             "gas station in 12 miles, but a sign you passed said it might be closed Sundays. "
             "It is Sunday. Range remaining: roughly 30 miles.",
             "Report fuel state and your plan; adapt as Bravo 2 feeds you map intel.",
             dynamic=True,
             twist="Respond as Bravo 2: checking the map — that station shows permanently "
                   "closed. Next one is 26 miles, at the edge of their range. Make the student "
                   "brief a fuel-conservation plan and a bingo decision point."),
    # ---- Level 5: full net discipline, multi-party ----
    Scenario("social", 5, "the whole team",
             "Surprise party op for Bravo 3's spouse. You're coordinating: Bravo 2 has the cake, "
             "Bravo 4 is decoy-driving the target around town. Target's ETA to the house must "
             "stay above 30 mikes until decorations are done, which needs 20 more minutes. "
             "Bravo 4 just texted: target insists on heading home NOW.",
             "Coordinate all stations: buy time, re-task assets, keep timings synced. Expect "
             "traffic from multiple callsigns and use Break correctly.",
             dynamic=True,
             twist="Play multiple stations. As Bravo 4: 'Negative, target is driving, I'm "
                   "passenger, ETA 15 mikes, advise.' As Bravo 2 (interrupt with Break): cake "
                   "pickup delayed 10 minutes. Occasionally garble one transmission so the "
                   "student must use 'Say again.' End when the student has a synced plan with "
                   "all stations acknowledging."),
    Scenario("contingency", 5, "the whole team",
             "Camping trip, day two. Weather radio reports severe thunderstorms in 90 minutes. "
             "Bravo 2 is at the lake with the kids (20 minutes away, spotty signal), Bravo 3 is "
             "at the ranger station buying firewood (15 minutes). Camp must be struck (30 "
             "minutes with two people) and everyone in vehicles before the storm.",
             "Recall all stations, assign tasks with timings, build in a comms-check schedule "
             "given the weak signal. Handle broken transmissions.",
             dynamic=True,
             twist="Play the stations. Bravo 2 comes in broken — reply with fragments so the "
                   "student says 'Say again' at least once; then confirm 25 mike ETA due to "
                   "packing wet gear. Bravo 3 asks whether to abandon the firewood. End when "
                   "tasks, timings, and a rally point are acknowledged by all."),
]


class ScenarioDeck:
    """Deals scenarios matching the current level, never repeating a category twice in a row."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.used: set[int] = set()
        self.last_category: str | None = None

    def draw(self, level: int) -> Scenario:
        pool = [
            (i, s) for i, s in enumerate(BANK)
            if s.level == min(level, 5) and i not in self.used
        ]
        if not pool:  # bank exhausted for this level: recycle
            pool = [(i, s) for i, s in enumerate(BANK) if s.level == min(level, 5)]
        preferred = [p for p in pool if p[1].category != self.last_category]
        i, s = self.rng.choice(preferred or pool)
        self.used.add(i)
        self.last_category = s.category
        return s
