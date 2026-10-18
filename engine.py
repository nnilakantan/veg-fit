"""
engine.py - Core Training Engine for VEG-FIT Pro
Handles exercise database indexing, 9-day periodization cycling,
kettlebell loading strategies (10, 15, 20 lbs), and daily plan generation.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ----------------------------------------------------------------------------------
# Global Configuration & Periodization Cycle
# ----------------------------------------------------------------------------------
ANTI_REPEAT_DAYS: int = 3
BODY_WEIGHT_LB: float = 140.0

# 9-day undulating periodization cycle:
# 3 Strength · 2 HIIT · 2 Zone 2 · 1 Metcon · 1 Recovery = 9 days
# (9 and 7 are coprime, drifting smoothly across weekdays)
CYCLE: List[str] = [
    "strength",   # Day 1: Strength - Upper Body Push/Pull & Core Armor
    "hiit",       # Day 2: HIIT - Kettlebell Swings & Anaerobic Intervals
    "zone2",      # Day 3: Zone 2 - Aerobic Mitochondrial Base
    "strength",   # Day 4: Strength - Lower Body Posterior Chain & Squat
    "metcon",     # Day 5: Metcon - Full Body Kettlebell Density Complex
    "zone2",      # Day 6: Zone 2 - Low-Impact Cardiovascular Flush
    "strength",   # Day 7: Strength - Total Body Functional Hypertrophy
    "hiit",       # Day 8: HIIT - Tabata Conditioning & Core
    "recovery",   # Day 9: Active Recovery - Joint Mobility & Decompression
]

# Equipment inventory incorporating your 10, 15, and 20 lb kettlebells
MY_EQUIPMENT: Set[str] = {
    "body_only",
    "kettlebells",
    "dumbbell",
}

MY_KETTLEBELLS: List[int] = [10, 15, 20]  # Available bell sizes (lbs)
EPOCH_DATE: dt.date = dt.date(2026, 1, 1)

# ----------------------------------------------------------------------------------
# Data Models
# ----------------------------------------------------------------------------------
@dataclass
class Move:
    name: str
    db_id: str
    cue: str = ""
    note: str = ""
    video_url: str = ""
    equipment: str = "body_only"
    category: str = "strength"
    primary_muscles: List[str] = field(default_factory=list)
    secondary_muscles: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)


@dataclass
class Item:
    move: Move
    dose: str
    detail: str = ""


@dataclass
class Block:
    title: str
    subtitle: str
    items: List[Item]


@dataclass
class Plan:
    date: dt.date
    kind: str
    title: str
    focus: str
    why: str
    minutes: int
    calorie_estimate: Tuple[int, int]
    cycle_day: int
    blocks: List[Block]


@dataclass
class PlanSummary:
    date: dt.date
    kind: str
    title: str

# ----------------------------------------------------------------------------------
# Curated Exercise Library (Free-Exercise-DB Schema Compatible)
# ----------------------------------------------------------------------------------
BASE_GITHUB_IMG = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises"

CURATED_EXERCISES: List[Dict] = [
    # --- Kettlebell Essentials (10, 15, 20 lb) ---
    {
        "id": "kb_two_arm_swing",
        "name": "Kettlebell Two-Arm Swing",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["glutes", "hamstrings", "lower back"],
        "secondaryMuscles": ["shoulders", "abs", "forearms"],
        "cue": "Hinge at the hips with a flat back; snap hips violently forward. Power comes from glutes, not arms.",
        "note": "Use your 20 lb bell for explosive hip power. Keep the bell above knee level on the backswing.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+two+arm+swing+form",
        "instructions": [
            "Stand with feet slightly wider than shoulder-width, kettlebell on the floor 1 foot in front of you.",
            "Hinge hips back with a soft knee bend, grabbing the handle with both hands.",
            "Hike the kettlebell back between your legs like a center in football.",
            "Drive your feet through the floor and snap your hips forward to full vertical standing lock.",
            "Let the bell float up to chest height on momentum; guide it back into the hinge."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Kettlebell_Swing/0.jpg",
            f"{BASE_GITHUB_IMG}/Kettlebell_Swing/1.jpg"
        ]
    },
    {
        "id": "kb_goblet_squat",
        "name": "Kettlebell Goblet Squat",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["quadriceps", "glutes"],
        "secondaryMuscles": ["calves", "abdominals", "upper back"],
        "cue": "Hold horns tight against sternum; pry knees apart with elbows in the bottom hole.",
        "note": "Great with either the 15 lb or 20 lb bell. Keep chest proud and spine neutral.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+goblet+squat+technique",
        "instructions": [
            "Hold the kettlebell close to your chest by the horns or ball with elbows tucked.",
            "Set your feet shoulder-width apart, toes turned slightly out (15-30 degrees).",
            "Inhale deep into your belly, descend by sending hips back and spreading your knees.",
            "Reach parallel or deeper while maintaining an upright torso.",
            "Drive out of the hole through mid-foot and heel to stand tall."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Goblet_Squat/0.jpg",
            f"{BASE_GITHUB_IMG}/Goblet_Squat/1.jpg"
        ]
    },
    {
        "id": "kb_single_arm_clean_press",
        "name": "Kettlebell Clean & Strict Press",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["shoulders", "triceps", "upper back"],
        "secondaryMuscles": ["glutes", "core", "forearms"],
        "cue": "Zip the jacket up to clean into rack position; crush the handle and press vertically overhead.",
        "note": "Use 10 lb bell for strict overhead control, or 15 lb as strength builds.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+clean+and+press",
        "instructions": [
            "Hinge and grab the bell single-handed; hike back and snap hips to clean into the front rack.",
            "In rack position, forearm is vertical, wrist straight, thumb tucked near collarbone.",
            "Squeeze glutes and abs tight to create a solid pillar.",
            "Press the bell smoothly overhead to full elbow lockout without leaning back.",
            "Lower slowly under control back into the rack position."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Clean_and_press/0.jpg",
            f"{BASE_GITHUB_IMG}/Clean_and_press/1.jpg"
        ]
    },
    {
        "id": "kb_single_arm_row",
        "name": "Kettlebell Gorilla Row",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["lats", "rhomboids"],
        "secondaryMuscles": ["biceps", "core", "hamstrings"],
        "cue": "Drive elbow towards hip pocket; keep opposing shoulder square and resist torso rotation.",
        "note": "Best with 15 lb or 20 lb bell. Focus on lat contraction at the top.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+gorilla+row",
        "instructions": [
            "Hinge into a wide deadlift stance with bell between your feet.",
            "Grab the handle with one hand while stabilizing through flat back.",
            "Pull elbow back towards ribcage without twisting your spine.",
            "Pause for 1 second at apex contraction, then return down with control."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Kettlebell_One-Arm_Row/0.jpg",
            f"{BASE_GITHUB_IMG}/Kettlebell_One-Arm_Row/1.jpg"
        ]
    },
    {
        "id": "kb_halo",
        "name": "Kettlebell Standing Halo",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["shoulders", "neck", "abdominals"],
        "secondaryMuscles": ["rotator cuff", "upper back"],
        "cue": "Circle the bell tight around your head like crown; keep ribs glued down and core locked.",
        "note": "Use the 10 lb bell to lubricate shoulders and build scapular resilience.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+halo+form",
        "instructions": [
            "Hold bell upside down by horns at upper chest level.",
            "Brace core firmly and orbit the bell closely around your ear, behind neck, and around opposite ear.",
            "Minimize neck and ribcage swaying; move smoothly through full 360-degree rotation.",
            "Alternate clockwise and counterclockwise repetitions."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Kettlebell_Halo/0.jpg",
            f"{BASE_GITHUB_IMG}/Kettlebell_Halo/1.jpg"
        ]
    },
    {
        "id": "kb_turkish_get_up",
        "name": "Kettlebell Turkish Get-Up (Half or Full)",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["shoulders", "abdominals", "quadriceps"],
        "secondaryMuscles": ["glutes", "forearms", "stabilizers"],
        "cue": "Eyes glued to bell knuckles throughout movement; keep supporting arm bone-stacked.",
        "note": "Use the 10 lb bell for premier shoulder stability and functional core control.",
        "video_url": "https://www.youtube.com/results?search_query=turkish+get+up+step+by+step",
        "instructions": [
            "Lie flat with bell pressed straight up in right arm; right knee bent, foot flat.",
            "Roll up diagonally onto left forearm, then press onto left palm.",
            "Bridge hips up, sweep left leg under to kneel in half-kneeling lunge.",
            "Stand tall while maintaining vertical bell lockout overhead.",
            "Reverse each milestone carefully back to floor."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Turkish_Get_Up/0.jpg",
            f"{BASE_GITHUB_IMG}/Turkish_Get_Up/1.jpg"
        ]
    },
    {
        "id": "kb_romanian_deadlift",
        "name": "Kettlebell Romanian Deadlift",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["hamstrings", "glutes"],
        "secondaryMuscles": ["lower back", "lats", "forearms"],
        "cue": "Push hips back towards back wall; soft knees, shins vertical, feel deep hamstring stretch.",
        "note": "Prime candidate for 20 lb bell. Pack lats tight to protect spine.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+romanian+deadlift",
        "instructions": [
            "Hold kettlebell by handle with both hands in front of thighs.",
            "Hinge hips back while keeping knees softly unlocked and spine straight.",
            "Lower bell just past kneecaps until maximum hamstring tension is achieved.",
            "Drive hips forward to return to standing lockout."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Romanian_Deadlift/0.jpg",
            f"{BASE_GITHUB_IMG}/Romanian_Deadlift/1.jpg"
        ]
    },
    {
        "id": "kb_russian_twist",
        "name": "Kettlebell Russian Twist",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["abdominals", "obliques"],
        "secondaryMuscles": ["lower back", "hip flexors"],
        "cue": "Rotate from upper ribcage, not just moving arms; keep heels hovering or lightly anchored.",
        "note": "Use 10 lb or 15 lb bell. Keep control over speed to protect lower back.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+russian+twist",
        "instructions": [
            "Sit on floor with knees bent, torso reclined back at 45 degrees.",
            "Hold kettlebell at chest with both hands.",
            "Rotate torso smoothly from left hip to right hip under steady tension."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Russian_Twist/0.jpg",
            f"{BASE_GITHUB_IMG}/Russian_Twist/1.jpg"
        ]
    },
    {
        "id": "kb_suitcase_carry",
        "name": "Kettlebell Suitcase Carry",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["obliques", "forearms", "traps"],
        "secondaryMuscles": ["glutes", "calves"],
        "cue": "Walk tall like proud royalty; resist leaning sideways toward the loaded side.",
        "note": "Challenge yourself with the 20 lb bell for intense lateral core anti-flexion.",
        "video_url": "https://www.youtube.com/results?search_query=suitcase+carry+kettlebell",
        "instructions": [
            "Deadlift bell with one hand by side like a suitcase.",
            "Keep shoulders level and posture tall; walk smoothly for distance or time.",
            "Turn around, switch hands and repeat."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Farmers_Walk/0.jpg",
            f"{BASE_GITHUB_IMG}/Farmers_Walk/1.jpg"
        ]
    },
    {
        "id": "kb_windmill",
        "name": "Kettlebell Windmill",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["obliques", "shoulders", "hamstrings"],
        "secondaryMuscles": ["rotator cuff", "glutes"],
        "cue": "Push hip back in direction of bell; slide bottom hand down inside front leg.",
        "note": "Use the 10 lb bell to master flexibility and shoulder stability.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+windmill",
        "instructions": [
            "Press kettlebell overhead with right arm; turn feet 45 degrees away from bell.",
            "Shift right hip back, keeping right arm locked straight toward ceiling.",
            "Slide left hand down inside left leg towards floor while looking at bell.",
            "Engage glutes to reverse back up to starting position."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Windmills/0.jpg",
            f"{BASE_GITHUB_IMG}/Windmills/1.jpg"
        ]
    },
    # --- Bodyweight Calisthenics & Cardio Engine ---
    {
        "id": "bw_pushups",
        "name": "Standard Push-Up (Tempo)",
        "equipment": "body_only",
        "category": "strength",
        "primaryMuscles": ["chest", "triceps"],
        "secondaryMuscles": ["shoulders", "core"],
        "cue": "Body forms a rigid plank from crown to heels; elbows track at 45-degree angle.",
        "note": "Control the 2-second eccentric phase for maximum hypertrophy.",
        "video_url": "https://www.youtube.com/results?search_query=push+up+proper+form",
        "instructions": [
            "Start in high plank with hands directly beneath shoulders.",
            "Lower chest to floor while bracing glutes and quadriceps.",
            "Press explosively back to top lockout."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Pushups/0.jpg",
            f"{BASE_GITHUB_IMG}/Pushups/1.jpg"
        ]
    },
    {
        "id": "bw_mountain_climbers",
        "name": "Speed Mountain Climbers",
        "equipment": "body_only",
        "category": "cardio",
        "primaryMuscles": ["abdominals", "hip flexors"],
        "secondaryMuscles": ["shoulders", "quadriceps"],
        "cue": "Drive knees toward chest without bouncing hips; maintain stable plank.",
        "note": "Great for HIIT intervals and cardiovascular output.",
        "video_url": "https://www.youtube.com/results?search_query=mountain+climbers+exercise",
        "instructions": [
            "Hold push-up position with hands flat on floor.",
            "Quickly alternate driving knees forward towards chest in running motion."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Mountain_climbers/0.jpg",
            f"{BASE_GITHUB_IMG}/Mountain_climbers/1.jpg"
        ]
    },
    {
        "id": "bw_air_squats",
        "name": "Bodyweight Tempo Air Squat",
        "equipment": "body_only",
        "category": "strength",
        "primaryMuscles": ["quadriceps", "glutes"],
        "secondaryMuscles": ["calves", "core"],
        "cue": "Sink between hips with upright spine; track knees over outer toes.",
        "note": "Excellent for warm-up or high-volume conditioning.",
        "video_url": "https://www.youtube.com/results?search_query=air+squat+form",
        "instructions": [
            "Stand tall, feet shoulder-width apart.",
            "Squat down until thighs break parallel, keeping arms out for balance.",
            "Stand tall and squeeze glutes at the top."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Bodyweight_Squat/0.jpg",
            f"{BASE_GITHUB_IMG}/Bodyweight_Squat/1.jpg"
        ]
    },
    {
        "id": "rec_world_greatest_stretch",
        "name": "World's Greatest Hip & Thoracic Stretch",
        "equipment": "body_only",
        "category": "stretching",
        "primaryMuscles": ["hip flexors", "hamstrings", "lats"],
        "secondaryMuscles": ["thoracic spine", "glutes"],
        "cue": "Elbow down inside front instep, rotate upper arm to ceiling, exhale into stretch.",
        "note": "Unrivaled joint opener before lifting or on active recovery days.",
        "video_url": "https://www.youtube.com/results?search_query=worlds+greatest+stretch",
        "instructions": [
            "Step into deep forward lunge with hands inside front foot.",
            "Drop inside elbow toward floor, pause for 2 seconds.",
            "Reach that same arm to ceiling, rotating upper spine.",
            "Straighten front leg to stretch hamstring, then switch sides."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Groin_Stretch/0.jpg",
            f"{BASE_GITHUB_IMG}/Groin_Stretch/1.jpg"
        ]
    }
]

# ----------------------------------------------------------------------------------
# Exercise Database Manager
# ----------------------------------------------------------------------------------
class ExerciseDB:
    """
    Manages catalog of exercises, metadata, muscles, and animated demos.
    Supports offline fallback and optional JSON loading from free-exercise-db.
    """
    def __init__(self):
        self._exercises: Dict[str, Move] = {}
        self.status: str = "Ready (Curated)"

    def load(self, json_path: Optional[str] = None):
        """Loads curated catalog and supplements with free-exercise-db if available."""
        for ex in CURATED_EXERCISES:
            move = Move(
                name=ex["name"],
                db_id=ex["id"],
                cue=ex.get("cue", ""),
                note=ex.get("note", ""),
                video_url=ex.get("video_url", ""),
                equipment=ex.get("equipment", "body_only"),
                category=ex.get("category", "strength"),
                primary_muscles=ex.get("primaryMuscles", []),
                secondary_muscles=ex.get("secondaryMuscles", []),
                instructions=ex.get("instructions", []),
                images=ex.get("images", [])
            )
            self._exercises[move.db_id] = move

        candidate_paths = [
            json_path,
            "exercises.json",
            "dist/exercises.json",
            os.path.expanduser("~/.cache/free-exercise-db/exercises.json")
        ]
        
        for path in candidate_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        count = self._ingest_raw_json(data)
                        self.status = f"Loaded {count} exercises from {os.path.basename(path)}"
                        return
                except Exception:
                    pass

        self.status = f"{len(self._exercises)} exercises indexed (Kettlebell & Functional DB)"

    def _ingest_raw_json(self, raw_list: List[Dict]) -> int:
        count = 0
        for item in raw_list:
            db_id = item.get("id") or item.get("name", "").lower().replace(" ", "_")
            if not db_id:
                continue
            imgs = item.get("images", [])
            full_imgs = [img if img.startswith("http") else f"{BASE_GITHUB_IMG}/{img.lstrip('/')}" for img in imgs]
            move = Move(
                name=item.get("name", db_id.replace("_", " ").title()),
                db_id=db_id,
                cue=item.get("instructions", ["Focus on clean posture and breathing."])[0] if item.get("instructions") else "Move with control.",
                note=f"Equipment: {item.get('equipment', 'body only').title()}",
                video_url=f"https://www.youtube.com/results?search_query={item.get('name', '').replace(' ', '+')}+exercise",
                equipment=item.get("equipment", "body only").replace(" ", "_"),
                category=item.get("category", "strength"),
                primary_muscles=item.get("primaryMuscles", []),
                secondary_muscles=item.get("secondaryMuscles", []),
                instructions=item.get("instructions", []),
                images=full_imgs
            )
            self._exercises[db_id] = move
            count += 1
        return count

    def get_move(self, db_id: str) -> Optional[Move]:
        return self._exercises.get(db_id)

    def images(self, db_id: str) -> List[str]:
        m = self.get_move(db_id)
        return m.images if m else []

    def instructions(self, db_id: str) -> List[str]:
        m = self.get_move(db_id)
        return m.instructions if m else []

    def muscles(self, db_id: str) -> List[str]:
        m = self.get_move(db_id)
        return (m.primary_muscles + m.secondary_muscles) if m else []

    def filter_moves(self, equipment_allowed: Set[str], category: Optional[str] = None) -> List[Move]:
        matches = []
        for m in self._exercises.values():
            eq = m.equipment.lower().rstrip("s")
            allowed = any(allowed_eq.lower().rstrip("s") in eq or eq in allowed_eq.lower().rstrip("s") for allowed_eq in equipment_allowed)
            if allowed and (category is None or m.category.lower() == category.lower()):
                matches.append(m)
        return matches

# ----------------------------------------------------------------------------------
# Periodization & Plan Generator
# ----------------------------------------------------------------------------------
_DB_INSTANCE: Optional[ExerciseDB] = None

def get_engine_db() -> ExerciseDB:
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = ExerciseDB()
        _DB_INSTANCE.load()
    return _DB_INSTANCE


def format_dose_and_detail(move: Move, kind: str) -> Tuple[str, str]:
    """Generates dosage and weight recommendation based on movement & session intensity."""
    name = move.name.lower()
    is_kb = "kettlebell" in name or "kettlebell" in move.equipment.lower() or "kb_" in move.db_id

    if kind == "strength":
        if is_kb:
            if any(w in name for w in ["swing", "deadlift", "squat", "carry", "gorilla"]):
                return ("4 sets × 12 reps @ 20 lb", "Rest 75s · Focus on explosive hip drive")
            elif any(w in name for w in ["halo", "windmill", "turkish", "press"]):
                return ("3 sets × 8 reps/side @ 10 lb", "Rest 60s · Shoulder stability & packed lats")
            else:
                return ("3 sets × 10 reps/side @ 15 lb", "Rest 60s · Crisp lockouts & core control")
        return ("3 sets × 12-15 reps", "Rest 60s · Slow 2-second negative")

    elif kind == "hiit":
        if is_kb:
            if "swing" in name:
                return ("5 rounds: 40s work / 20s rest @ 20 lb", "Maximum hip snap on every rep")
            return ("4 rounds: 30s work / 30s rest @ 10-15 lb", "Continuous rhythmic cadence")
        return ("4 rounds: 40s work / 20s rest", "High speed & steady breathing")

    elif kind == "metcon":
        if is_kb:
            return ("4 rounds: 12 reps @ 15 lb", "Minimal rest between exercises · 90s round rest")
        return ("4 rounds: 15 reps", "Continuous flow")

    elif kind == "zone2":
        return ("3 sets × 20 steady reps", "Maintain conversational breathing pace")

    else:  # recovery
        return ("3 sets × 60s hold / flow", "Deep belly breathing into tight fascial lines")


def generate_plan(target_date: dt.date) -> Plan:
    """
    Generates a deterministic workout plan for a given calendar date.
    Calculates periodization kind, filters equipment (including 10, 15, 20 lb KBs),
    and enforces anti-repeat window.
    """
    db = get_engine_db()
    days_since_epoch = (target_date - EPOCH_DATE).days
    cycle_day = days_since_epoch % len(CYCLE)
    kind = CYCLE[cycle_day]

    # Deterministic seed so plan remains stable across page refreshes
    seed_val = int(target_date.strftime("%Y%m%d"))
    rng = random.Random(seed_val)

    # History anti-repeat filtering
    recent_used_ids: Set[str] = set()
    for back in range(1, ANTI_REPEAT_DAYS + 1):
        prev_date = target_date - dt.timedelta(days=back)
        prev_seed = int(prev_date.strftime("%Y%m%d"))
        prev_rng = random.Random(prev_seed)
        available_prev = db.filter_moves(MY_EQUIPMENT)
        if available_prev:
            sampled = prev_rng.sample(available_prev, min(len(available_prev), 4))
            recent_used_ids.update(m.db_id for m in sampled)

    pool = [m for m in db.filter_moves(MY_EQUIPMENT) if m.db_id not in recent_used_ids]
    if len(pool) < 4:
        pool = db.filter_moves(MY_EQUIPMENT)

    if kind == "strength":
        title = "Functional Strength & Kettlebell Hypertrophy"
        focus = "Progressive overload with 10, 15 & 20 lb kettlebells and bodyweight tension"
        why = "Stimulates lean muscle retention, raises resting metabolic rate, and reinforces connective tissue."
        minutes = 45
        met_val = 5.5
        
        kb_moves = [m for m in pool if "kettlebell" in m.equipment.lower() or "kb_" in m.db_id]
        main_picks = rng.sample(kb_moves, min(len(kb_moves), 3)) if kb_moves else []
        remaining = [m for m in pool if m not in main_picks]
        extra_picks = rng.sample(remaining, min(len(remaining), 2))
        chosen_moves = main_picks + extra_picks

        blocks = [
            Block(
                title="Block A · Movement Prep & Activation",
                subtitle="Prime hips, thoracic spine, and shoulder joint stabilizers",
                items=[Item(chosen_moves[0], "2 sets × 10 reps", "Active mobility & core priming")]
            ),
            Block(
                title="Block B · Primary Kettlebell Strength",
                subtitle="Heavy hinges, goblet squats, and unilateral loaded carries",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen_moves[1:4]]
            ),
            Block(
                title="Block C · Core & Posterior Armor",
                subtitle="Anti-rotation and rotational endurance",
                items=[Item(chosen_moves[-1], *format_dose_and_detail(chosen_moves[-1], kind))]
            )
        ]

    elif kind == "hiit":
        title = "Kettlebell Swing & Cardiovascular Interval Blast"
        focus = "High velocity hip snap (20 lb), explosive transitions, and anaerobic threshold"
        why = "Ignites excess post-exercise oxygen consumption (EPOC) to accelerate 24-hour fat oxidation."
        minutes = 30
        met_val = 9.0

        shuffled = list(pool)
        rng.shuffle(shuffled)
        picks = shuffled[:4]

        blocks = [
            Block(
                title="Dynamic Warmup",
                subtitle="Elevate heart rate and grease groove patterns",
                items=[Item(picks[0], "3 minutes continuous flow", "Build steady body heat")]
            ),
            Block(
                title="High Intensity Interval Circuit (4-5 Rounds)",
                subtitle="Alternate ballistic kettlebell work with bodyweight tempo",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in picks[1:]]
            )
        ]

    elif kind == "metcon":
        title = "Metabolic Conditioning Kettlebell Complex"
        focus = "Continuous work capacity, lactate buffering, and full-body synergy"
        why = "Bridges strength and cardiovascular capacity without catabolic muscle loss."
        minutes = 35
        met_val = 8.0

        shuffled = list(pool)
        rng.shuffle(shuffled)
        picks = shuffled[:4]

        blocks = [
            Block(
                title="Warmup Primer",
                subtitle="Lubricate joints and rehearse rack position",
                items=[Item(picks[0], "2 sets × 8 reps", "Smooth control")]
            ),
            Block(
                title="The Complex (Density Rounds)",
                subtitle="Move directly from exercise to exercise; rest 90s only at end of round",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in picks[1:]]
            )
        ]

    elif kind == "zone2":
        title = "Aerobic Base & Steady-State Conditioning"
        focus = "Sub-lactate threshold cadence, mitochondrial density, and fat oxidation"
        why = "Builds the aerobic engine required to recover quickly between heavy strength sets."
        minutes = 40
        met_val = 6.5

        shuffled = list(pool)
        rng.shuffle(shuffled)
        picks = shuffled[:3]

        blocks = [
            Block(
                title="Aerobic Movement Circuit",
                subtitle="Keep heart rate strictly in Zone 2 (nasal breathing / conversational pace)",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in picks]
            )
        ]

    else:  # recovery
        title = "Joint Mobility & Parasympathetic Decompression"
        focus = "Hip capsule mobility, spinal articulation, and tissue restoration"
        why = "Downregulates nervous system stress and prepares neuromuscular system for the next cycle."
        minutes = 25
        met_val = 2.8

        rec_moves = [m for m in db.filter_moves(MY_EQUIPMENT, category="stretching")] or pool[:3]
        picks = rec_moves[:3]

        blocks = [
            Block(
                title="Restorative Flow",
                subtitle="Hold each posture with calm nasal breathing",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in picks]
            )
        ]

    # MET-based calorie estimate calculation
    kg_weight = BODY_WEIGHT_LB * 0.453592
    hours = minutes / 60.0
    baseline_kcal = int(met_val * kg_weight * hours)
    lo = int(baseline_kcal * 0.90)
    hi = int(baseline_kcal * 1.15)

    return Plan(
        date=target_date,
        kind=kind,
        title=title,
        focus=focus,
        why=why,
        minutes=minutes,
        calorie_estimate=(lo, hi),
        cycle_day=cycle_day,
        blocks=blocks
    )


def upcoming(start_date: dt.date, num_days: int = 7) -> List[PlanSummary]:
    """Generates preview summaries for the upcoming N days for the top outlook bar."""
    summaries = []
    for i in range(num_days):
        d = start_date + dt.timedelta(days=i)
        p = generate_plan(d)
        summaries.append(PlanSummary(date=d, kind=p.kind, title=p.title))
    return summaries
