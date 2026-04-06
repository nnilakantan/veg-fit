import streamlit as st
import requests
import datetime
import time

st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    plans = {
        "Monday": {
            "title": "🏋️ Dumbbell Strength & Boxing",
            "exercises": [
                {
                    "name": "Goblet Squats", 
                    "reps": "4 Sets of 12", 
                    "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Goblet_Squat.jpg/640px-Goblet_Squat.jpg",
                    "steps": ["Hold one 25lb DB at chest.", "Sit back until thighs are parallel to floor.", "Drive through heels to stand."]
                },
                {
                    "name": "Overhead Press", 
                    "reps": "3 Sets of 10", 
                    "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Overhead_Press.jpg/640px-Overhead_Press.jpg",
                    "steps": ["Press DBs from shoulders to ceiling.", "Keep core tight; do not arch back."]
                }
            ]
        },
        "Tuesday": {
            "title": "🏃 Treadmill HIIT",
            "exercises": [
                {
                    "name": "Interval Sprints", 
                    "reps": "10 Rounds", 
                    "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Running_on_treadmill.jpg/640px-Running_on_treadmill.jpg",
                    "steps": ["30s Sprint / 30s Walk.", "Repeat 10 times."]
                }
            ]
        }
    }
    return day, plans.get(day, {"title": "Active Recovery", "exercises": []})

day_name, today_plan = get_workout_data()

st.subheader(f"📅 {day_name.upper()}: {today_plan['title']}")

for ex in today_plan['exercises']:
    with st.expander(f"🔹 {ex['name']} ({ex['reps']})", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Form Checklist:**")
            for step in ex['steps']:
                st.write(f"✅ {step}")
        with col2:
            st.image(ex['img'], use_container_width=True)

st.divider()

# Recipe Search (Remains exactly as before)
st.subheader("🔍 Asian Vegetarian Recipe Finder")
ingredient = st.text_input("Search (e.g. Tofu, Paneer):")

if st.button("Search Recipes"):
    if ingredient:
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY, "includeIngredients": ingredient,
                "cuisine": "Indian,Thai,Asian", "diet": "vegetarian", "number": 3
            }).json()
            if res.get('results'):
                for r in res['results']:
                    st.image(r['image'], caption=r['title'])
            else:
                st.warning("No matches.")
        except:
            st.error("Connection error.")
