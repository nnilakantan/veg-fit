"""
engine.py - Core Training Engine for VEG-FIT Pro
Handles balanced mixed-modality programming (Dumbbells, Bodyweight, Cardio & Kettlebells),
9-day periodization cycling, and daily plan generation.
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
CYCLE: List[str] = [
    "strength",   # Day 1: Strength - Upper Body Push/Pull & Core Armor
    "hiit",       # Day 2: HIIT - Cardio Intervals & Athletic Conditioning
    "zone2",      # Day 3: Zone 2 - Aerobic Base & Steady State
    "strength",   # Day 4: Strength - Lower Body Power & Posterior Chain
    "metcon",     # Day 5: Metcon - Metabolic Density & Full-Body Circuit
    "zone2",      # Day 6: Zone 2 - Low-Impact Cardiovascular Flush
    "strength",   # Day 7: Strength - Total Body Functional Hypertrophy
    "hiit",       # Day 8: HIIT - Boxing & High-Velocity Conditioning
    "recovery",   # Day 9: Active Recovery - Joint Mobility & Decompression
]

# Equipment inventory: Dumbbells, bodyweight, and supplemental kettlebells
MY_EQUIPMENT: Set[str] = {
    "body_only",
    "dumbbell",
    "kettlebells",
}

MY_KETTLEBELLS: List[int] = [10, 15, 20]  # Available bell weights (lbs)
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
# Balanced Exercise Library (Dumbbells, Calisthenics, Cardio & Kettlebells)
# ----------------------------------------------------------------------------------
BASE_GITHUB_IMG = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises"

CURATED_EXERCISES: List[Dict] = [
    # --- Dumbbell Staples (Strength & Hypertrophy Foundation) ---
    {
        "id": "db_bench_press",
        "name": "Dumbbell Floor / Bench Press",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["chest", "triceps"],
        "secondaryMuscles": ["shoulders"],
        "cue": "Retract scapulae firmly; lower dumbbells at 45-degree elbow tuck and press to ceiling.",
        "note": "Primary horizontal push for chest and arm development (20-25 lb dumbbells).",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+bench+press+proper+form",
        "instructions": [
            "Lie on flat bench or floor holding dumbbells at chest level.",
            "Set feet firmly, retract shoulder blades, and press weights smoothly upward.",
            "Lower under a 2-second tempo until elbows gently tap floor or chest reaches full stretch.",
            "Drive up without clanking weights at top."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Dumbbell_Bench_Press/0.jpg",
            f"{BASE_GITHUB_IMG}/Dumbbell_Bench_Press/1.jpg"
        ]
    },
    {
        "id": "db_bent_over_row",
        "name": "Dumbbell Bent-Over Row",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["lats", "rhomboids"],
        "secondaryMuscles": ["biceps", "lower back"],
        "cue": "Hinge hips back with a flat spine; pull elbows toward your hip pockets and squeeze upper back.",
        "note": "Compound back builder. Resist jerking the weights with your torso.",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+bent+over+row+technique",
        "instructions": [
            "Hinge at hips with knees softly bent until torso is roughly 45 degrees to floor.",
            "Hold dumbbells with neutral or overhand grip.",
            "Pull dumbbells up towards ribs, leading with elbows.",
            "Squeeze lats at apex for 1 second, then lower with control."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Bent_Over_Two-Arm_Dumbbell_Row/0.jpg",
            f"{BASE_GITHUB_IMG}/Bent_Over_Two-Arm_Dumbbell_Row/1.jpg"
        ]
    },
    {
        "id": "db_overhead_press",
        "name": "Dumbbell Seated / Standing Shoulder Press",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["shoulders", "triceps"],
        "secondaryMuscles": ["upper chest", "core"],
        "cue": "Brace abs and glutes; press vertically without arching your lower back.",
        "note": "Vertical push staple for shoulder deltoids and overhead stability.",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+shoulder+press+form",
        "instructions": [
            "Bring dumbbells to shoulder level with elbows slightly in front of body.",
            "Press weights straight overhead until arms are extended.",
            "Lower smoothly back to shoulder height."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Dumbbell_Shoulder_Press/0.jpg",
            f"{BASE_GITHUB_IMG}/Dumbbell_Shoulder_Press/1.jpg"
        ]
    },
    {
        "id": "db_thrusters",
        "name": "Dumbbell Thrusters",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["quadriceps", "shoulders"],
        "secondaryMuscles": ["glutes", "triceps", "core"],
        "cue": "Squat deep and use explosive leg drive to pop dumbbells overhead in one fluid motion.",
        "note": "Full-body metabolic power builder. High cardiovascular demand.",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+thruster+form",
        "instructions": [
            "Hold dumbbells racked at shoulders, feet shoulder-width apart.",
            "Squat down until thighs reach parallel.",
            "Explode upward through heels, transferring momentum straight into overhead press."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Push_Press/0.jpg",
            f"{BASE_GITHUB_IMG}/Push_Press/1.jpg"
        ]
    },
    {
        "id": "db_walking_lunges",
        "name": "Dumbbell Walking Lunges",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["quadriceps", "glutes"],
        "secondaryMuscles": ["hamstrings", "calves", "forearms"],
        "cue": "Take a generous forward step; lower trailing knee softly to ground, keeping chest proud.",
        "note": "Unilateral leg developer and balance builder.",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+walking+lunge",
        "instructions": [
            "Hold dumbbells by your sides with arms hanging long.",
            "Step forward into a lunge, lowering hips until both knees form 90-degree angles.",
            "Drive through front heel to step into the next repetition."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Dumbbell_Lunges/0.jpg",
            f"{BASE_GITHUB_IMG}/Dumbbell_Lunges/1.jpg"
        ]
    },
    {
        "id": "db_bicep_hammer_curls",
        "name": "Dumbbell Neutral-Grip Hammer Curls",
        "equipment": "dumbbell",
        "category": "strength",
        "primaryMuscles": ["biceps", "forearms"],
        "secondaryMuscles": ["brachialis"],
        "cue": "Pin elbows to your ribs; curl with palms facing each other to target brachialis and forearm grip.",
        "note": "Arm isolation to build elbow joint resilience and pulling power.",
        "video_url": "https://www.youtube.com/results?search_query=dumbbell+hammer+curls",
        "instructions": [
            "Stand with dumbbells at sides, palms facing inwards.",
            "Curl weights upwards while keeping upper arms fixed.",
            "Lower slowly under a 2-second negative."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Hammer_Curls/0.jpg",
            f"{BASE_GITHUB_IMG}/Hammer_Curls/1.jpg"
        ]
    },

    # --- Bodyweight Calisthenics & Core ---
    {
        "id": "bw_pushups",
        "name": "Standard Push-Up (Tempo)",
        "equipment": "body_only",
        "category": "strength",
        "primaryMuscles": ["chest", "triceps"],
        "secondaryMuscles": ["shoulders", "core"],
        "cue": "Body forms a rigid plank from crown to heels; elbows track at 45-degree angle.",
        "note": "Control the 2-second eccentric phase for maximum chest hypertrophy.",
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
        "id": "bw_burpees",
        "name": "Athletic Burpee / Sprawl",
        "equipment": "body_only",
        "category": "cardio",
        "primaryMuscles": ["quadriceps", "chest"],
        "secondaryMuscles": ["shoulders", "calves", "abdominals"],
        "cue": "Drop hips back, kick feet to plank, drop chest softly, snap feet to hands and jump.",
        "note": "Metabolic burner for HIIT & Metcon days.",
        "video_url": "https://www.youtube.com/results?search_query=burpee+technique",
        "instructions": [
            "Place hands on floor, kick feet back into plank.",
            "Lower chest to ground, press up and jump feet back towards hands.",
            "Jump explosively upwards with hands overhead."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Burpee/0.jpg",
            f"{BASE_GITHUB_IMG}/Burpee/1.jpg"
        ]
    },
    {
        "id": "bw_hollow_body_hold",
        "name": "Hollow Body Core Hold",
        "equipment": "body_only",
        "category": "strength",
        "primaryMuscles": ["abdominals"],
        "secondaryMuscles": ["lower back", "hip flexors"],
        "cue": "Press lower back firmly into the floor with zero gap; point toes forward.",
        "note": "Gymnastic core foundation. Scale by bending knees if lower back arches.",
        "video_url": "https://www.youtube.com/results?search_query=hollow+body+hold",
        "instructions": [
            "Lie flat on back with arms extended overhead and legs straight.",
            "Lift shoulders and legs slightly off floor, tucking pelvis into floor.",
            "Hold position while breathing rhythmically."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Hollow_rock/0.jpg",
            f"{BASE_GITHUB_IMG}/Hollow_rock/1.jpg"
        ]
    },
    {
        "id": "bw_plank_taps",
        "name": "Plank Shoulder Taps",
        "equipment": "body_only",
        "category": "strength",
        "primaryMuscles": ["abdominals", "obliques"],
        "secondaryMuscles": ["shoulders", "glutes"],
        "cue": "Widen feet slightly to anchor base; touch opposite shoulder without rocking hips.",
        "note": "Anti-rotational core strength.",
        "video_url": "https://www.youtube.com/results?search_query=plank+shoulder+taps",
        "instructions": [
            "Start in tall push-up plank position.",
            "Slowly lift right hand to tap left shoulder, keeping hips completely level.",
            "Return and repeat on other side."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Plank/0.jpg",
            f"{BASE_GITHUB_IMG}/Plank/1.jpg"
        ]
    },

    # --- Cardio / Machine / Boxing Conditioning ---
    {
        "id": "cardio_treadmill_intervals",
        "name": "Treadmill Intervals (1 min Hard / 2 min Walk)",
        "equipment": "body_only",
        "category": "cardio",
        "primaryMuscles": ["quadriceps", "hamstrings", "calves"],
        "secondaryMuscles": ["heart"],
        "cue": "Sprint with upright posture and forefoot strike; use recovery walks to bring heart rate down.",
        "note": "High-intensity aerobic conditioning and VO2 max builder.",
        "video_url": "https://www.youtube.com/results?search_query=treadmill+interval+workout",
        "instructions": [
            "Warm up with 3 minutes easy walking.",
            "Perform interval rounds alternating between fast run and recovery walk.",
            "Cool down with 2 minutes flat walk."
        ],
        "images": []
    },
    {
        "id": "cardio_rowing_steady",
        "name": "Rowing Machine Steady State / Intervals",
        "equipment": "body_only",
        "category": "cardio",
        "primaryMuscles": ["lats", "hamstrings", "quadriceps"],
        "secondaryMuscles": ["core", "biceps"],
        "cue": "Legs push first, then body leans back, then arms pull. Reverse arms, body, legs on return.",
        "note": "Zero-impact total-body cardio. Fantastic for Zone 2 aerobic base.",
        "video_url": "https://www.youtube.com/results?search_query=rowing+machine+technique",
        "instructions": [
            "Strap feet in, grab handle with overhand grip.",
            "Drive legs explosively, swing torso open to 11 o'clock, and pull handle to sternum.",
            "Glide forward smoothly to catch position."
        ],
        "images": []
    },
    {
        "id": "cardio_heavy_bag",
        "name": "Heavy Bag Boxing Rounds",
        "equipment": "body_only",
        "category": "cardio",
        "primaryMuscles": ["shoulders", "core", "calves"],
        "secondaryMuscles": ["back", "chest"],
        "cue": "Pivot back foot on the cross; snap punches out and immediately back to guard.",
        "note": "High-energy shoulder stamina and rotational core conditioning.",
        "video_url": "https://www.youtube.com/results?search_query=heavy+bag+boxing+workout",
        "instructions": [
            "Assume boxing stance with hands up guarding chin.",
            "Throw sharp punch combinations (Jab-Cross-Hook) with constant footwork.",
            "Keep core braced and exhale sharply with each strike."
        ],
        "images": []
    },

    # --- Kettlebells (Targeted Accessories & Power Enhancers: 10, 15, 20 lb) ---
    {
        "id": "kb_two_arm_swing",
        "name": "Kettlebell Two-Arm Swing",
        "equipment": "kettlebells",
        "category": "strength",
        "primaryMuscles": ["glutes", "hamstrings", "lower back"],
        "secondaryMuscles": ["shoulders", "abs", "forearms"],
        "cue": "Hinge at the hips with a flat back; snap hips violently forward. Power comes from glutes, not arms.",
        "note": "Explosive posterior chain power. Great with your 20 lb bell.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+two+arm+swing+form",
        "instructions": [
            "Stand with feet slightly wider than shoulder-width, kettlebell on floor 1 foot in front.",
            "Hinge hips back with a soft knee bend, grabbing handle with both hands.",
            "Hike bell back between legs like a football center.",
            "Drive feet through floor and snap hips forward to full vertical standing lock.",
            "Let bell float to chest height on momentum; guide it smoothly back into hinge."
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
        "note": "Ideal quad and hip mobility builder with your 15 lb or 20 lb bell.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+goblet+squat+technique",
        "instructions": [
            "Hold kettlebell close to chest by horns with elbows tucked.",
            "Set feet shoulder-width apart, toes turned slightly out.",
            "Descend by sending hips back and spreading knees.",
            "Reach parallel or deeper with upright torso, then drive out through mid-foot."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Goblet_Squat/0.jpg",
            f"{BASE_GITHUB_IMG}/Goblet_Squat/1.jpg"
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
        "note": "Pre-workout shoulder lubricating drill. Best with your 10 lb bell.",
        "video_url": "https://www.youtube.com/results?search_query=kettlebell+halo+form",
        "instructions": [
            "Hold bell upside down by horns at upper chest level.",
            "Brace core firmly and orbit bell closely around your head.",
            "Keep torso rigid without swaying; alternate clockwise and counterclockwise."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Kettlebell_Halo/0.jpg",
            f"{BASE_GITHUB_IMG}/Kettlebell_Halo/1.jpg"
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
        "note": "Heavy unilateral core anti-flexion with your 20 lb bell.",
        "video_url": "https://www.youtube.com/results?search_query=suitcase+carry+kettlebell",
        "instructions": [
            "Deadlift bell with one hand by your side like a heavy suitcase.",
            "Keep shoulders level and posture tall; walk smoothly for distance or time.",
            "Turn around, switch hands and repeat."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Farmers_Walk/0.jpg",
            f"{BASE_GITHUB_IMG}/Farmers_Walk/1.jpg"
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
        "note": "Functional shoulder stability and full-body synergy with your 10 lb bell.",
        "video_url": "https://www.youtube.com/results?search_query=turkish+get+up+step+by+step",
        "instructions": [
            "Lie flat with bell pressed straight up in right arm; right knee bent.",
            "Roll up diagonally onto left forearm, then palm.",
            "Bridge hips up, sweep leg under into kneeling lunge, and stand tall.",
            "Reverse each milestone carefully back to floor."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Turkish_Get_Up/0.jpg",
            f"{BASE_GITHUB_IMG}/Turkish_Get_Up/1.jpg"
        ]
    },

    # --- Mobility & Restorative Stretches ---
    {
        "id": "rec_world_greatest_stretch",
        "name": "World's Greatest Hip & Thoracic Stretch",
        "equipment": "body_only",
        "category": "stretching",
        "primaryMuscles": ["hip flexors", "hamstrings", "lats"],
        "secondaryMuscles": ["thoracic spine", "glutes"],
        "cue": "Elbow down inside front instep, rotate upper arm to ceiling, exhale into stretch.",
        "note": "Joint opener before lifting or on active recovery days.",
        "video_url": "https://www.youtube.com/results?search_query=worlds+greatest+stretch",
        "instructions": [
            "Step into deep forward lunge with hands inside front foot.",
            "Drop inside elbow toward floor, pause for 2 seconds.",
            "Reach arm to ceiling, rotating upper spine.",
            "Straighten front leg to stretch hamstring, then switch sides."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Groin_Stretch/0.jpg",
            f"{BASE_GITHUB_IMG}/Groin_Stretch/1.jpg"
        ]
    },
    {
        "id": "rec_cat_cow",
        "name": "Cat-Cow Spinal Articulation",
        "equipment": "body_only",
        "category": "stretching",
        "primaryMuscles": ["lower back", "spine"],
        "secondaryMuscles": ["abdominals", "neck"],
        "cue": "Synchronize breath with spinal segment movement; inhale to arch, exhale to round.",
        "note": "Decompresses lumbar spine and resets posture.",
        "video_url": "https://www.youtube.com/results?search_query=cat+cow+stretch",
        "instructions": [
            "Start on hands and knees with wrists under shoulders, knees under hips.",
            "Inhale, drop belly toward floor and lift chest and tailbone (Cow).",
            "Exhale, round spine upward towards ceiling and tuck chin (Cat)."
        ],
        "images": [
            f"{BASE_GITHUB_IMG}/Cat_Cow/0.jpg",
            f"{BASE_GITHUB_IMG}/Cat_Cow/1.jpg"
        ]
    }
]

# ----------------------------------------------------------------------------------
# Exercise Database Manager
# ----------------------------------------------------------------------------------
class ExerciseDB:
    def __init__(self):
        self._exercises: Dict[str, Move] = {}
        self.status: str = "Ready (Curated)"

    def load(self, json_path: Optional[str] = None):
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

        self.status = f"{len(self._exercises)} exercises indexed (Dumbbells, Bodyweight & Kettlebells)"

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
                cue=item.get("instructions", ["Focus on form."])[0] if item.get("instructions") else "Move with control.",
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
    name = move.name.lower()
    is_kb = "kettlebell" in name or "kettlebell" in move.equipment.lower() or "kb_" in move.db_id
    is_db = "dumbbell" in name or "dumbbell" in move.equipment.lower() or "db_" in move.db_id

    if kind == "strength":
        if is_kb:
            if any(w in name for w in ["swing", "deadlift", "squat", "carry"]):
                return ("3-4 sets × 12 reps @ 20 lb", "Rest 75s · Explosive hip extension")
            elif any(w in name for w in ["halo", "windmill", "turkish"]):
                return ("3 sets × 8 reps/side @ 10 lb", "Rest 60s · Shoulder stability & packed lats")
            else:
                return ("3 sets × 10 reps @ 15 lb", "Rest 60s · Crisp lockouts")
        elif is_db:
            if "bench" in name or "row" in name or "press" in name:
                return ("3-4 sets × 8-10 reps @ 20-25 lb", "Rest 75s · Control the eccentric phase")
            elif "thruster" in name or "lunge" in name:
                return ("3 sets × 10 reps @ 15-20 lb", "Rest 60s · Steady tempo")
            else:
                return ("3 sets × 12 reps @ 15 lb", "Rest 60s · Squeeze at top")
        else:
            return ("3 sets × 12-15 reps", "Rest 60s · Full range of motion")

    elif kind == "hiit":
        if is_kb:
            return ("5 rounds: 40s work / 20s rest @ 20 lb", "Maximum hip snap on swings")
        elif is_db:
            return ("4 rounds: 30s work / 30s rest @ 15 lb", "Crisp athletic cadence")
        elif "treadmill" in name or "interval" in name:
            return ("8 rounds: 1 min hard / 2 min walk", "Maintain 85-90% effort during work interval")
        elif "bag" in name or "boxing" in name:
            return ("4 rounds: 3 min work / 1 min rest", "Active combinations and swift footwork")
        else:
            return ("4 rounds: 40s work / 20s rest", "High speed & steady breathing")

    elif kind == "metcon":
        if is_kb:
            return ("4 rounds: 12 reps @ 15 lb", "Smooth transitions in the circuit")
        elif is_db:
            return ("4 rounds: 10 reps @ 20 lb", "Move smoothly under control")
        else:
            return ("4 rounds: 15 reps", "Continuous flow")

    elif kind == "zone2":
        if "row" in name:
            return ("20-30 min steady row at 60% capacity", "Nasal breathing / conversational pace")
        elif "treadmill" in name or "walk" in name:
            return ("30-40 min incline treadmill walk", "Keep heart rate steady under lactate threshold")
        else:
            return ("3 sets × 20 steady reps", "Light active movement")

    else:  # recovery
        return ("3 sets × 60s hold / flow", "Deep diaphragmatic breathing into tight lines")


def generate_plan(target_date: dt.date) -> Plan:
    db = get_engine_db()
    days_since_epoch = (target_date - EPOCH_DATE).days
    cycle_day = days_since_epoch % len(CYCLE)
    kind = CYCLE[cycle_day]

    seed_val = int(target_date.strftime("%Y%m%d"))
    rng = random.Random(seed_val)

    # Anti-repeat tracking from recent sessions
    recent_used_ids: Set[str] = set()
    for back in range(1, ANTI_REPEAT_DAYS + 1):
        prev_date = target_date - dt.timedelta(days=back)
        prev_seed = int(prev_date.strftime("%Y%m%d"))
        prev_rng = random.Random(prev_seed)
        all_moves = db.filter_moves(MY_EQUIPMENT)
        if all_moves:
            sampled = prev_rng.sample(all_moves, min(len(all_moves), 4))
            recent_used_ids.update(m.db_id for m in sampled)

    pool = [m for m in db.filter_moves(MY_EQUIPMENT) if m.db_id not in recent_used_ids]
    if len(pool) < 6:
        pool = db.filter_moves(MY_EQUIPMENT)

    kb_pool = [m for m in pool if m.equipment == "kettlebells"]
    db_pool = [m for m in pool if m.equipment == "dumbbell"]
    bw_pool = [m for m in pool if m.equipment == "body_only"]

    all_db = [m for m in db.filter_moves(MY_EQUIPMENT) if m.equipment == "dumbbell"]
    all_bw = [m for m in db.filter_moves(MY_EQUIPMENT) if m.equipment == "body_only"]
    all_kb = [m for m in db.filter_moves(MY_EQUIPMENT) if m.equipment == "kettlebells"]

    if len(db_pool) < 2: db_pool = all_db
    if len(bw_pool) < 2: bw_pool = all_bw
    if len(kb_pool) < 1: kb_pool = all_kb

    used_today: Set[str] = set()

    def get_moves(source_pool: List[Move], count: int, preferred_keywords: Optional[List[str]] = None) -> List[Move]:
        available = [m for m in source_pool if m.db_id not in used_today]
        if not available:
            available = source_pool

        if preferred_keywords:
            matched = [m for m in available if any(k in m.name.lower() or k in m.db_id.lower() for k in preferred_keywords)]
            if matched:
                available = matched

        k = min(count, len(available))
        picked = rng.sample(available, k) if k > 0 else []
        for m in picked:
            used_today.add(m.db_id)
        return picked

    if kind == "strength":
        if cycle_day == 0:
            title = "Upper Body Push/Pull & Core Armor"
            focus = "Dumbbell presses, bent-over rows, and core stabilization"
            why = "Builds dense upper-body musculature while protecting the shoulder girdle."
            warmup = get_moves(all_bw, 1, ["stretch", "pushup", "taps"])
            main_db = get_moves(db_pool, 2, ["bench", "row", "press", "curl"])
            core = get_moves(bw_pool, 1, ["hollow", "plank", "twist", "climbers"])
            kb_acc = get_moves(kb_pool, 1, ["halo", "carry", "twist"])  # 1 KB accessory
            chosen = warmup + main_db + core + kb_acc
        elif cycle_day == 3:
            title = "Lower Body Power & Posterior Chain"
            focus = "Dumbbell lunges, air squats, and explosive kettlebell hip hinges"
            why = "Stimulates glute and hamstring power to bulletproof knees and hips."
            warmup = get_moves(all_bw, 1, ["squat", "stretch"])
            lunge_db = get_moves(db_pool, 1, ["lunge", "thruster"])
            kb_power = get_moves(kb_pool, 1, ["swing", "squat", "deadlift"])  # 1 KB compound
            extra_db = get_moves(db_pool, 1)
            core = get_moves(bw_pool, 1, ["hollow", "plank"])
            chosen = warmup + lunge_db + kb_power + extra_db + core
        else:  # cycle_day == 6
            title = "Total Body Functional Hypertrophy"
            focus = "Full-body compound dumbbell sequence paired with calisthenics"
            why = "Maximizes motor unit recruitment across all kinetic chain segments."
            warmup = get_moves(all_bw, 1, ["squat", "stretch"])
            main_db = get_moves(db_pool, 2)
            calisthenics = get_moves(bw_pool, 1, ["pushup", "burpee"])
            kb_finisher = get_moves(kb_pool, 1, ["carry", "swing", "clean"])  # 1 KB finisher
            chosen = warmup + main_db + calisthenics + kb_finisher

        minutes = 45
        met_val = 5.5

        blocks = [
            Block(
                title="Block A · Movement Prep",
                subtitle="Light mobility and activation",
                items=[Item(chosen[0], "2 sets × 10 reps", "Joint lubrication and muscle activation")]
            ),
            Block(
                title="Block B · Primary Compound Strength",
                subtitle="Dumbbell foundation complemented by functional loading",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen[1:3]]
            ),
            Block(
                title="Block C · Functional Accessory & Core",
                subtitle="Core stabilization and unilateral work",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen[3:]]
            )
        ]

    elif kind == "hiit":
        if cycle_day == 1:
            title = "Cardio Intervals & Athletic Conditioning"
            focus = "Treadmill or sprint intervals paired with burpees and kettlebell swings"
            why = "Elevates heart rate recovery velocity and spikes post-workout metabolic burn."
            warmup = get_moves(all_bw, 1, ["stretch", "squat"])
            cardio_station = get_moves(bw_pool, 1, ["treadmill", "climbers"])
            kb_station = get_moves(kb_pool, 1, ["swing"])  # 1 KB power interval
            burpee_station = get_moves(bw_pool, 1, ["burpee", "pushup"])
            chosen = warmup + cardio_station + kb_station + burpee_station
        else:  # cycle_day == 7
            title = "Heavy Bag Boxing & Explosive Intervals"
            focus = "Punching bag rounds, bodyweight tempo, and power conditioning"
            why = "Builds rotational core endurance and fast-twitch shoulder power."
            warmup = get_moves(all_bw, 1, ["stretch", "taps"])
            bag_station = get_moves(bw_pool, 1, ["bag", "climbers"])
            db_station = get_moves(db_pool, 1, ["thruster", "lunge"])
            kb_station = get_moves(kb_pool, 1, ["swing", "squat"])  # 1 KB station
            chosen = warmup + bag_station + db_station + kb_station

        minutes = 30
        met_val = 9.0

        blocks = [
            Block(
                title="Warmup Flow",
                subtitle="Dynamic stretch and temperature elevation",
                items=[Item(chosen[0], "3 minutes continuous flow", "Gradually raise core temperature")]
            ),
            Block(
                title="High-Intensity Interval Circuit",
                subtitle="Alternate explosive power stations with short rest windows",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen[1:]]
            )
        ]

    elif kind == "metcon":
        title = "Metabolic Density & Full-Body Circuit"
        focus = "Continuous mixed-modality circuit (Dumbbells, Bodyweight & 1 Kettlebell station)"
        why = "Increases work capacity and muscular endurance while burning calories."
        minutes = 35
        met_val = 8.0

        warmup = get_moves(all_bw, 1, ["stretch", "squat"])
        d_move = get_moves(db_pool, 1, ["thruster", "row", "lunge"])
        b_move = get_moves(bw_pool, 1, ["pushup", "burpee", "taps"])
        k_move = get_moves(kb_pool, 1, ["clean", "squat", "swing"])  # 1 KB station
        chosen = warmup + d_move + b_move + k_move

        blocks = [
            Block(
                title="Movement Primer",
                subtitle="Light rehearsal of circuit patterns",
                items=[Item(chosen[0], "2 sets × 8 reps", "Warm up joints and rehearse rhythm")]
            ),
            Block(
                title="The Mixed Circuit (4 Rounds)",
                subtitle="Move smoothly through all stations; rest 90 seconds only between full rounds",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen[1:]]
            )
        ]

    elif kind == "zone2":
        title = "Aerobic Base & Steady-State Conditioning"
        focus = "Steady rowing, incline treadmill walk, or continuous aerobic flow (Zero heavy loading)"
        why = "Develops mitochondrial volume and capillary density for superior recovery."
        minutes = 40
        met_val = 6.5

        # Pure aerobic steady state: No kettlebells
        chosen = get_moves(all_bw, 2, ["rowing", "treadmill", "squat"])

        blocks = [
            Block(
                title="Aerobic Cardiovascular Engine",
                subtitle="Keep heart rate strictly in Zone 2 (nasal breathing / conversational pace)",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen]
            )
        ]

    else:  # recovery
        title = "Joint Mobility & Parasympathetic Decompression"
        focus = "Hip capsule mobility, spinal articulation, and tissue restoration (Restorative flow)"
        why = "Downregulates the nervous system and facilitates tissue remodeling."
        minutes = 25
        met_val = 2.8

        # Pure restorative mobility: No kettlebells
        stretches = [m for m in db.filter_moves(MY_EQUIPMENT, category="stretching")]
        chosen = get_moves(stretches or all_bw, 2, ["stretch", "cat"])

        blocks = [
            Block(
                title="Restorative Mobility Flow",
                subtitle="Hold each position with slow nasal breathing",
                items=[Item(m, *format_dose_and_detail(m, kind)) for m in chosen]
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
    summaries = []
    for i in range(num_days):
        d = start_date + dt.timedelta(days=i)
        p = generate_plan(d)
        summaries.append(PlanSummary(date=d, kind=p.kind, title=p.title))
    return summaries
