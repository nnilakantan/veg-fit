import streamlit as st
import requests
import datetime
import time

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

# 1. Workout Database - Simplified for 100% Stability
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    
    plans = {
        "Monday": {
            "title": "🏋️ Dumbbell Strength & Boxing",
            "exercises": [
                {"name": "Goblet Squats", "reps": "4 Sets of 12", "steps": ["Hold one 25lb DB vertically at chest height.", "Keep elbows tucked to ribs.", "Sit back into the squat until thighs are parallel to floor.", "Drive through heels to stand up."]},
                {"name": "Overhead Press", "reps": "3 Sets of 10", "steps": ["Hold DBs at shoulder height, palms facing each other.", "Tighten core and glutes (don't arch back).", "Press DBs toward the ceiling until arms are straight.", "Lower slowly back to shoulders."]},
                {"name": "Heavy Bag Punching", "reps": "5 Minutes", "steps": ["Maintain boxing stance.", "Throw 1-2 (Jab-Cross) combos.", "Keep hands up to protect your face.", "Stay light on your feet."]}
            ]
        },
        "Tuesday": {
            "title": "🏃 Treadmill HIIT",
            "exercises": [
                {"name": "Interval Sprints", "reps": "10 Rounds", "steps": ["30 seconds: Sprint (Level 7-9 speed).", "30 seconds: Walk (Level 3 speed).", "Repeat 10 times total."]}
            ]
        },
        "Wednesday": {
            "title": "🚣 Rowing & Core",
            "exercises": [
                {"name": "Steady State Rowing", "reps": "15 Minutes", "steps": ["Push with legs first.", "Lean back slightly.", "Pull handle to lower ribs.", "Return arms, then torso, then legs."]}
            ]
        }
    }
    return day, plans.get(day, {"title": "Active Recovery", "exercises": []})

day_name, today_plan = get_workout_data()

# 2. Workout UI
st.subheader(f"📅 {day_name.upper()}: {today_plan['title']}")

# Rest Timer
if st.button("⏱️ Start 60s Rest Timer"):
    t = st.empty()
    for i in range(60, 0, -1):
        t.metric("Resting...", f"{i}s")
        time.sleep(1)
    st.success("🔥 Back to work!")

for ex in today_plan['exercises']:
    with st.expander(f"🔹 {ex['name']} ({ex['reps']})", expanded=True):
        st.write(f"**Target:** {ex['reps']}")
        st.write("**Step-by-Step:**")
        for step in ex['steps']:
            st.write(f"✅ {step}")

st.divider()

# 3. Recipe Finder
st.subheader("🔍 Asian Vegetarian Recipe Finder")
ingredient = st.text_input("Enter ingredients (e.g. Tofu, Cabbage):")

if st.button("Search Recipes"):
    if ingredient:
        st.write("Searching Asian Vegetarian options...")
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY,
                "includeIngredients": ingredient,
                "cuisine": "Indian,Thai,Asian,Chinese,Vietnamese",
                "diet": "vegetarian",
                "number": 5,
                "addRecipeInformation": True
            }).json()
            
            if res.get('results'):
                for r in res['results']:
                    with st.expander(f"🍲 {r['title']}"):
                        st.write(f"[Open Full Recipe]({r['sourceUrl']})")
                        # We keep images for recipes as Spoonacular links are very stable
                        st.image(r['image'])
            else:
                st.warning("No matches found.")
        except Exception:
            st.error("Connection error.")
    else:
        st.error("Please enter an ingredient first!")
