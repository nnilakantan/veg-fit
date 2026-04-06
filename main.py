import streamlit as st
import requests
import datetime

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

# 1. Workout Database with "Embedded" Visuals
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    
    plans = {
        "Monday": {
            "title": "🏋️ Dumbbell Strength & Boxing",
            "exercises": [
                {
                    "name": "Goblet Squats", 
                    "reps": "4 Sets of 12", 
                    # This is a tiny placeholder image that Streamlit can't block
                    "img": "https://img.icons8.com/color/144/weightlift.png",
                    "steps": ["Hold one 25lb DB at chest.", "Sit back until thighs are parallel to floor.", "Drive through heels to stand."]
                },
                {
                    "name": "Overhead Press", 
                    "reps": "3 Sets of 10", 
                    "img": "https://img.icons8.com/color/144/overhead-shoulder-press.png",
                    "steps": ["Press DBs from shoulders to ceiling.", "Keep core tight; do not arch back."]
                }
            ]
        }
    }
    return day, plans.get(day, {"title": "Active Recovery", "exercises": []})

day_name, today_plan = get_workout_data()

# 2. Workout UI (Single Column for better mobile loading)
st.subheader(f"📅 {day_name.upper()}: {today_plan['title']}")

for ex in today_plan['exercises']:
    with st.expander(f"🔹 {ex['name']} ({ex['reps']})", expanded=True):
        st.image(ex['img'], width=100)
        st.write("**Form Checklist:**")
        for step in ex['steps']:
            st.write(f"✅ {step}")

st.divider()

# 3. Recipe Finder
st.subheader("🔍 Asian Vegetarian Recipe Finder")
ingredient = st.text_input("Search (e.g. Tofu, Paneer):")

if st.button("Search Recipes"):
    if ingredient:
        st.write("Searching Asian Vegetarian options...")
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY,
                "includeIngredients": ingredient,
                "cuisine": "Indian,Thai,Asian",
                "diet": "vegetarian",
                "number": 3,
                "addRecipeInformation": True
            }).json()
            
            if res.get('results'):
                for r in res['results']:
                    with st.container():
                        st.write(f"### {r['title']}")
                        # Spoonacular images are usually safe because they use a CDN
                        st.image(r['image'], use_container_width=True)
                        st.write(f"[Open Full Recipe]({r['sourceUrl']})")
            else:
                st.warning("No matches found.")
        except:
            st.error("Connection error.")
