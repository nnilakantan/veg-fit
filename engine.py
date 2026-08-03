"""
VEG-FIT Pro - workout generation engine (no UI code in here).

Design notes
------------
* The plan is *deterministic per calendar date*: the same date always produces the
  same workout (so refreshing the app mid-session doesn't shuffle your workout),
  but every date produces a different one.

* Session type is driven by a **9-day cycle**, not by the weekday. 9 and 7 are
  coprime, so the weekday -> session-type mapping only repeats every 63 days.
  That is the whole point of requirement #4: Monday is *not* "weights day".

* Exercise selection additionally avoids anything used in the previous
  ANTI_REPEAT_DAYS days, so you don't get goblet squats four sessions running.

* Programming follows the mainstream evidence for fat loss: resistance training
  is the backbone (preserve lean mass in a deficit), 2 HIIT sessions per cycle,
  2 Zone-2 sessions, 1 true recovery day. See README.md for sources.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable, Sequence

# --------------------------------------------------------------------------------------
# 1. YOUR CONFIG  --  edit these three things and nothing else needs to change
# --------------------------------------------------------------------------------------

# Equipment tokens. Delete a line to drop every exercise that needs it; the
# generator re-balances automatically.
DUMBBELLS = "dumbbells"
PUNCH_BAG = "punching_bag"
TREADMILL = "treadmill"
ROWER = "rower"
BODYWEIGHT = "bodyweight"
BENCH = "bench"  # a weight bench, sturdy chair, step or coffee table all count
JUMP_ROPE = "jump_rope"

MY_EQUIPMENT: set[str] = {
    DUMBBELLS,
    PUNCH_BAG,
    TREADMILL,
    ROWER,
    BODYWEIGHT,
    BENCH,
    # JUMP_ROPE,   # <- uncomment if you get one; adds rope intervals to HIIT days
}

# Used only for the calorie estimate. Set it to your actual weight.
BODY_WEIGHT_LB = 170

# How many days back to look when avoiding repeat exercises.
ANTI_REPEAT_DAYS = 5

# The cycle is anchored here. Changing this date shifts which session lands on
# which weekday, if you ever want to re-phase the program.
CYCLE_EPOCH = _dt.date(2026, 1, 1)

# --------------------------------------------------------------------------------------
# 2. EXERCISE DATABASE  --  free-exercise-db (public domain), cached to disk
# --------------------------------------------------------------------------------------

DB_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
IMG_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exercise_db_cache.json")


class ExerciseDB:
    """Lazy, cached accessor for the free-exercise-db dataset.

    The app is fully usable without it (you still get names, sets, reps and
    coaching cues) - the DB only supplies demo photos and step-by-step
    instructions, so a network failure degrades instead of crashing.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, dict] = {}
        self.status: str = "not loaded"

    def load(self) -> None:
        if self._by_id:
            return
        raw = self._read_cache()
        if raw is None:
            raw = self._download()
        if raw is not None:
            self._by_id = {e["id"]: e for e in raw if "id" in e}

    def _read_cache(self) -> list | None:
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                self.status = f"cached ({len(data)} exercises)"
                return data
        except (OSError, ValueError):
            pass
        return None

    def _download(self) -> list | None:
        try:
            req = urllib.request.Request(DB_URL, headers={"User-Agent": "veg-fit-pro"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            self.status = f"offline - demo photos unavailable ({type(exc).__name__})"
            return None
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except OSError:
            pass  # read-only dir is fine, we just re-download next time
        self.status = f"downloaded ({len(data)} exercises)"
        return data

    def entry(self, db_id: str | None) -> dict:
        if not db_id:
            return {}
        return self._by_id.get(db_id, {})

    def images(self, db_id: str | None) -> list[str]:
        """Absolute URLs for the start/end frames of the movement."""
        return [IMG_BASE + p for p in self.entry(db_id).get("images", [])]

    def instructions(self, db_id: str | None) -> list[str]:
        return list(self.entry(db_id).get("instructions", []))

    def muscles(self, db_id: str | None) -> list[str]:
        e = self.entry(db_id)
        return list(e.get("primaryMuscles", [])) + list(e.get("secondaryMuscles", []))


def video_search_url(name: str) -> str:
    q = urllib.parse.quote_plus(f"{name} proper form technique tutorial")
    return f"https://www.youtube.com/results?search_query={q}"


# --------------------------------------------------------------------------------------
# 3. MOVEMENT CATALOG
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Move:
    """One movement we know how to program.

    ``db_id`` links to free-exercise-db for photos + instructions. A few
    movements (heavy-bag rounds, machine interval protocols) have no honest
    match in that dataset; those carry ``db_id=None`` and rely on our own cue
    text plus the video link.
    """

    key: str
    name: str
    cue: str
    equip: frozenset[str]
    db_id: str | None = None
    note: str = ""  # shown when the stock photo differs from what you'll do

    @property
    def video_url(self) -> str:
        return video_search_url(self.name)


def _m(key, name, cue, equip, db_id="__same__", note="") -> Move:
    return Move(
        key=key,
        name=name,
        cue=cue,
        equip=frozenset(equip),
        db_id=key if db_id == "__same__" else db_id,
        note=note,
    )


D, B, T, R, W, BN, JR = DUMBBELLS, PUNCH_BAG, TREADMILL, ROWER, BODYWEIGHT, BENCH, JUMP_ROPE

# --- knee-dominant ---------------------------------------------------------------------
SQUAT = [
    _m("Goblet_Squat", "Goblet Squat", "Dumbbell at your chest, elbows inside your knees, sit straight down.", [D]),
    _m("Dumbbell_Squat", "Dumbbell Squat", "Weights at your sides, chest tall, knees tracking over your toes.", [D]),
    _m("Dumbbell_Lunges", "Dumbbell Lunge", "Step back, drop the back knee straight down, drive through the front heel.", [D]),
    _m("Dumbbell_Step_Ups", "Dumbbell Step-Up", "Whole foot on the step. Do NOT push off the trailing leg.", [D, BN]),
    _m("Dumbbell_Squat_To_A_Bench", "Dumbbell Box Squat", "Sit to the bench, pause a beat, stand without rocking.", [D, BN]),
    _m("Bodyweight_Walking_Lunge", "Walking Lunge", "Long strides, torso upright, control the descent.", [W]),
    _m("Bodyweight_Squat", "Bodyweight Squat", "Slow 3-count down, drive up fast. Squeeze glutes at the top.", [W]),
    _m("Sit_Squats", "Deep Sit Squat", "Heels down, sink into the hole and hold - a mobility squat.", [W]),
]

# --- hip-dominant ----------------------------------------------------------------------
HINGE = [
    _m("Romanian_Deadlift", "Dumbbell Romanian Deadlift", "Push your hips back, soft knees, dumbbells brushing your thighs.",
       [D], note="Stock photo shows a barbell - do the identical hinge holding dumbbells."),
    _m("Dumbbell_Clean", "Dumbbell Clean", "Explosive hip snap, then catch the weights at your shoulders.", [D]),
    _m("Butt_Lift_Bridge", "Glute Bridge", "Ribs down, squeeze the glutes hard at the top for a full second.", [W]),
    _m("Natural_Glute_Ham_Raise", "Nordic / Glute-Ham Raise", "Anchor your feet, lower as slowly as you can, catch with your hands.", [W]),
    _m("Glute_Kickback", "Glute Kickback", "Back flat. Drive the heel to the ceiling - no arching the lower back.", [W]),
]

# --- horizontal push --------------------------------------------------------------------
PUSH_H = [
    _m("Dumbbell_Bench_Press", "Dumbbell Bench Press", "Wrists stacked over elbows, lower until your elbows pass your ribs.", [D, BN]),
    _m("Dumbbell_Floor_Press", "Dumbbell Floor Press", "Triceps tap the floor, pause, then press. Great on a joint-cranky day.", [D]),
    _m("Dumbbell_Flyes", "Dumbbell Fly", "Big arc, slight elbow bend, stretch the chest - go light here.", [D, BN]),
    _m("Pushups", "Push-Up", "Body in one line, elbows about 45 degrees from your ribs.", [W]),
    _m("Push-Up_Wide", "Wide Push-Up", "Hands wider than shoulders - more chest, less triceps.", [W]),
    _m("Push_Up_to_Side_Plank", "Push-Up to Side Plank", "Press up, then rotate open and reach for the ceiling.", [W]),
    _m("Incline_Push-Up", "Incline Push-Up", "Hands elevated. Use this to keep reps clean once you fatigue.", [W, BN]),
    _m("Decline_Push-Up", "Decline Push-Up", "Feet elevated. Shifts load to the upper chest and shoulders.", [W, BN]),
    _m("Plyo_Push-up", "Plyometric Push-Up", "Push hard enough that your hands leave the floor. Land soft.", [W]),
]

# --- vertical push ----------------------------------------------------------------------
PUSH_V = [
    _m("Dumbbell_Shoulder_Press", "Dumbbell Shoulder Press", "Brace your abs so your lower back doesn't arch as you press.", [D]),
    _m("Arnold_Dumbbell_Press", "Arnold Press", "Start palms-in, rotate out as you press. Slow and deliberate.", [D]),
    _m("Side_Lateral_Raise", "Lateral Raise", "Lead with your elbows, stop at shoulder height, no swinging.", [D]),
    _m("Front_Dumbbell_Raise", "Front Raise", "Straight arms to eye level, lower under control over 3 seconds.", [D]),
]

# --- pull ---------------------------------------------------------------------------------
PULL = [
    _m("Bent_Over_Two-Dumbbell_Row", "Bent-Over Dumbbell Row", "Hinge to ~45 degrees, flat back, row to your hips not your chest.", [D]),
    _m("One-Arm_Dumbbell_Row", "One-Arm Dumbbell Row", "Brace on the bench, pull the elbow past your ribs, squeeze.", [D, BN]),
    _m("Dumbbell_Incline_Row", "Incline Dumbbell Row", "Chest supported - removes all lower-back cheating.", [D, BN]),
    _m("Dumbbell_One-Arm_Upright_Row", "One-Arm Upright Row", "Elbow leads, keep the weight close to your body.", [D]),
    _m("Bodyweight_Mid_Row", "Inverted / Table Row", "Use a sturdy table edge. Body straight, chest to the edge.", [W]),
    _m("Dumbbell_Lying_Rear_Lateral_Raise", "Lying Rear Delt Raise", "Face down on the bench, thumbs up, raise wide.", [D, BN]),
    _m("Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench", "Supported Rear Delt Raise",
       "Forehead on the bench takes momentum out - rear delts do all the work.", [D, BN]),
    _m("Dumbbell_Shrug", "Dumbbell Shrug", "Straight up, pause one second at the top, no rolling.", [D]),
]

# --- arms ------------------------------------------------------------------------------
ARMS = [
    _m("Dumbbell_Bicep_Curl", "Dumbbell Curl", "Elbows pinned to your sides, no swinging the torso.", [D]),
    _m("Hammer_Curls", "Hammer Curl", "Neutral grip. Hits the brachialis - makes the arm look thicker.", [D]),
    _m("Alternate_Hammer_Curl", "Alternating Hammer Curl", "One arm at a time, full lockout at the bottom.", [D]),
    _m("Cross_Body_Hammer_Curl", "Cross-Body Hammer Curl", "Curl across to the opposite shoulder.", [D]),
    _m("Concentration_Curls", "Concentration Curl", "Elbow braced on your thigh. Peak-contraction squeeze.", [D, BN]),
    _m("Tricep_Dumbbell_Kickback", "Triceps Kickback", "Upper arm locked parallel to the floor, extend from the elbow only.", [D]),
    _m("Lying_Dumbbell_Tricep_Extension", "Lying Triceps Extension", "Lower to your forehead, elbows pointing at the ceiling.", [D, BN]),
    _m("Bench_Dips", "Bench Dip", "Hips close to the bench, elbows straight back to 90 degrees.", [W, BN]),
    _m("Close-Grip_Push-Up_off_of_a_Dumbbell", "Close-Grip Push-Up", "Hands on the dumbbells, elbows tight to your ribs.", [D]),
]

# --- core ------------------------------------------------------------------------------
CORE = [
    _m("Plank", "Plank", "Squeeze glutes and abs. Hips level - no sagging, no piking.", [W]),
    _m("Side_Bridge", "Side Plank", "Stack your feet, drive the bottom hip to the ceiling.", [W]),
    _m("Russian_Twist", "Russian Twist", "Lean back to ~45 degrees, rotate from the ribs not the arms.", [W]),
    _m("Air_Bike", "Bicycle Crunch", "Slow. Opposite elbow to knee, fully extend the other leg.", [W]),
    _m("Crunches", "Crunch", "Curl the ribs toward the hips - don't yank on your neck.", [W]),
    _m("Cross-Body_Crunch", "Cross-Body Crunch", "Rotate through the obliques, pause at the top.", [W]),
    _m("Reverse_Crunch", "Reverse Crunch", "Lift the hips off the floor using your abs, not momentum.", [W]),
    _m("Bent-Knee_Hip_Raise", "Bent-Knee Hip Raise", "Small, controlled - it's a curl of the pelvis, not a leg throw.", [W]),
    _m("Superman", "Superman", "Lift arms and legs together, hold two seconds. Balances all that flexion.", [W]),
    _m("Spider_Crawl", "Spider Crawl", "Plank position, drive the knee to the same-side elbow.", [W]),
    _m("Decline_Crunch", "Decline Crunch", "Feet anchored. Control the way down, don't drop.", [W, BN]),
    _m("Scissor_Kick", "Scissor Kick", "Lower back pressed flat into the floor the entire time.", [W]),
    _m("Lower_Back_Curl", "Lower Back Curl", "Gentle extension - a good counterbalance to crunch work.", [W]),
    _m("Dumbbell_Side_Bend", "Dumbbell Side Bend", "One dumbbell only. Bend sideways, don't twist.", [D]),
    _m("Plate_Twist", "Weighted Russian Twist", "Hold one dumbbell, tap either side of your hips.",
       [D], note="Stock photo uses a plate - hold a dumbbell instead."),
]

# --- plyometric / explosive --------------------------------------------------------------
PLYO = [
    _m("Knee_Tuck_Jump", "Tuck Jump", "Explode up, knees to chest, land softly through the whole foot.", [W]),
    _m("Rocket_Jump", "Rocket Jump", "Dip, then jump as high as you can with arms overhead.", [W]),
    _m("Lateral_Bound", "Lateral Bound", "Skater-style. Push off sideways, stick the landing on one leg.", [W]),
    _m("Scissors_Jump", "Scissor / Split Jump", "Lunge, jump, swap legs mid-air. Soft, quiet landings.", [W]),
    _m("Freehand_Jump_Squat", "Jump Squat", "Squat to parallel, jump, absorb the landing back into a squat.", [W]),
    _m("Mountain_Climbers", "Mountain Climbers", "Hips low and still. Drive the knees fast.", [W]),
    _m("Bench_Jump", "Bench / Box Jump", "Jump up, STEP down. Never jump down - that's how ankles go.", [W, BN]),
    _m("Wind_Sprints", "Shuttle Sprints", "All-out for the work interval, then walk it off completely.", [W]),
]

# --- loaded carries / finishers ------------------------------------------------------------
CARRY = [
    _m("Farmers_Walk", "Farmer's Walk", "Heaviest dumbbells you own, shoulders back, walk tall and don't lean.",
       [D], note="Stock photo shows a strongman implement - dumbbells work identically."),
]

# --- cardio machines & the bag ---------------------------------------------------------------
CARDIO_HARD = [
    _m("Running_Treadmill", "Treadmill Sprint", "Hop onto the rails to start/stop the interval - don't decelerate the belt.", [T]),
    _m("Rowing_Stationary", "Rowing Machine", "Legs, then hips, then arms. Reverse the order on the recovery.", [R]),
    _m("Rope_Jumping", "Jump Rope", "Wrists do the turning, small hops, stay on the balls of your feet.", [JR]),
    _m("Heavy_Bag_Thrust", "Heavy Bag Thrust", "Explosive two-hand shove into the bag, catch it and repeat.", [B]),
]
CARDIO_STEADY = [
    _m("Jogging_Treadmill", "Treadmill Jog", "Conversational pace - you should be able to speak in full sentences.", [T]),
    _m("Walking_Treadmill", "Incline Treadmill Walk", "10-15% incline, 3-3.5 mph, hands OFF the rails.", [T]),
    _m("Rowing_Stationary", "Steady-State Row", "Aim for 22-24 strokes/min. Long, smooth, unhurried drives.", [R]),
    _m("Trail_Running_Walking", "Outdoor Walk / Jog", "Get outside. Nose-breathing pace.", [W]),
]

# Bag work has no honest match in the photo dataset, so these carry db_id=None:
# you get the written protocol plus a video link instead of a still photo.
BAG_WORK = [
    Move("bag_rounds", "Heavy Bag Rounds",
         "Hands up, chin down, rotate your hips into every punch. Never punch with a flat, locked arm.",
         frozenset([B]), None),
    Move("bag_combos", "Heavy Bag Power Combos",
         "1-2, 1-2-3, then a hook off the back foot. Reset your stance between combos.",
         frozenset([B]), None),
    Move("bag_speed", "Heavy Bag Speed Bursts",
         "Fastest hands you have for the burst, light contact. Speed over power.",
         frozenset([B]), None),
    Move("bag_technique", "Heavy Bag Technique Work",
         "Slow, deliberate reps. Film yourself once - most form errors are invisible from the inside.",
         frozenset([B]), None),
]

# --- warm-up (dynamic) --------------------------------------------------------------------
WARMUP = [
    _m("Arm_Circles", "Arm Circles", "20 forward, 20 back. Progressively bigger.", [W]),
    _m("Shoulder_Circles", "Shoulder Rolls", "Big slow circles, front and back.", [W]),
    _m("Elbow_Circles", "Elbow Circles", "Opens the elbows and biceps before any pressing.", [W]),
    _m("Ankle_Circles", "Ankle Circles", "Both directions. Cheap insurance before jumping or sprinting.", [W]),
    _m("Knee_Circles", "Knee Circles", "Hands on knees, small controlled circles.", [W]),
    _m("Hip_Circles_prone", "Hip Circles", "Big circles - the hips need the most warming of anything.", [W]),
    _m("Groiners", "Groiners", "Plank, step the foot outside the hand, drop the hip.", [W]),
    _m("Inchworm", "Inchworm", "Walk your hands out to a plank, walk your feet in. Repeat.", [W]),
    _m("Front_Leg_Raises", "Leg Swings (front)", "Controlled swings - momentum, not force.", [W]),
    _m("Rear_Leg_Raises", "Leg Swings (back)", "Squeeze the glute at the top of each swing.", [W]),
    _m("Side_Leg_Raises", "Lateral Leg Swings", "Opens the adductors before any lateral work.", [W]),
    _m("Dynamic_Chest_Stretch", "Dynamic Chest Opener", "Swing the arms wide and cross - build the range gradually.", [W]),
    _m("Dynamic_Back_Stretch", "Dynamic Back Stretch", "Reach and round, then extend. Wake the spine up.", [W]),
    _m("Crossover_Reverse_Lunge", "Crossover Reverse Lunge", "Step back and across - hits the glute medius.", [W]),
    _m("Iron_Crosses_stretch", "Iron Crosses", "On your back, cross the leg over. Shoulders stay down.", [W]),
    _m("Frog_Hops", "Frog Hops", "Deep squat, small hop forward. Great pre-plyo.", [W]),
    _m("Round_The_World_Shoulder_Stretch", "Round-the-World Shoulders", "Full shoulder circumduction.", [W]),
]

# --- cool-down (static) -------------------------------------------------------------------
COOLDOWN = [
    _m("Childs_Pose", "Child's Pose", "Sit back onto your heels, breathe into your back for 30-45s.", [W]),
    _m("Cat_Stretch", "Cat-Cow", "Slow, on the breath. Round on the exhale, arch on the inhale.", [W]),
    _m("Seated_Hamstring", "Seated Hamstring Stretch", "Hinge from the hips, flat back. Never round to reach further.", [W]),
    _m("Lying_Glute", "Lying Glute Stretch", "Figure-4, pull the supporting thigh toward you.", [W]),
    _m("Kneeling_Hip_Flexor", "Kneeling Hip Flexor Stretch", "Tuck your tailbone under FIRST, then lean. Huge difference.", [W]),
    _m("Overhead_Triceps", "Overhead Triceps Stretch", "Elbow to the ceiling, gently pull with the other hand.", [W]),
    _m("Overhead_Lat", "Overhead Lat Stretch", "Reach and side-bend away. Breathe into the ribs.", [W]),
    _m("Quad_Stretch", "Standing Quad Stretch", "Knees together, push the hip forward.", [W]),
    _m("Runners_Stretch", "Runner's Stretch", "Deep lunge, back heel reaching down.", [W]),
    _m("Seated_Calf_Stretch", "Seated Calf Stretch", "Pull the toes toward you, knee straight.", [W]),
    _m("One_Knee_To_Chest", "Knee to Chest", "One at a time, other leg flat on the floor.", [W]),
    _m("Hug_Knees_To_Chest", "Double Knee Hug", "Rock gently side to side to massage the lower back.", [W]),
    _m("Chin_To_Chest_Stretch", "Neck Flexion Stretch", "Slow. No pulling hard on the head.", [W]),
    _m("Side_Neck_Stretch", "Lateral Neck Stretch", "Ear toward shoulder, opposite hand reaching down.", [W]),
    _m("Behind_Head_Chest_Stretch", "Chest Stretch", "Hands behind head, drive the elbows back.", [W]),
    _m("Middle_Back_Stretch", "Mid-Back Stretch", "Round forward and reach - separate the shoulder blades.", [W]),
    _m("Seated_Glute", "Seated Glute Stretch", "Ankle on knee, sit tall, hinge forward.", [W]),
    _m("90_90_Hamstring", "90/90 Hamstring Stretch", "Hip and knee at 90, straighten the knee slowly.", [W]),
    _m("Lying_Crossover", "Supine Spinal Twist", "Both shoulders stay on the floor. Exhale into it.", [W]),
    _m("Knee_Across_The_Body", "Knee Across Body", "Gentle rotation for the lower back and glute.", [W]),
    _m("Calf_Stretch_Hands_Against_Wall", "Wall Calf Stretch", "Back heel down, back knee straight.", [W]),
    _m("Intermediate_Hip_Flexor_and_Quad_Stretch", "Couch Stretch", "The one that hurts if you sit all day. Do it anyway.", [W]),
]


def _available(pool: Sequence[Move]) -> list[Move]:
    return [m for m in pool if m.equip <= MY_EQUIPMENT]


# --------------------------------------------------------------------------------------
# 4. PLAN DATA MODEL
# --------------------------------------------------------------------------------------


@dataclass
class Item:
    move: Move
    dose: str  # "4 x 8-10" / "8 rounds: 30s hard / 30s easy"
    detail: str = ""  # RPE, rest, tempo


@dataclass
class Block:
    title: str
    subtitle: str
    items: list[Item] = field(default_factory=list)


@dataclass
class Plan:
    date: _dt.date
    cycle_day: int
    kind: str  # strength | hiit | metcon | zone2 | recovery
    title: str
    focus: str
    minutes: int
    blocks: list[Block]
    why: str  # why this session exists in a fat-loss program

    @property
    def main_keys(self) -> set[str]:
        """Keys used in the main work - what the anti-repeat logic looks at."""
        return {
            it.move.key
            for b in self.blocks
            if b.title not in ("Warm-Up", "Cool-Down")
            for it in b.items
        }

    @property
    def calorie_estimate(self) -> tuple[int, int]:
        met = {"strength": 5.0, "hiit": 9.0, "metcon": 8.0, "zone2": 6.5, "recovery": 3.3}[self.kind]
        kg = BODY_WEIGHT_LB * 0.4536
        kcal = met * 3.5 * kg / 200.0 * self.minutes
        return int(kcal * 0.85), int(kcal * 1.15)


# --------------------------------------------------------------------------------------
# 5. GENERATOR
# --------------------------------------------------------------------------------------

# 9-day cycle. 9 is coprime with 7, so the weekday -> session mapping takes
# 63 days to come back around: "every Monday is weights" cannot happen.
CYCLE = [
    ("strength", "Full-Body Strength Circuit", "Total body - metabolic circuit", 45),
    ("hiit", "HIIT Intervals", "Cardio - maximum intensity", 28),
    ("zone2", "Zone 2 Steady State", "Cardio - fat oxidation + core", 45),
    ("strength", "Upper Body Strength", "Chest, back, shoulders, arms + core", 45),
    ("metcon", "Metabolic Conditioning", "Full body - AMRAP + EMOM", 35),
    ("recovery", "Active Recovery & Mobility", "Restoration - keep the deficit, drop the stress", 30),
    ("strength", "Lower Body Strength", "Quads, hamstrings, glutes + core", 45),
    ("hiit", "HIIT Intervals", "Cardio - maximum intensity (different modality)", 28),
    ("zone2", "Long Zone 2 + Core", "Cardio - longest aerobic piece of the cycle", 55),
]

WHY = {
    "strength": (
        "Resistance training is the backbone of fat loss, not cardio. In a calorie deficit it is what "
        "tells your body to hold onto lean muscle and shed fat instead of the other way round. Keep the "
        "rests short - that is what turns a strength session into a metabolic one."
    ),
    "hiit": (
        "HIIT is a time-efficiency tool: roughly the same fat loss as steady cardio in about 40% of the time. "
        "It is deliberately capped at 2 sessions per cycle - daily HIIT reliably leads to overtraining and "
        "junk-intensity sessions."
    ),
    "zone2": (
        "Low-intensity aerobic work burns a high proportion of fat, adds almost no recovery cost, and lets you "
        "keep training hard on the other days. This is the session most people skip and most need."
    ),
    "metcon": (
        "Mixed-modal conditioning keeps the heart rate high across a lot of muscle mass. High energy cost per "
        "minute, and enough variety that you stay interested past week three."
    ),
    "recovery": (
        "Fat loss happens while you recover, not while you train. Light movement raises your daily energy "
        "burn (NEAT) without adding fatigue, and mobility work is what keeps the hard days available to you."
    ),
}

STRENGTH_SCHEMES = [
    ("4 sets x 8-10 reps", "RPE 8 - stop 2 reps short of failure - 60s rest"),
    ("3 sets x 12-15 reps", "RPE 7-8 - lighter and faster - 45s rest"),
    ("5 sets x 6-8 reps", "RPE 8-9 - heaviest scheme - 75s rest"),
    ("3 sets x 10-12 reps", "RPE 8 - 2 seconds down, 1 second up - 50s rest"),
    ("4 sets x 12 reps", "RPE 7-8 - constant tension, no lockout pauses - 45s rest"),
]

HIIT_PROTOCOLS = [
    ("10 rounds: 30s hard / 30s easy", "Hard = ~90% effort. You should not be able to talk."),
    ("8 rounds: 40s hard / 20s easy", "Short recovery - pace the first two rounds or you will die on round five."),
    ("2 blocks of 8 x 20s / 10s (Tabata)", "3 minutes easy between blocks. Brutal and very short."),
    ("8 rounds: 60s hard / 60s easy", "Longer intervals - hold a hard-but-repeatable pace, not a sprint."),
    ("Pyramid: 15/30/45/60/45/30/15s hard", "Equal easy time after each. Two times through."),
    ("12 rounds: 30s hard / 45s easy", "Higher volume, slightly more recovery. Keep every rep quality."),
]

ZONE2_DOSE = [
    ("30 minutes continuous", "Heart rate 60-70% of max. You can hold a conversation the whole way."),
    ("35 minutes continuous", "Nose-breathing pace. If you are mouth-breathing you are going too hard."),
    ("40 minutes continuous", "Boring is the point. Put a podcast on."),
    ("45 minutes continuous", "The longest steady piece - fuel with water and don't rush it."),
]


def _rng(date: _dt.date, salt: str = "") -> random.Random:
    return random.Random(f"{date.isoformat()}|{salt}|vegfit-v2")


class Picker:
    """Draws movements for one session.

    Two separate exclusion rules, and the distinction matters:

    * ``used`` is a HARD rule - a movement already chosen for this session can
      never be chosen again, so you never see the same exercise twice in one day
      even when the equipment filter has left a pool almost empty.
    * ``avoid`` is a SOFT rule - movements you did in the last few days go to the
      back of the queue, but they are still available if the pool would otherwise
      run dry.
    """

    def __init__(self, rng: random.Random, avoid: Iterable[str]) -> None:
        self.rng = rng
        self.avoid = set(avoid)
        self.used: set[str] = set()

    def take(self, pool: Sequence[Move], n: int) -> list[Move]:
        items = [m for m in pool if m.equip <= MY_EQUIPMENT and m.key not in self.used]
        if not items:
            return []
        self.rng.shuffle(items)
        fresh = [m for m in items if m.key not in self.avoid]
        stale = [m for m in items if m.key in self.avoid]
        out = (fresh + stale)[:n]
        self.used.update(m.key for m in out)
        return out

    def one(self, pool: Sequence[Move]) -> Move | None:
        got = self.take(pool, 1)
        return got[0] if got else None

    def choice(self, options: Sequence):
        return options[self.rng.randrange(len(options))]


def _block(title: str, subtitle: str, items: list[Item]) -> Block | None:
    """Blocks whose pool was emptied by the equipment filter are dropped."""
    return Block(title, subtitle, items) if items else None


def _compact(blocks: Iterable[Block | None]) -> list[Block]:
    return [b for b in blocks if b is not None]


def _warmup(p: Picker) -> Block | None:
    return _block(
        "Warm-Up",
        "5 minutes - do not skip this, it is where injuries don't happen",
        [Item(m, "45 seconds", "Easy, building range each rep") for m in p.take(WARMUP, 5)],
    )


def _cooldown(p: Picker) -> Block | None:
    return _block(
        "Cool-Down",
        "5 minutes - breathe out slowly, this is what drops your heart rate",
        [Item(m, "40 seconds each side", "Stretch to mild tension, never to pain") for m in p.take(COOLDOWN, 5)],
    )


def _build(date: _dt.date, avoid: set[str]) -> Plan:
    cycle_day = (date - CYCLE_EPOCH).days % len(CYCLE)
    kind, title, focus, minutes = CYCLE[cycle_day]

    # One picker for the whole session, so no movement can appear twice - not
    # even across the main work and the cool-down on a mobility day.
    p = Picker(_rng(date, kind), avoid)

    warm = _warmup(Picker(_rng(date, "warmup"), avoid))
    if warm:
        p.used.update(i.move.key for i in warm.items)

    if kind == "strength" and cycle_day == 0:
        main = _full_body(p)
    elif kind == "strength" and cycle_day == 3:
        main = _upper(p)
    elif kind == "strength":
        main = _lower(p)
    elif kind == "hiit":
        main = _hiit(p, alt=(cycle_day == 7))
    elif kind == "metcon":
        main = _metcon(p)
    elif kind == "zone2":
        main = _zone2(p, long=(cycle_day == 8))
    else:
        main = _recovery(p)

    blocks = _compact([warm, *main, _cooldown(p)])
    return Plan(date, cycle_day, kind, title, focus, minutes, blocks, WHY[kind])


def _full_body(p: Picker) -> list[Block | None]:
    dose, detail = p.choice(STRENGTH_SCHEMES)
    picks = (
        p.take(SQUAT, 1) + p.take(HINGE, 1) + p.take(PUSH_H, 1) + p.take(PULL, 1) + p.take(PUSH_V, 1)
    )
    fin = p.take(PLYO, 2) + p.take(CORE, 1)
    return [
        _block("Main Work - Circuit",
               f"{dose}. Move between exercises with minimal rest, then rest 90s at the end of each round.",
               [Item(m, dose, detail) for m in picks]),
        _block("Finisher",
               "3 rounds, 40 seconds on / 20 seconds off. This is the part that raises the calorie cost.",
               [Item(m, "40 seconds", "All-out but controlled") for m in fin]),
    ]


def _upper(p: Picker) -> list[Block | None]:
    dose, detail = p.choice(STRENGTH_SCHEMES)
    a = p.take(PUSH_H, 1) + p.take(PULL, 1)
    b = p.take(PUSH_V, 1) + p.take(PULL, 1)
    arms = p.take(ARMS, 2)
    core = p.take(CORE, 2)
    return [
        _block("Superset A - Push / Pull", f"{dose}. Alternate the two with no rest between them.",
               [Item(m, dose, detail) for m in a]),
        _block("Superset B - Shoulders / Back", "3 sets x 12 reps. Same deal - alternate, then 45s rest.",
               [Item(m, "3 x 12", "RPE 7-8 - lighter weight, perfect form") for m in b]),
        _block("Arms", "2 sets x 15 reps each, straight through.",
               [Item(m, "2 x 15", "RPE 7 - burn, not grind - 30s rest") for m in arms]),
        _block("Core Finisher", "3 rounds, minimal rest.",
               [Item(m, "45 seconds", "Quality over speed") for m in core]),
    ]


def _lower(p: Picker) -> list[Block | None]:
    dose, detail = p.choice(STRENGTH_SCHEMES)
    sq = p.take(SQUAT, 2)
    hi = p.take(HINGE, 2)
    power = [(m, "30 seconds") for m in p.take(PLYO, 1)] + [(m, "45 seconds") for m in p.take(CARRY, 1)]
    core = p.take(CORE, 2)
    return [
        _block("Knee-Dominant", f"{dose}.", [Item(m, dose, detail) for m in sq]),
        _block("Hip-Dominant", "3 sets x 12 reps. Slow eccentric - 3 seconds lowering.",
               [Item(m, "3 x 12", "RPE 8 - 60s rest") for m in hi]),
        _block("Power + Carry", "3 rounds. Explosive work while you are still fresh enough to be explosive.",
               [Item(m, d, "Land soft / walk tall") for m, d in power]),
        _block("Core Finisher", "3 rounds, minimal rest.",
               [Item(m, "45 seconds", "Brace, don't hold your breath") for m in core]),
    ]


def _hiit(p: Picker, alt: bool) -> list[Block | None]:
    dose, detail = p.choice(HIIT_PROTOCOLS)
    # Lead with the bag on the second HIIT day of the cycle, machines on the first,
    # so the two HIIT slots never feel like the same session.
    primary = p.one(BAG_WORK + CARDIO_HARD if alt else CARDIO_HARD + BAG_WORK)
    second = p.one(CARDIO_HARD + BAG_WORK)
    body = p.take(PLYO, 2) + p.take(CORE, 2)
    return [
        _block("Main Interval Set", detail,
               [Item(primary, dose, "Warm up 3 min easy first")] if primary else []),
        _block("Second Modality", "Switch machines - keeps the legs fresh enough to hold intensity.",
               [Item(second, "6 rounds: 30s hard / 60s easy", "Slightly longer recovery here")] if second else []),
        _block("Bodyweight Burnout", "2 rounds, 30 seconds on / 15 seconds off.",
               [Item(m, "30 seconds", "Last 5 minutes - empty the tank") for m in body]),
    ]


def _metcon(p: Picker) -> list[Block | None]:
    amrap = p.take(SQUAT, 1) + p.take(PUSH_H, 1) + p.take(PULL, 1) + p.take(CORE, 1)
    emom = p.take(PLYO, 1) + p.take(HINGE, 1)
    cond = p.one(CARDIO_HARD + BAG_WORK)
    return [
        _block("AMRAP 12",
               "As many rounds as possible in 12 minutes: 10 reps of each, back to back. Log your rounds.",
               [Item(m, "10 reps", "Break sets before you have to, not after") for m in amrap]),
        _block("EMOM 10",
               "Every minute on the minute for 10 minutes - alternate the two. Rest is whatever is left of the minute.",
               [Item(m, "12 reps", "Aim for ~35 seconds of work") for m in emom]),
        _block("Conditioning Cap", "One hard push to finish.",
               [Item(cond, "5 minutes for max distance / rounds", "Negative split - second half faster")]
               if cond else []),
    ]


def _zone2(p: Picker, long: bool) -> list[Block | None]:
    primary = p.one(CARDIO_STEADY)
    dose, detail = ZONE2_DOSE[p.rng.randrange(2, 4) if long else p.rng.randrange(0, 2)]
    second = p.one(CARDIO_STEADY) if long else None
    core = p.take(CORE, 3)
    return [
        _block("Steady State", detail,
               [Item(primary, dose, "Zone 2 - RPE 4-5 out of 10")] if primary else []),
        _block("Modality Swap", "Split the time across two machines - easier on the joints.",
               [Item(second, "15 minutes continuous", "Same easy effort")] if second else []),
        _block("Core Circuit", "3 rounds, 40 seconds each, 20 seconds rest.",
               [Item(m, "40 seconds", "Slow and deliberate - you are not tired, so no excuses") for m in core]),
    ]


def _recovery(p: Picker) -> list[Block | None]:
    easy = p.one(CARDIO_STEADY)
    skill = p.one([m for m in BAG_WORK if m.key == "bag_technique"] or BAG_WORK)
    mob = p.take(COOLDOWN, 6)
    return [
        _block("Easy Movement", "Genuinely easy. If you are breathing hard you have missed the point.",
               [Item(easy, "20-25 minutes", "RPE 3 out of 10")] if easy else []),
        _block("Skill Work (optional)", "Technique only - no power, no fatigue.",
               [Item(skill, "3 rounds x 2 minutes", "Light contact, focus on footwork")] if skill else []),
        _block("Extended Mobility", "Hold each for 60 seconds. This is the session, not a warm-up for one.",
               [Item(m, "60 seconds", "Relax into it - tension defeats the stretch") for m in mob]),
    ]


def generate_plan(date: _dt.date) -> Plan:
    """The plan for ``date``, avoiding movements used in the previous days.

    Lookback is intentionally one level deep (previous days are generated with an
    empty avoid-set) so this always terminates and stays deterministic.
    """
    recent: set[str] = set()
    for back in range(1, ANTI_REPEAT_DAYS + 1):
        recent |= _build(date - _dt.timedelta(days=back), set()).main_keys
    return _build(date, recent)


def upcoming(date: _dt.date, days: int = 7) -> list[Plan]:
    return [generate_plan(date + _dt.timedelta(days=i)) for i in range(days)]
