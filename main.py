import streamlit as st
import requests
import datetime
import time

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

# 1. Workout Database with Open-Source Stable Images
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    
    plans = {
        "Monday": {
            "title": "Dumbbell Strength & Boxing",
            "exercises": [
                {"name": "Goblet Squats", "reps": "4 Sets of 12", "desc": "Hold one 25lb DB at chest. Sit back into the squat.", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Goblet_Squat.jpg/640px-Goblet_Squat.jpg"},
                {"name": "Overhead Press", "reps": "3 Sets of 10", "desc": "Press DBs from shoulders to ceiling. Core tight.", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Overhead_Press.jpg/640px-Overhead_Press.jpg"},
                {"name": "Heavy Bag Punching", "reps": "5 Minutes", "desc": "Continuous 1-2 combos. Move your feet.", "img": "https://images.unsplash.com/photo-1594381898411-846e7d193883?auto=format&fit=crop&q=80&w=400"}
            ]
        },
        "Tuesday": {
            "title": "Treadmill HIIT",
            "exercises": [
                {"name": "Interval Sprints", "reps": "10 Rounds", "desc": "30 sec Sprint / 30 sec Walk.", "img": "https://images.unsplash.com/photo-1571008887538-b36bb32f4571?auto=format&fit=crop&q=80&w=400"}
            ]
        },
        "Wednesday": {
            "title": "Rowing & Core",
            "exercises": [
                {"name": "Steady Rowing", "reps": "15 Minutes", "desc": "Legs-Core-Arms sequence.", "img": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&q=80&w=400"},
                {"name": "Bicycle Crunches", "reps": "3 Sets of 20", "desc": "Opposite elbow to opposite knee.", "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Bicycle_Crunches.jpg/640px-Bicycle_Crunches.jpg"}
            ]
        }
    }
    # Add Thursday-Sunday (Omitted for brevity, but same structure as above)
    return day, plans.get(day, {"title": "Active Recovery", "exercises": []})

day_name, today_plan = get_workout_data()

# 2. Workout UI
st.subheader(f"📅 {day_name.upper()}: {today_plan['title']}")

# NEW: Rest Timer for discipline
if st.button("Start 60s Rest Timer"):
    t = st.empty()
    for i in range(60, 0, -1):
        t.metric("Resting...", f"{i}s")
        time.sleep(1)
    st.success("Back to work!")

for ex in today_plan['exercises']:
    with st.expander(f"{ex['name']} - {ex['reps']}", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"**Step-by-Step:**\n{ex['desc']}")
            st.write(f"**Target:** {ex['reps']}")
        with col2:
            st.image(ex['img'], use_container_width=True)

st.divider()

# 3. Recipe Finder (Remains the same)
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
                    with st.expander(r['title']):
                        st.write(f"[View Full Recipe]({r['sourceUrl']})")
                        st.image(r['image'])
            else:
                st.warning("No matches found.")
        except Exception:
            st.error("Connection error.")
    else:
        st.error("Please enter an ingredient first!")
