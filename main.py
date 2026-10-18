import datetime as dt
import streamlit as st

from engine import (
    ANTI_REPEAT_DAYS,
    BODY_WEIGHT_LB,
    CYCLE,
    MY_EQUIPMENT,
    Block,
    ExerciseDB,
    Item,
    Plan,
    generate_plan,
    upcoming,
)

# ----------------------------------------------------------------------------------
# Setup & Config
# ----------------------------------------------------------------------------------
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥦", layout="centered")

# Kettlebell inventory specification (in lbs)
AVAILABLE_KETTLEBELLS = [10, 15, 20]

# Ensure kettlebell is incorporated into MY_EQUIPMENT if not already set in engine.py
if isinstance(MY_EQUIPMENT, set):
    MY_EQUIPMENT.add("kettlebells")
elif isinstance(MY_EQUIPMENT, list) and "kettlebells" not in MY_EQUIPMENT:
    MY_EQUIPMENT.append("kettlebells")

KIND_STYLE = {
    "strength": ("🏋️", "#4ade80", "STRENGTH"),
    "hiit": ("🔥", "#f87171", "HIIT"),
    "metcon": ("⚡", "#fbbf24", "METCON"),
    "zone2": ("🏃", "#60a5fa", "ZONE 2"),
    "recovery": ("🧘", "#a78bfa", "RECOVERY"),
}

@st.cache_resource
def get_db():
    db = ExerciseDB()
    db.load()
    return db

DB = get_db()

# Initialize session state for the date
if "date" not in st.session_state:
    st.session_state.date = dt.date.today()

# ----------------------------------------------------------------------------------
# Kettlebell Logic & Helpers
# ----------------------------------------------------------------------------------
def is_kettlebell_exercise(move) -> bool:
    """Detects if an exercise natively uses or focuses on kettlebells."""
    name = getattr(move, "name", "").lower()
    equipment = getattr(move, "equipment", "").lower()
    db_id = str(getattr(move, "db_id", "")).lower()
    return "kettlebell" in name or "kettlebell" in equipment or "kettlebell" in db_id


def is_kettlebell_compatible(move) -> bool:
    """Identifies exercises that can easily use kettlebells as a substitute."""
    name = getattr(move, "name", "").lower()
    compatible_keywords = [
        "goblet", "squat", "deadlift", "lunge", "row", "overhead press",
        "shoulder press", "clean", "swing", "snatch", "farmer", "carry",
        "halo", "windmill", "get-up", "russian twist", "renegade row"
    ]
    return any(kw in name for kw in compatible_keywords)


def suggest_kettlebell_weight(move, plan_kind: str = "strength") -> int:
    """
    Selects the best kettlebell weight (10, 15, or 20 lb) based on
    biomechanics, muscle recruitment, and session intensity.
    """
    name = getattr(move, "name", "").lower()

    # In fast-paced HIIT, Metcon, or Zone 2, favor 10 or 15 lb to protect form
    if plan_kind in ("hiit", "metcon", "zone2"):
        if any(w in name for w in ["swing", "deadlift", "squat", "carry"]):
            return 15
        return 10

    # Strength sessions (standard progressive loading)
    # 20 lb: Big posterior chain & leg movements
    if any(w in name for w in ["two-arm swing", "two-handed swing", "double swing", "deadlift", "sumo", "goblet squat", "squat", "farmer", "suitcase carry"]):
        return 20

    # 10 lb: Shoulder stability, overhead mobility, rotational core
    if any(w in name for w in ["halo", "windmill", "turkish", "get-up", "overhead", "press", "snatch", "lateral", "twist", "curl", "tricep"]):
        return 10

    # 15 lb: Unilateral ballistics, lunges, and pulls
    return 15

# ----------------------------------------------------------------------------------
# UI Helpers
# ----------------------------------------------------------------------------------
def pill_html(label: str, color: str = "#4ade80", bg: str = "#14301f") -> str:
    """Generates HTML for a styled pill badge to mimic Flet's UI."""
    return f'<span style="background-color: {bg}; color: {color}; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid {color}55; display: inline-block; margin: 2px;">{label}</span>'


