import streamlit as st
import requests
import datetime

# 1. Page Configuration
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

# Your Spoonacular API Key
API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

# 2. APP HEADER & WEIGHT TRACKER
st.title("🥗 VEG-FIT PRO")

# Weight Loss Tracker Section
with st.container():
    st.header("📉 Weight Loss Tracker")
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        start_weight = 200.0
        goal_weight = 140.0
        # Input for current progress
        current_weight = st.number_input("Enter Today's Weight (lbs):", value=195.0, step=0.1)
    
    with col_w2:
        lbs_lost = start_weight - current_weight
        lbs_to_go = current_weight - goal_weight
        # Calculate progress percentage
        progress_pct = min(100.0, max(0.0, (lbs_lost / (start_weight - goal_weight))))
        
        st.metric("Lbs to Goal", f"{lbs_to_go:.1f} lbs", delta=f"-{lbs_lost:.1f} Total")

    # Visual Progress Bar
    st.write(f"**Overall Progress to 140 lbs:** {int(progress_pct * 100)}%")
    st.progress(progress_pct)
    
    # Cheat Meal Logic
    days_since_start = (datetime.datetime.now() - datetime.datetime(2026, 4, 1)).days
    days_until_cheat = 10 - (days_since_start % 10)
    st.caption(f"🥙 Next Cheat Meal in: {days_until_cheat} days (Remember: Eat until 80% full!)")

st.divider()

# 3. Weekly Workout Database
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    plans = {
        "Monday": {
            "title": "🔥 Dumbbell Strength & Boxing",
            "exercises": [
                {"name": "Goblet Squats", "reps": "4 Sets of 12", "img": "squat.jpg", "steps": ["Hold 25lb DB at chest.", "Sit back deep into heels.", "Drive up explosively."]},
                {"name": "Overhead Press", "reps": "3 Sets of 10", "img": "press.jpg", "steps": ["Press DBs to ceiling.", "Lock core; don't arch back."]}
            ]
        },
        "Tuesday": {
            "title": "🏃 Treadmill HIIT (Fat Burn)",
            "exercises": [
                {"name": "Interval Sprints", "reps": "10 Rounds", "img": "treadmill.jpg", "steps": ["30s Sprint (Fast).", "30s Walk (Slow).", "High intensity intervals."]}
            ]
        },
        "Wednesday": {
            "title": "🚣 Rowing & Core",
            "exercises": [
                {"name": "Steady State Rowing", "reps": "15 Minutes", "img": "rowing.jpg", "steps": ["Legs -> Core -> Arms sequence.", "Maintain 22-24 strokes per minute."]},
                {"name": "Bicycle Crunches", "reps": "3 Sets of 20", "img": "core.jpg", "steps": ["Elbow to opposite knee.", "Slow and controlled."]}
            ]
        },
        "Thursday": {
            "title": "🚣 Endurance Rowing",
            "exercises": [
                {"name": "Pyramid Row", "reps": "40 Minutes", "img": "rowing.jpg", "steps": ["5 min moderate / 5 min high intensity.", "Focus on breathing rhythm."]}
            ]
        },
        "Friday": {
            "title": "🏋️ Strength & Lunges",
            "exercises": [
                {"name": "Dumbbell Thrusters", "reps": "4 Sets of 10", "img": "squat.jpg", "steps": ["Full squat then overhead press.", "Keep motion fluid."]}
            ]
        },
        "Saturday": {
            "title": "🚶 Active Recovery Mix",
            "exercises": [
                {"name": "Incline Walk", "reps": "20 Minutes", "img": "treadmill.jpg", "steps": ["3.5 mph speed.", "8% to 10% Incline.", "Don't hold the rails."]}
            ]
        },
        "Sunday": {
            "title": "🧘 Rest & Stretch",
            "exercises": []
        }
    }
    return day, plans.get(day, {"title": "Rest", "exercises": []})

day_name, today_plan = get_workout_data()

# 4. Workout Display
st.header(f"📅 {day_name.upper()}: {today_plan['title']}")

if not today_plan['exercises']:
    st.write("Enjoy your rest day! Maybe a light walk in Washougal?")
else:
    for ex in today_plan['exercises']:
        with st.expander(f"💪 {ex['name']} ({ex['reps']})", expanded=True):
            c1, c2 = st.columns([1.2, 1])
            with c1:
                for step in ex['steps']:
                    st.write(f"✅ {step}")
            with c2:
                try:
                    st.image(ex['img'], use_container_width=True)
                except:
                    st.warning(f"Upload '{ex['img']}' to GitHub.")

st.divider()

# 5. Recipe Finder
st.header("🔍 High-Protein Asian Fuel")
ingredient = st.text_input("What's in the fridge? (e.g., Tofu, Paneer, Chickpeas)")

if st.button("Search Recipes"):
    if ingredient:
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY, "includeIngredients": ingredient, "cuisine": "Indian,Thai,Asian",
                "diet": "vegetarian", "number": 3, "addRecipeInformation": True
            }).json()
            for r in res.get('results', []):
                st.subheader(r['title'])
                st.image(r['image'], use_container_width=True)
                st.write(f"🔗 [View Recipe]({r['sourceUrl']})")
        except:
            st.error("Connection error.")
