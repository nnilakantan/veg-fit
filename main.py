import streamlit as st
import requests
import datetime

# 1. Page Configuration & Theme
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

# Your Spoonacular API Key
API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

# 2. Sidebar: Goal Tracking (200lbs -> 140lbs)
with st.sidebar:
    st.header("📉 Weight Loss Journey")
    current_w = st.number_input("Today's Weight (lbs):", value=200.0, step=0.1)
    
    goal_w = 140.0
    start_w = 200.0
    
    lbs_lost = start_w - current_w
    lbs_to_go = current_w - goal_w
    progress_pct = min(100, int((lbs_lost / (start_w - goal_w)) * 100))
    
    st.metric("Pounds to 140", f"{lbs_to_go:.1f} lbs", delta=f"-{lbs_lost:.1f}")
    st.write(f"**Progress:** {progress_pct}%")
    st.progress(progress_pct / 100)
    
    st.divider()
    st.info("💡 Tip: Drink 500ml water before every meal to boost metabolism.")

# 3. App Header
st.title("🥗 VEG-FIT PRO")

# 4. Detailed Weekly Workout Database
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
                {"name": "Interval Sprints", "reps": "10 Rounds", "img": "treadmill.jpg", "steps": ["30s Sprint (Level 7-9).", "30s Walk (Level 3).", "Focus on high knees during sprint."]}
            ]
        },
        "Wednesday": {
            "title": "🚣 Rowing & Core",
            "exercises": [
                {"name": "Steady State Rowing", "reps": "15 Minutes", "img": "rowing.jpg", "steps": ["Legs -> Core -> Arms sequence.", "Maintain 22-24 strokes per minute."]},
                {"name": "Bicycle Crunches", "reps": "3 Sets of 20", "img": "core.jpg", "steps": ["Elbow to opposite knee.", "Keep shoulder blades off the floor."]}
            ]
        },
        "Thursday": {
            "title": "🚣 Endurance Rowing",
            "exercises": [
                {"name": "Pyramid Row", "reps": "40 Minutes", "img": "rowing.jpg", "steps": ["5 min moderate / 5 min high intensity.", "Breathe rhythmically with strokes."]}
            ]
        },
        "Friday": {
            "title": "🏋️ Strength & Lunges",
            "exercises": [
                {"name": "Dumbbell Thrusters", "reps": "4 Sets of 10", "img": "squat.jpg", "steps": ["Full squat then overhead press.", "Keep the motion fluid."]}
            ]
        },
        "Saturday": {
            "title": "🚶 Active Recovery Mix",
            "exercises": [
                {"name": "Incline Walk", "reps": "20 Minutes", "img": "treadmill.jpg", "steps": ["3.5 mph speed.", "8% to 10% Incline.", "Pump arms; don't hold the rails."]}
            ]
        },
        "Sunday": {
            "title": "🧘 Rest & Stretch",
            "exercises": [
                {"name": "Yoga Flow", "reps": "20 Minutes", "img": "yoga.jpg", "steps": ["Focus on hips and lower back.", "Deep nasal breathing."]}
            ]
        }
    }
    return day, plans.get(day, {"title": "Rest", "exercises": []})

day_name, today_plan = get_workout_data()

# 5. Workout UI Display
st.header(f"📅 {day_name.upper()}: {today_plan['title']}")

for ex in today_plan['exercises']:
    with st.expander(f"💪 {ex['name']} ({ex['reps']})", expanded=True):
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.write("**Instructional Steps:**")
            for step in ex['steps']:
                st.write(f"✅ {step}")
            st.write(f"**Target:** {ex['reps']}")
        with col2:
            try:
                st.image(ex['img'], use_container_width=True)
            except:
                st.warning(f"📷 Upload '{ex['img']}' to GitHub to see this visual.")

st.divider()

# 6. Recipe Finder Section
st.header("🔍 High-Protein Asian Fuel")
ingredient = st.text_input("What ingredients are in your fridge? (e.g., Tofu, Paneer, Chickpeas)")

if st.button("Search Recipes"):
    if ingredient:
        st.write(f"Searching for vegetarian {ingredient} recipes...")
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
                        st.subheader(r['title'])
                        st.image(r['image'], use_container_width=True)
                        st.write(f"🔗 [View Full Recipe and Macro Info]({r['sourceUrl']})")
                        st.divider()
            else:
                st.warning("No matches found. Try broadening your ingredient search!")
        except:
            st.error("Technical glitch connecting to the recipe server. Try again in a minute!")
