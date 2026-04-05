# 1. Install Flet, requests, and localtunnel
!pip install --upgrade flet requests
!npm install -g localtunnel

# 2. Create the main.py with Hex Colors
with open("main.py", "w") as f:
    f.write("""
import flet as ft
import requests
import datetime

API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

def main(page: ft.Page):
    page.title = "VEG-FIT Pro"
    page.theme_mode = "dark"
    page.padding = 20
    page.scroll = "adaptive"

    def get_workout_data():
        day = datetime.datetime.now().strftime("%A").lower()
        workouts = {
            "monday": {"text": "Dumbbell Strength (25lb Focus) + 5 min Punching Bag.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
            "tuesday": {"text": "HIIT: 30 min Treadmill Intervals.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
            "wednesday": {"text": "Full Body: Rowing 15 min + Ab Crunches.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
            "thursday": {"text": "Endurance: 40 min Steady Rowing.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
            "friday": {"text": "Strength: Thrusters and Lunges + 10 min Boxing.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
            "saturday": {"text": "Active: 20 min Rowing + 20 min Incline Walk.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
            "sunday": {"text": "Rest & Stretch: 30 min light walking.", "img": ""}
        }
        return day, workouts.get(day, {"text": "Rest Day", "img": ""})

    def fetch_recipes(e):
        if not ingredient_input.value: return
        status_text.value = "Searching..."
        recipe_results.controls.clear()
        page.update()
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY, "includeIngredients": ingredient_input.value,
                "cuisine": "Indian,Thai,Asian,Chinese,Vietnamese", "diet": "vegetarian",
                "number": 5, "addRecipeInformation": True
            }).json()
            if res.get('results'):
                for r in res['results']:
                    recipe_results.controls.append(ft.ListTile(title=ft.Text(r['title']), on_click=lambda _, u=r['sourceUrl']: page.launch_url(u)))
                status_text.value = "Matches found:"
            else:
                status_text.value = "No matches."
        except: status_text.value = "Error!"
        page.update()

    day_name, today_workout = get_workout_data()
    status_text = ft.Text("")
    recipe_results = ft.Column()
    ingredient_input = ft.TextField(label="Ingredients", border_color="#4ade80")

    page.add(
        ft.Text("VEG-FIT", size=30, weight="bold", color="#4ade80"),
        ft.Container(content=ft.Column([
            ft.Text(f"{day_name.upper()} PLAN", weight="bold"),
            ft.Text(today_workout['text']),
            ft.Image(src=today_workout['img'], height=200) if today_workout['img'] else ft.Text("Rest Day")
        ]), bgcolor="#212121", padding=20, border_radius=15),
        ft.Divider(),
        ingredient_input,
        ft.ElevatedButton("Search Recipes", on_click=fetch_recipes, bgcolor="#2e7d32", color="white"),
        status_text,
        recipe_results
    )

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
""")

# 3. GET YOUR IP
print("--- PASSWORD ---")
!curl ipv4.icanhazip.com

# 4. RUN THE TUNNEL
from threading import Thread
import time

def run_flet():
    !python main.py

def run_tunnel():
    time.sleep(5)
    !lt --port 8550

Thread(target=run_flet).start()
run_tunnel()