import streamlit as st
import requests
import datetime

st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    # We use a Relative Path to find the images in your GitHub folder
    plans = {
        "Monday": {
            "title": "🏋️ Dumbbell Strength",
            "exercises": [
                {
                    "name": "Goblet Squats", 
                    "reps": "4 Sets of 12", 
                    "img": "squat.jpg", # Matches the filename on GitHub
                    "steps": ["Hold one 25lb DB at chest.", "Sit back deep.", "Drive through heels."]
                },
                {
                    "name": "Overhead Press", 
                    "reps": "3 Sets of 10", 
                    "img": "press.jpg", # Matches the filename on GitHub
                    "steps": ["Press DBs to ceiling.", "Keep core tight."]
                }
            ]
        }
    }
    return day, plans.get(day, {"title": "Active Recovery", "exercises": []})

day_name, today_plan = get_workout_data()

st.subheader(f"📅 {day_name.upper()}")

for ex in today_plan['exercises']:
    with st.expander(f"🔹 {ex['name']}", expanded=True):
        # This tells Streamlit to load the image from your project folder
        try:
            st.image(ex['img'], width=300)
        except:
            st.write("📷 Upload 'squat.jpg' and 'press.jpg' to GitHub to see visuals.")
        
        for step in ex['steps']:
            st.write(f"✅ {step}")

st.divider()

# Recipe Finder (Spoonacular links are external but usually whitelisted)
st.subheader("🔍 Asian Vegetarian Recipes")
ingredient = st.text_input("Ingredients:")
if st.button("Search"):
    res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
        "apiKey": API_KEY, "includeIngredients": ingredient, "number": 3
    }).json()
    for r in res.get('results', []):
        st.image(r['image'], caption=r['title'])