def render_animated_images(frames: list[str]):
    """Replaces the Flet asyncio ticker with native CSS animations."""
    if not frames:
        return
    
    if len(frames) == 1:
        st.image(frames[0], use_container_width=True)
        return

    # Native CSS animation loop (swaps frames exactly like the 1.1s ticker)
    html = f"""
    <style>
    .anim-container {{
        position: relative;
        width: 100%;
        padding-top: 67.8%; /* Matches 280x190 aspect ratio */
        border-radius: 10px;
        overflow: hidden;
    }}
    .anim-container img {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        object-fit: cover;
    }}
    .frame-top {{ animation: fade 2.2s infinite; }}
    @keyframes fade {{
        0%, 49.9% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
    }}
    </style>
    <div class="anim-container">
        <img src="{frames[1]}" />
        <img src="{frames[0]}" class="frame-top" />
    </div>
    """
    st.components.v1.html(html, height=210)

# ----------------------------------------------------------------------------------
# Components
# ----------------------------------------------------------------------------------
def build_exercise_card(item: Item, plan_kind: str = "strength"):
    move = item.move
    frames = DB.images(move.db_id)
    steps = DB.instructions(move.db_id)
    muscles = DB.muscles(move.db_id)

    is_kb = is_kettlebell_exercise(move)
    can_kb = is_kettlebell_compatible(move)
    suggested_weight = suggest_kettlebell_weight(move, plan_kind)

    with st.container(border=True):
        col_media, col_details = st.columns([1, 2], gap="medium")
        
        # --- Left: Demo Media ---
        with col_media:
            if frames:
                st.markdown(pill_html("LOOPING DEMO" if len(frames) > 1 else "DEMO", "#4ade80", "#0f2a1a"), unsafe_allow_html=True)
                render_animated_images(frames)
            else:
                st.info("No stock photo. Use the video link.")

        # --- Right: Details ---
        with col_details:
            st.subheader(move.name, anchor=False)
            
            # Badges (Dose, details, muscles, equipment tags)
            badges = [pill_html(item.dose, "#4ade80", "#14301f")]
            if item.detail:
                badges.append(pill_html(item.detail, "#8b98a5", "#1c2230"))

            if is_kb:
                badges.append(pill_html("🔔 KETTLEBELL", "#f59e0b", "#2e1c0c"))
                badges.append(pill_html(f"Rec: {suggested_weight} lb", "#38bdf8", "#0c2438"))
            elif can_kb:
                badges.append(pill_html("🔔 KB Friendly", "#a78bfa", "#251b38"))
            
            for m in list(dict.fromkeys(muscles))[:6]:
                badges.append(pill_html(m.title(), "#93c5fd", "#16233a"))
                
            st.markdown(" ".join(badges), unsafe_allow_html=True)
            st.write("")  # spacing
            
            # Interactive Kettlebell Weight Selector
            if is_kb or can_kb:
                session_key = f"kb_weight_{move.db_id}_{st.session_state.date}"
                default_idx = AVAILABLE_KETTLEBELLS.index(suggested_weight) if suggested_weight in AVAILABLE_KETTLEBELLS else 1
                
                selected_weight = st.radio(
                    label="Kettlebell Weight:",
                    options=AVAILABLE_KETTLEBELLS,
                    index=default_idx,
                    format_func=lambda w: f"{w} lb" + (" (Recommended)" if w == suggested_weight else ""),
                    horizontal=True,
                    key=session_key,
                )

            # Coaching Cue & Notes
            st.markdown(f"💡 **Cue:** {move.cue}")
            if move.note:
                st.warning(f"⚠️ {move.note}", icon=None)

            # Video Link
            if move.video_url:
                st.link_button("▶️ Watch demo videos", move.video_url, type="primary")

            # Steps Expander
            if steps:
                with st.expander(f"Step-by-step technique ({len(steps)} steps)"):
                    for i, s in enumerate(steps, 1):
                        st.markdown(f"**{i}.** {s}")


