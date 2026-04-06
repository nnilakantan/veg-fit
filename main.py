import streamlit as st
import requests
import datetime

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

st.title("🥗 VEG-FIT PRO")

# 1. Detailed Workout Database with Reliable Images
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    
    plans = {
        "Monday": {
            "title": "Dumbbell Strength & Boxing",
            "exercises": [
                {"name": "Goblet Squats", "reps": "4 Sets of 12", "desc": "Hold one 25lb DB vertically at chest height. Keep elbows tucked. Sit back into the squat.", "img": "https://proworkout.app/wp-content/uploads/2020/05/goblet-squat.jpg"},
                {"name": "Overhead Press", "reps": "3 Sets of 10", "desc": "Press DBs from shoulders to ceiling. Keep your core tight so your back doesn't arch.", "img": "https://proworkout.app/wp-content/uploads/2020/05/dumbbell-overhead-press.jpg"},
                {"name": "Heavy Bag Punching", "reps": "5 Minutes", "desc": "Continuous 1-2 combos. Move your feet. Focus on 'snapping' your punches.", "img": "https://www.burnthefatinnercircle.com/members/images/1543.jpg"}
            ]
        },
        "Tuesday": {
            "title": "Treadmill HIIT",
            "exercises": [
                {"name": "Warm-up Walk", "reps": "5 Minutes", "desc": "3.0 mph at 1% incline. Get the blood flowing.", "img": "https://proworkout.app/wp-content/uploads/2020/05/treadmill-walking.jpg"},
                {"name": "Sprints", "reps": "10 Rounds", "desc": "30 sec Sprint (7-8 mph) / 30 sec Walk (3 mph).", "img": "https://proworkout.app/wp-content/uploads/2020/05/treadmill-running.jpg"},
                {"name": "Incline Cool Down", "reps": "5 Minutes", "desc": "3.0 mph at 5% incline to burn extra calories.", "img": "https://proworkout.app/wp-content/uploads/2020/05/treadmill-walking.jpg"}
            ]
        },
        "Wednesday": {
            "title": "Rowing & Core",
            "exercises": [
                {"name": "Steady State Rowing", "reps": "15 Minutes", "desc": "Push with legs first, then lean back, then pull with arms.", "img": "https://proworkout.app/wp-content/uploads/2020/05/rowing-machine.jpg"},
                {"name": "Bicycle Crunches", "reps": "3 Sets of 20", "desc": "Opposite elbow to opposite knee. Focus on the twist.", "img": "https://proworkout.app/wp-content/uploads/2020/05/bicycle-crunch.jpg"}
            ]
        },
        "Thursday": {
            "title": "Endurance Rowing",
            "exercises": [
                {"name": "Pyramid Row", "reps": "40 Minutes", "desc": "Alternating intensity. 5 min easy, 5 min hard.", "img": "https://proworkout.app/wp-content/uploads/2020/05/rowing-machine.jpg"}
            ]
        },
        "Friday": {
            "title": "Thrusters & Lunges",
            "exercises": [
                {"name": "Dumbbell Thrusters", "reps": "4 Sets of 10", "desc": "Squat down with DBs at shoulders, then explode up into an overhead press.", "img": "https://proworkout.app/wp-content/uploads/2020/05/dumbbell-thruster.jpg"},
                {"name": "Walking Lunges", "reps": "3 Sets of 12", "desc": "Hold DBs at sides. Large step forward, dropping back knee toward floor.", "img": "https://proworkout.app/wp-content/uploads/2020/05/dumbbell-walking-lunge.jpg"}
            ]
        },
        "Saturday": {
            "title": "Active Recovery Mix",
            "exercises": [
                {"name": "Moderate Rowing", "reps": "20 Minutes", "desc": "Focus on perfect form and consistent breathing.", "img": "https://proworkout.app/wp-content/uploads/2020/05/rowing-machine.jpg"},
                {"name": "Incline Treadmill Walk", "reps": "20 Minutes", "desc": "3.5 mph at 8% incline. Great for weight loss.", "img": "https://proworkout.app/wp-content/uploads/2020/05/treadmill-walking.jpg"}
            ]
        },
        "Sunday": {
            "title": "Deep Stretch",
            "exercises": [
                {"name": "Sun Salutations", "reps": "5 Rounds", "desc": "Slow flow: Plank to Cobra to Downward Dog.", "img": "https://proworkout.app/wp-content/uploads/2020/05/yoga-sun-salutation.jpg"},
                {"name": "Child's Pose", "reps": "3 Minutes", "desc": "Sit on heels, reach arms forward, forehead to floor.", "img": "https://proworkout.app/wp-content/uploads/2020/05/childs-pose.jpg"}
            ]
        }
    }
    return day, plans.get(day, {"title": "Rest", "exercises": []})

day_name, today_plan = get_workout_data()

# 2. Workout UI
st.subheader(f"📅 {day_name.upper()}: {today_plan['title']}")

for ex in today_plan['exercises']:
    with st.expander(f"{ex['name']} - {ex['reps']}", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"**Step-by-Step:**\n{ex['desc']}")
            st.write(f"**Target:** {ex['reps']}")
        with col2:
            st.image(ex['img'], use_container_width=True)

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
                    with st.expander(r['title']):
                        st.write(f"[View Full Recipe]({r['sourceUrl']})")
                        st.image(r['image'])
            else:
                st.warning("No matches found. Try different ingredients!")
        except Exception:
            st.error("Connection error. Please try again later.")
    else:
        st.error("Please enter an ingredient first!")
