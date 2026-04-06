import streamlit as st
import requests
import datetime

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

# 1. Detailed Workout Database
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    
    # Detailed exercise database
    plans = {
        "Monday": {
            "title": "Dumbbell Strength & Boxing",
            "exercises": [
                {"name": "Goblet Squats", "reps": "4 Sets of 12", "desc": "Hold one 25lb DB at chest height. Keep back straight.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKMGpxx66F1vN6w/giphy.gif"},
                {"name": "Overhead Press", "reps": "3 Sets of 10", "desc": "Press DBs from shoulders to ceiling. Control the descent.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"},
                {"name": "Heavy Bag Punching", "reps": "5 Minutes", "desc": "Continuous 1-2 combos. Focus on rotation and breath.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/l0HlPtb37p9I5hNja/giphy.gif"}
            ]
        },
        "Tuesday": {
            "title": "Treadmill HIIT",
            "exercises": [
                {"name": "Warm-up Walk", "reps": "5 Minutes", "desc": "3.0 mph at 1% incline.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"},
                {"name": "Sprints", "reps": "10 Rounds", "desc": "30 sec Sprint (7-8 mph) / 30 sec Walk (3 mph).", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/l0HlV0v4eU8YxYyYw/giphy.gif"},
                {"name": "Incline Cool Down", "reps": "5 Minutes", "desc": "3.0 mph at 5% incline.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"}
            ]
        },
        "Wednesday": {
            "title": "Rowing & Core",
            "exercises": [
                {"name": "Steady State Rowing", "reps": "15 Minutes", "desc": "Maintain 22-24 strokes per minute.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKP0mY16669N6yA/giphy.gif"},
                {"name": "Bicycle Crunches", "reps": "3 Sets of 20", "desc": "Opposite elbow to opposite knee. Slow and controlled.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/l0HlPtb37p9I5hNja/giphy.gif"}
            ]
        },
        "Thursday": {
            "title": "Endurance Rowing",
            "exercises": [
                {"name": "Pyramid Row", "reps": "40 Minutes", "desc": "5 min easy, 5 min hard, repeat until 40 mins total.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKP0mY16669N6yA/giphy.gif"}
            ]
        },
        "Friday": {
            "title": "Thrusters & Lunges",
            "exercises": [
                {"name": "Dumbbell Thrusters", "reps": "4 Sets of 10", "desc": "Full squat into overhead press with 25lb DBs.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKMGpxx66F1vN6w/giphy.gif"},
                {"name": "Walking Lunges", "reps": "3 Sets of 12", "desc": "Hold DBs at sides. Don't let knee touch the ground.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"}
            ]
        },
        "Saturday": {
            "title": "Active Recovery Mix",
            "exercises": [
                {"name": "Moderate Rowing", "reps": "20 Minutes", "desc": "Zone 2 cardio (can still talk while rowing).", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKP0mY16669N6yA/giphy.gif"},
                {"name": "Incline Treadmill Walk", "reps": "20 Minutes", "desc": "3.5 mph at 8% incline.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"}
            ]
        },
        "Sunday": {
            "title": "Deep Stretch",
            "exercises": [
                {"name": "Sun Salutations", "reps": "5 Rounds", "desc": "Slow flow to open the hips and back.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/3o7TKVUn7XYMgbzgB2/giphy.gif"},
                {"name": "Child's Pose", "reps": "3 Minutes", "desc": "Deep breathing and low back release.", "img": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzRreXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4eXJ4/l0HlPtb37p9I5hNja/giphy.gif"}
            ]
        }
    }
    return day, plans.get(day, {"title": "Rest", "exercises": []})

day_name, today_plan = get_workout_data()

# 2. Workout UI
st.subheader(f"📅 Today's {day_name.upper()} Focus: {today_plan['title']}")

for ex in today_plan['exercises']:
    with st.expander(f"{ex['name']} - {ex['reps']}", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"**Instructions:** {ex['desc']}")
            st.write(f"**Goal:** {ex['reps']}")
        with col2:
            st.image(ex['img'], use_container_width=True)

st.divider()

# 3. Recipe Finder (Same as before)
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
                st.warning("No matches found. Try different ingredients!")
        except Exception:
            st.error("Connection error. Please try again later.")
    else:
        st.error("Please enter an ingredient first!")