def build_plan_view(plan: Plan):
    icon, colour, badge = KIND_STYLE[plan.kind]
    lo, hi = plan.calorie_estimate
    total_moves = sum(len(b.items) for b in plan.blocks)

    # --- Header ---
    with st.container(border=True):
        st.markdown(f"#### {icon} {plan.date.strftime('%A, %d %B %Y').upper()}")
        st.title(plan.title, anchor=False)
        st.caption(plan.focus)
        
        summary_badges = [
            pill_html(badge, colour, f"{colour}22"),
            pill_html(f"~{plan.minutes} min"),
            pill_html(f"~{lo}-{hi} kcal", "#fbbf24", "#2a2312"),
            pill_html(f"{total_moves} exercises", "#93c5fd", "#16233a"),
            pill_html(f"Cycle day {plan.cycle_day + 1}/{len(CYCLE)}", "#8b98a5", "#1c2230")
        ]
        st.markdown(" ".join(summary_badges), unsafe_allow_html=True)
        st.info(plan.why, icon="🧬")

    # --- Outlook ---
    with st.container(border=True):
        st.write("**NEXT 7 DAYS**")
        st.caption("Session type runs on a 9-day cycle, so it drifts against the weekdays. The same weekday only sees the same session once every 63 days.")
        
        cols = st.columns(7)
        for i, p in enumerate(upcoming(plan.date, 7)):
            with cols[i]:
                day_icon = KIND_STYLE[p.kind][0]
                day_badge = KIND_STYLE[p.kind][2]
                label = f"{p.date.strftime('%a')}\n{day_icon} {day_badge}"
                
                # Highlight today's equivalent
                btn_type = "primary" if p.date == plan.date else "secondary"
                if st.button(label, key=f"outlook_{p.date}", help=f"{p.date.strftime('%A %d %b')} - {p.title}", type=btn_type, use_container_width=True):
                    st.session_state.date = p.date
                    st.rerun()

    # --- Blocks ---
    for block in plan.blocks:
        st.divider()
        st.markdown(f"<h3 style='color: #4ade80;'>{block.title.upper()}</h3>", unsafe_allow_html=True)
        st.caption(block.subtitle)
        
        for item in block.items:
            build_exercise_card(item, plan_kind=plan.kind)

# ----------------------------------------------------------------------------------
# Main App Layout
# ----------------------------------------------------------------------------------
def main():
    # Top Bar Navigation
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown("## 🔥 VEG-FIT PRO")
        st.caption("Daily fat-loss training - built around your equipment")
    
    with cols[1]:
        nav_cols = st.columns(3)
        if nav_cols[0].button("⬅️", help="Previous Day"):
            st.session_state.date -= dt.timedelta(days=1)
            st.rerun()
        if nav_cols[1].button("Today", type="primary"):
            st.session_state.date = dt.date.today()
            st.rerun()
        if nav_cols[2].button("➡️", help="Next Day"):
            st.session_state.date += dt.timedelta(days=1)
            st.rerun()

    # Equipment readout
    equip_badges = [pill_html(e.replace("_", " ").title(), "#8b98a5", "#1c2230") for e in sorted(MY_EQUIPMENT)]
    # Add dedicated kettlebell inventory badge
    kb_summary_badge = pill_html("🔔 Kettlebells: 10, 15, 20 lbs", "#f59e0b", "#2e1c0c")
    st.markdown(f"**Your equipment:** {' '.join(equip_badges)} {kb_summary_badge}", unsafe_allow_html=True)
    st.write("")  # Spacing
    
    # Generate and display the plan
    current_plan = generate_plan(st.session_state.date)
    build_plan_view(current_plan)

    # Footer
    st.divider()
    with st.container(border=True):
        st.write("**HOW THIS PLAN IS BUILT**")
        st.caption(f"""
        - Session type follows a 9-day cycle (3 strength · 2 HIIT · 2 Zone 2 · 1 metcon · 1 recovery). 9 and 7 are coprime, so no weekday is permanently 'weights day'.
        - Exercises are filtered to the equipment listed above, including your 10, 15, and 20 lb kettlebells, avoiding moves done in the last {ANTI_REPEAT_DAYS} days.
        - **Kettlebell Loading Strategy:**
          - **10 lb**: Overhead presses, halos, Turkish get-ups, rotational work, high-cadence HIIT.
          - **15 lb**: Single-arm swings, cleans, lunges, and renegade rows.
          - **20 lb**: Two-handed swings, goblet squats, Romanian deadlifts, and loaded carries.
        - The plan is seeded by the calendar date, so it will not reshuffle if you refresh mid-workout.
        - Calorie figures are MET-based estimates for {BODY_WEIGHT_LB} lb - change BODY_WEIGHT_LB in engine.py. Treat them as ballpark, not truth.
        - Training drives the deficit but does not create it on its own: aim for ~0.7-1.0g protein per lb of bodyweight, a 300-500 kcal deficit, 8-10k steps, and 7-9 h of sleep.
        """)
        st.divider()
        st.caption(f"Exercise DB: {DB.status} · Photos/Instructions: free-exercise-db (public domain).")

if __name__ == "__main__":
    main()
