import streamlit as st
import requests
import datetime

# Page Config
st.set_page_config(page_title="VEG-FIT Pro", page_icon="🥗", layout="centered")

# Your Spoonacular API Key
API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

# 1. Title
st.title("🥗 VEG-FIT PRO")

# 2. Workout Section
def get_workout_data():
    day = datetime.datetime.now().strftime("%A")
    workouts = {
        "Monday": {"text": "Dumbbell Strength (25lb Focus) + 5 min Punching Bag.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
        "Tuesday": {"text": "HIIT: 30 min Treadmill Intervals.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
        "Wednesday": {"text": "Full Body: Rowing 15 min + Ab Crunches.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
        "Thursday": {"text": "Endurance: 40 min Steady Rowing.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
        "Friday": {"text": "Strength: Thrusters and Lunges + 10 min Boxing.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
        "Saturday": {"text": "Active: 20 min Rowing + 20 min Incline Walk.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
        "Sunday": {"text": "Rest & Stretch: 30 min light walking.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/Yoga-5c8e7e1746e0fb00014e7a2b.jpg"}
    }
    return day, workouts.get(day, {"text": "Rest Day", "img": ""})

day_name, today_workout = get_workout_data()

with st.container():
    st.subheader(f"📅 Today's {day_name.upper()} Plan")
    st.info(today_workout['text'])
    if today_workout['img']:
        st.image(today_workout['img'], use_container_width=True)

st.divider()

# 3. Recipe Finder Section
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
