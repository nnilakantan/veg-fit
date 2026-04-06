import flet as ft
import requests
import datetime

# Your Spoonacular API Key
API_KEY = "1954fed20ccd484a87c2e25338a2bccc"

def main(page: ft.Page):
    page.title = "VEG-FIT Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"

    # 1. Workout Logic
    def get_workout_data():
        # Get the current day in lowercase (e.g., 'monday')
        day = datetime.datetime.now().strftime("%A").lower()
        workouts = {
            "monday": {"text": "Dumbbell Strength (25lb Focus) + 5 min Punching Bag.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
            "tuesday": {"text": "HIIT: 30 min Treadmill Intervals.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
            "wednesday": {"text": "Full Body: Rowing 15 min + Ab Crunches.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
            "thursday": {"text": "Endurance: 40 min Steady Rowing.", "img": "https://content.active.com/Assets/Active.com+Content+Site+Digital+Assets/Fitness/Articles/Proper+Rowing+Form/rowing+machine.jpg"},
            "friday": {"text": "Strength: Thrusters and Lunges + 10 min Boxing.", "img": "https://hips.hearstapps.com/hmg-prod/images/mh-1-23-goblet-squat-1674510761.jpg"},
            "saturday": {"text": "Active: 20 min Rowing + 20 min Incline Walk.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/PunchingBag-5c8e7e1746e0fb00014e7a2b.jpg"},
            "sunday": {"text": "Rest & Stretch: 30 min light walking.", "img": "https://www.verywellfit.com/thmb/gYJ4m3h8T8p4F_xO8wE_g_nQJ4s=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/Yoga-5c8e7e1746e0fb00014e7a2b.jpg"}
        }
        return day, workouts.get(day, {"text": "Rest Day", "img": ""})

    # 2. Recipe Search Logic
    def fetch_recipes(e):
        if not ingredient_input.value:
            status_text.value = "Please enter an ingredient."
            page.update()
            return
            
        status_text.value = "Searching Asian Vegetarian options..."
        recipe_results.controls.clear()
        page.update()
        
        try:
            res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params={
                "apiKey": API_KEY,
                "includeIngredients": ingredient_input.value,
                "cuisine": "Indian,Thai,Asian,Chinese,Vietnamese",
                "diet": "vegetarian",
                "number": 5,
                "addRecipeInformation": True
            }).json()
            
            if res.get('results'):
                for r in res['results']:
                    recipe_results.controls.append(
                        ft.ListTile(
                            title=ft.Text(r['title'], color=ft.colors.GREEN_ACCENT_400),
                            subtitle=ft.Text("Tap to view recipe"),
                            on_click=lambda _, u=r['sourceUrl']: page.launch_url(u)
                        )
                    )
                status_text.value = "Matches found:"
            else:
                status_text.value = "No matches found for those ingredients."
        except Exception:
            status_text.value = "Error connecting to recipe service."
        page.update()

    # UI Components
    day_name, today_workout = get_workout_data()
    status_text = ft.Text("", italic=True)
    recipe_results = ft.Column()
    ingredient_input = ft.TextField(
        label="Ingredients (Tofu, Cabbage, etc.)",
        border_color=ft.colors.GREEN_ACCENT_400
    )

    # Adding to Page
    page.add(
        ft.Text("VEG-FIT PRO", size=32, weight="bold", color=ft.colors.GREEN_ACCENT_400),
        ft.Container(
            content=ft.Column([
                ft.Text(f"TODAY'S {day_name.upper()} PLAN", weight="bold", size=18),
                ft.Text(today_workout['text'], size=16),
                ft.Image(src=today_workout['img'], height=200, border_radius=10) if today_workout['img'] else ft.Text("Enjoy your rest!")
            ]),
            bgcolor=ft.colors.GREY_900,
            padding=20,
            border_radius=15
        ),
        ft.Divider(height=40, color=ft.colors.TRANSPARENT),
        ft.Text("RECIPE FINDER", size=20, weight="bold"),
        ingredient_input,
        ft.ElevatedButton(
            "Search Asian Recipes", 
            on_click=fetch_recipes,
            style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
        ),
        status_text,
        recipe_results
    )

# Critical: This line is required for web hosting
if __name__ == "__main__":
    ft.app(target=main)
