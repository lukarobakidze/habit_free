import os
from kivy.config import Config

Config.set('graphics', 'width', '360')  
Config.set('graphics', 'height', '640')  # approximately iphone 13 width and height
Config.set('graphics', 'resizable', '0')  # prevent window resizing
Config.set('graphics', 'borderless', '0')  # keep window borders
Config.set('graphics', 'fullscreen', '0')  # prevent fullscreen
Config.write()

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty, ListProperty, DictProperty, ObjectProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.factory import Factory
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore

import datetime
import calendar
import json
import pytz
import random
import re
import requests
from urllib.parse import urlencode
import time

BASE_URL = "http://127.0.0.1:5002"  
utc = pytz.utc

# theme colors
light_theme = {
    "background": get_color_from_hex("#F5F5F5"),  # Light gray background
    "primary": get_color_from_hex("#4CAF50"),     # Material Design Green
    "primary_text": get_color_from_hex("#FFFFFF"), # White text
    "secondary": get_color_from_hex("#2196F3"),    # Material Design Blue
    "secondary_text": get_color_from_hex("#333333"), # Dark gray text
    "accent": get_color_from_hex("#FF4081"),      # Pink accent
    "error": get_color_from_hex("#F44336"),       # Material Design Red
    "status_text": get_color_from_hex("#2E7D32"), # Darker Material Green
    "success_text": get_color_from_hex("#2E7D32"), # Darker Green 
    "input_text": get_color_from_hex("#000000"),  # Black input text
    "input_background": get_color_from_hex("#FFFFFF"), # White input background
    "item_background": get_color_from_hex("#FFFFFF"), # White item background
    "disabled_text": get_color_from_hex("#9E9E9E"), # Gray disabled text
}

PREDEFINED_HABITS = {
    "Smoking": "Quitting smoking drastically reduces risks of cancer, heart disease, and lung problems. You'll breathe easier and have more energy.",
    "Excessive Sugar": "Reducing sugar intake helps manage weight, improves dental health, lowers diabetes risk, and can lead to more stable energy levels.",
    "Nail Biting": "Stopping nail biting prevents infections, improves nail appearance, and reduces dental issues. It's often linked to stress relief.",
    "Procrastination": "Overcoming procrastination reduces stress, improves productivity, boosts self-esteem, and helps achieve goals more effectively.",
    "Excessive Screen Time": "Limiting screen time, especially before bed, improves sleep quality, reduces eye strain, and encourages more physical activity or real-world interaction.",
    "Alcohol": "Reducing or quitting alcohol improves liver health, aids weight loss, enhances sleep quality, boosts mental clarity, and lowers risks of various diseases.",
    "Caffeine": "Lowering caffeine intake can reduce anxiety, improve sleep, prevent digestive issues, and decrease dependency.",
    "Junk Food": "Avoiding junk food helps maintain a healthy weight, provides better nutrition, increases energy levels, and lowers risks of chronic diseases like heart disease and diabetes."
}

# custom widgets
class HabitItem(BoxLayout):
    habit_id = NumericProperty(0)
    habit_name = StringProperty("")
    start_datetime_str = StringProperty("")
    elapsed_time_str = StringProperty("0d 0h 0m")
    is_predefined = BooleanProperty(False)
    background_color = ObjectProperty(get_color_from_hex("#FFFFFF"))

    def __init__(self, habit_data, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.habit_id = habit_data['id']
        self.habit_name = habit_data['name']
        self.start_datetime_str = habit_data['start_datetime']
        self.is_predefined = self.habit_name in PREDEFINED_HABITS
        
        # start the timer with 1 second interval 
        Clock.schedule_interval(self.update_elapsed_time, 1)
        self.update_elapsed_time(0)
        
        Clock.schedule_once(self.apply_theme, 0)

    def update_elapsed_time(self, dt):
        try:
            # parse the UTC time from the backend
            start_time = datetime.datetime.fromisoformat(self.start_datetime_str.replace('Z', '+00:00'))
            if start_time.tzinfo is None:
                start_time = pytz.utc.localize(start_time)
            
            # get current time in UTC
            now = datetime.datetime.now(pytz.utc)
            
            # calculate the time difference in UTC
            delta = now - start_time
            
            # extract days, hours, and minutes
            days = delta.days
            total_seconds = delta.seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            # format the elapsed time string
            if days > 0:
                new_time_str = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                new_time_str = f"{hours}h {minutes}m"
            else:
                new_time_str = f"{minutes}m"
            
            # Only update if the time string has changed
            if new_time_str != self.elapsed_time_str:
                self.elapsed_time_str = new_time_str
                # Force UI update
                if hasattr(self, 'ids') and 'elapsed_time_label' in self.ids:
                    self.ids.elapsed_time_label.text = self.elapsed_time_str.replace('d', ' Days ').replace('h', ' Hours ').replace('m', ' Minutes')
            
            # print debug information every minute
            if minutes % 1 == 0 and total_seconds % 60 == 0:
                print(f"Time update - Start: {start_time}, Now: {now}, Delta: {delta}, Display: {self.elapsed_time_str}")
            
        except Exception as e:
            print(f"Error updating elapsed time: {e}")
            self.elapsed_time_str = "Error"

    def apply_theme(self, *args):
        if not self.app: return
        colors = self.app.theme_colors
        self.background_color = colors.get('item_background', (1,1,1,1))
        if 'habit_label' in self.ids: self.ids.habit_label.color = colors.get('secondary_text')
        if 'elapsed_time_label' in self.ids: self.ids.elapsed_time_label.color = colors.get('primary')
        if 'delete_button' in self.ids: self.ids.delete_button.background_color = colors.get('error')
        if 'fact_button' in self.ids:
            self.ids.fact_button.color = colors.get('accent')
            self.ids.fact_button.disabled = not self.is_predefined
            self.ids.fact_button.opacity = 1.0 if self.is_predefined else 0.0

    def show_habit_fact(self):
        if self.is_predefined and self.app:
            fact = PREDEFINED_HABITS.get(self.habit_name, "No fact available.")
            if self.app.root and hasattr(self.app.root.current_screen, 'show_popup'):
                # create a custom BoxLayout with a blue background
                class BlueBox(BoxLayout):
                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)
                        with self.canvas.before:
                            Color(0.2, 0.6, 0.8, 1)  # Blue
                            self.bg_rect = RoundedRectangle(radius=[20], pos=self.pos, size=self.size)
                        self.bind(pos=self._update_bg, size=self._update_bg)
                    def _update_bg(self, *args):
                        self.bg_rect.pos = self.pos
                        self.bg_rect.size = self.size

                content = BlueBox(orientation='vertical', padding=30, spacing=20, size_hint=(1, 1), height=350)
                
                # title label
                title_label = Label(
                    text=f"[b][i]Benefit of Quitting {self.habit_name}[/i][/b]",
                    font_size='22sp',
                    color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=50,
                    halign='center',
                    valign='middle',
                    text_size=(self.app.root.width * 0.8, None),
                    markup=True
                )
                
                # fact text
                fact_label = Label(
                    text=fact,
                    font_size='17sp',
                    color=(1, 1, 1, 1),
                    text_size=(self.app.root.width * 0.8, 200),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=200
                )
                
                # close button
                close_button = Button(
                    text='Close',
                    size_hint=(None, None),
                    size=(120, 48),
                    pos_hint={'center_x': 0.5},
                    background_color=(0.1, 0.5, 0.2, 1),
                    color=(1,1,1,1),
                    bold=True,
                    font_size='16sp',
                    background_normal='',
                    background_down='',
                )
                
                content.add_widget(title_label)
                content.add_widget(fact_label)
                content.add_widget(close_button)
                
                popup = Popup(
                    title='',
                    content=content,
                    size_hint=(0.9, None),
                    height=420,
                    auto_dismiss=True,
                    background_color=(0,0,0,0),  
                    separator_height=0,
                )
                
                close_button.bind(on_release=popup.dismiss)
                popup.open()


class MessageItem(BoxLayout):
    message_id = NumericProperty(0)
    message_text = StringProperty("")
    send_date_str = StringProperty("")
    is_masked = BooleanProperty(True)
    masked_text = StringProperty("********")
    background_color = ObjectProperty(get_color_from_hex("#FFFFFF"))
    eye_open_source = StringProperty('')
    eye_closed_source = StringProperty('')

    def __init__(self, message_data, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.message_id = message_data['id']
        self.message_text = message_data['message']
        self.send_date_str = f"Send on: {message_data['send_date']}"
        self.is_masked = message_data.get('is_masked', True)
        self.masked_text = "*" * min(len(self.message_text), 20)  # cap at 20 asterisks
        
        # set the image paths
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.eye_open_source = os.path.join(current_dir, 'open_eye.PNG')
        self.eye_closed_source = os.path.join(current_dir, 'closed_eye.PNG')
        
        Clock.schedule_once(self.apply_theme, 0)
        Clock.schedule_once(self.update_toggle_button, 0)

    def update_toggle_button(self, dt):
        """Update the toggle button appearance based on masked state"""
        if hasattr(self, 'ids') and 'toggle_mask_button' in self.ids:
            button = self.ids.toggle_mask_button
            button.background_normal = self.eye_closed_source if self.is_masked else self.eye_open_source
            button.background_down = button.background_normal

    def on_is_masked(self, instance, value):
        """Called when is_masked property changes"""
        Clock.schedule_once(self.update_toggle_button, 0)

    def toggle_mask(self):
        """Toggle message masking and update server."""
        url = f"{self.app.base_url}/toggle_message_mask/{self.message_id}?user_id={self.app.user_id}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            UrlRequest(
                url,
                method='POST',
                req_headers=headers,
                on_success=self.on_toggle_success,
                on_failure=self.on_toggle_failure,
                on_error=self.on_toggle_error
            )
        except Exception as e:
            print(f"Failed to send toggle request: {e}")

    def on_toggle_success(self, request, result):
        """Handle successful mask toggle."""
        message_data = result.get('message_data', {})
        self.is_masked = message_data.get('is_masked', self.is_masked)
        self.update_toggle_button(0)  # update button appearance immediately

    def on_toggle_failure(self, request, result):
        """Handle toggle failure."""
        print(f"Failed to toggle message mask: {result}")

    def on_toggle_error(self, request, error):
        """Handle toggle error."""
        print(f"Error toggling message mask: {error}")

    def apply_theme(self, *args):
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return
        if 'message_content' in self.ids: self.ids.message_content.color = colors.get('secondary_text')
        if 'message_date' in self.ids: self.ids.message_date.color = colors.get('primary')
        if 'delete_msg_button' in self.ids: self.ids.delete_msg_button.background_color = colors.get('error')
        if 'toggle_mask_button' in self.ids: 
            self.ids.toggle_mask_button.background_color = (1, 1, 1, 1)
            self.update_toggle_button(0)


# register the custom widgets with Factory
Factory.register('HabitItem', cls=HabitItem)
Factory.register('MessageItem', cls=MessageItem)

# base screen class
class BaseScreen(Screen):
    status_message = StringProperty('')
    app = ObjectProperty(None)
    base_url = StringProperty(BASE_URL)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._init_app, 0)
        Clock.schedule_once(self._apply_theme_on_load, 0)

    def _init_app(self, dt):
        self.app = App.get_running_app()
        if self.app:
            self.base_url = self.app.base_url

    def _apply_theme_on_load(self, dt):
        if self.app:
            self.apply_theme()

    def apply_theme(self, *args):
        """Apply theme colors to all widgets"""
        if self.app:
            self.apply_theme_widgets()

    def apply_theme_widgets(self):
        """Override in child classes to apply theme to specific widgets"""
        pass

    def show_popup(self, title, message):
        """Show a popup with the given title and message"""
        if not self.app:
            return
            
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        message_label = Label(
            text=message,
            size_hint_y=0.8,
            text_size=(self.width * 0.8, None),
            halign='left',
            valign='middle',
            color=self.app.theme_colors.get('secondary_text', [1,1,1,1])
        )
        button = Button(
            text='Close',
            size_hint=(None, None),
            size=(100, 44),
            pos_hint={'center_x': 0.5},
            background_color=self.app.theme_colors.get('primary', [0,0.7,0.7,1]),
            color=self.app.theme_colors.get('primary_text', [1,1,1,1])
        )
        content.add_widget(message_label)
        content.add_widget(button)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, None),
            height=300,
            auto_dismiss=True
        )
        button.bind(on_release=popup.dismiss)
        popup.open()

    def update_status(self, message, is_error=False):
        """Update status message with optional error styling"""
        # formatting message to fit within screen width
        if message:
            # split long messages into multiple lines
            words = message.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 35:  
                    if len(current_line) > 1:
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(' '.join(current_line))
                        current_line = []
            
            if current_line:
                lines.append(' '.join(current_line))
            
            self.status_message = '\n'.join(lines)
        else:
            self.status_message = ''
            
        if hasattr(self.ids, 'status_label') and self.app:
            self.ids.status_label.color = self.app.theme_colors.get('error' if is_error else 'status_text')

    def handle_network_response(self, request, result, success_callback, failure_message="Error processing response"):
        """Handle network response with proper error checking"""
        if not self.app:
            return
            
        try:
            if isinstance(result, dict) and result.get('success'):
                success_callback(result)
            else:
                error_msg = result.get('message', failure_message) if isinstance(result, dict) else failure_message
                self.update_status(error_msg, is_error=True)
        except Exception as e:
            self.update_status(f"Error: {str(e)}", is_error=True)

    def on_network_failure(self, request, result):
        """Handle network failure response"""
        if isinstance(result, dict):
            error_msg = result.get('message', 'Unknown error occurred')
        else:
            error_msg = str(result)
        print(f"{self.name} - Network failure: {error_msg}")
        self.update_status(error_msg, is_error=True)
        
        # show popup for connection errors
        if "Could not connect" in str(error_msg) or "Connection refused" in str(error_msg):
            self.show_popup("Connection Error", 
                          "Could not connect to the server.\nPlease ensure the backend server is running.")

    def on_network_error(self, request, error):
        """Handle network error"""
        error_msg = str(error)
        print(f"{self.name} - Connection error: {error}")
        
        if "Errno 61" in error_msg or "Connection refused" in error_msg:
            self.update_status("Server unavailable. Please ensure the backend is running.", is_error=True)
            self.show_popup("Connection Error", 
                          "Could not connect to the server.\nPlease ensure the backend server is running.")
        else:
            self.update_status(error_msg, is_error=True)
            self.show_popup("Error", f"An unexpected error occurred:\n{error}")

    def on_enter(self, *args):
        print(f"Entering {self.name}")
        self.apply_theme()
        if hasattr(self, 'fetch_data'):
            Clock.schedule_once(self.fetch_data, 0.1)

    def on_size(self, instance, value):
        pass


# dashboard screen
class DashboardScreen(BaseScreen):
    last_fetch_time = NumericProperty(0)
    habits_data = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.habits_grid = None
        Clock.schedule_once(self._init_grid, 0)

    def _init_grid(self, dt):
        if hasattr(self.ids, 'habit_list'):
            self.habits_grid = self.ids.habit_list
            print("Habits grid initialized")

    def on_enter(self, *args):
        """Called when screen is entered"""
        super().on_enter(*args)
        if self.app and self.app.user_id:
            self.fetch_data()

    def fetch_data(self, *args):
        """Fetch habits data from the server."""
        if not self.app or not self.app.user_id:
            self.update_status("Not logged in", is_error=True)
            return
            
        current_time = time.time()
        if current_time - self.last_fetch_time < 1:  # prevent rapid refetching
            return
            
        self.last_fetch_time = current_time
        url = f"{self.app.base_url}/get_habits?user_id={self.app.user_id}"
        
        try:
            UrlRequest(
                url,
                on_success=self.handle_fetch_success,
                on_failure=self.on_network_failure,
                on_error=self.on_network_error,
                req_headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            self.update_status(f"Network error: {str(e)}", is_error=True)
            print(f"Error fetching habits: {str(e)}")

    def handle_fetch_success(self, request, result):
        """Handle successful habits fetch"""
        print(f"Fetch success response: {result}")
        if isinstance(result, dict) and result.get('success'):
            self.habits_data = result.get('habits', [])
            print(f"Fetched {len(self.habits_data)} habits")
            self.update_habits_grid()
            self.update_status("", False)  # clear any error messages
        else:
            error_msg = result.get('message', 'No habits found or invalid response')
            self.update_status(error_msg, is_error=True)

    def update_habits_grid(self):
        """Update the habits grid with fetched data"""
        if not self.habits_grid:
            print("Error: habits_grid not initialized")
            return
            
        self.habits_grid.clear_widgets()
        print(f"Updating habits grid with {len(self.habits_data)} habits")
        
        if not self.habits_data:
            print("No habits to display")
            self.update_status("No habits found")
            return
            
        for habit in self.habits_data:
            print(f"Adding habit to grid: {habit}")
            habit_item = Factory.HabitItem(habit_data=habit)
            self.habits_grid.add_widget(habit_item)
            print(f"Added habit {habit['name']} to grid")

    def show_random_fact(self):
        if hasattr(self, 'ids') and 'habit_fact_label' in self.ids:
            fact = random.choice(self.habit_facts)
            self.ids.habit_fact_label.text = fact

    def update_elapsed_times(self, dt):
        pass # HabitItem internal timer handles this

    def delete_habit(self, habit_id):
        if not self.app.user_id:
            self.update_status("Error: No user session", True)
            return

        self.update_status("Deleting habit...", False)
        url = f"{self.base_url}/delete/{habit_id}?user_id={self.app.user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Sending delete request for ID {habit_id} to {url}")
        try:
            UrlRequest(url, method='DELETE',
                      req_headers=headers,
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_delete_success, "Delete failed"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
             self.update_status(f"Failed to send delete request: {e}", True)
             self.show_popup("Error", f"Failed to delete habit: {e}")

    def on_delete_success(self, result):
        self.update_status("Habit deleted.", False)
        self.fetch_data()

    def go_to_add_habit(self, *args):
        print("Navigating to Add Habit")
        self.manager.transition = FadeTransition(duration=0.2); self.manager.current = 'add_habit'
    def go_to_inbox(self, *args):
         print("Navigating to Inbox")
         self.manager.transition = FadeTransition(duration=0.2); self.manager.current = 'inbox'
    def go_to_profile(self, *args):
        print("Navigating to Profile")
        self.manager.transition = FadeTransition(duration=0.2); self.manager.current = 'profile'

# add habit screen
class AddHabitScreen(BaseScreen):
    predefined_habits = ListProperty([
        'Smoking',
        'Excessive Sugar',
        'Nail Biting',
        'Procrastination',
        'Excessive Screen Time',
        'Alcohol',
        'Caffeine',
        'Junk Food'
    ])

    def apply_theme_widgets(self):
        """Apply theme to add habit widgets."""
        super().apply_theme_widgets()
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return

        if 'predefined_spinner' in self.ids: self.ids.predefined_spinner.background_color = colors.get('secondary')
        if 'add_habit_input' in self.ids:
             self.ids.add_habit_input.background_color = colors.get('input_background')
             self.ids.add_habit_input.foreground_color = colors.get('input_text')
             is_custom = self.ids.predefined_spinner.text == "Custom Habit" if 'predefined_spinner' in self.ids else True
             self.ids.add_habit_input.disabled_foreground_color = colors.get('disabled_text')

        if 'confirm_add_button' in self.ids:
            self.ids.confirm_add_button.background_color = colors.get('primary')
            self.ids.confirm_add_button.color = colors.get('primary_text')
        if 'cancel_button' in self.ids:
            self.ids.cancel_button.background_color = colors.get('secondary')
            self.ids.cancel_button.color = colors.get('secondary_text')

    def on_enter(self, *args):
        """Clear input and status on entering."""
        super().on_enter(*args)
        if hasattr(self, 'ids'):
            if 'add_habit_input' in self.ids: self.ids.add_habit_input.text = ""
            if 'predefined_spinner' in self.ids: self.ids.predefined_spinner.text = "Custom Habit"
            self.on_predefined_select("Custom Habit")

    def on_predefined_select(self, selected_habit):
        """Handle selection from the predefined habit spinner."""
        if not hasattr(self, 'ids') or not self.app: return
        colors = self.app.theme_colors
        is_custom = selected_habit == "Custom Habit"
        if 'add_habit_input' in self.ids:
            input_widget = self.ids.add_habit_input
            input_widget.disabled = not is_custom
            input_widget.text = ""
            input_widget.hint_text = "Enter custom habit name" if is_custom else "Using predefined habit"
            input_widget.background_color = colors.get('input_background') if is_custom else colors.get('item_background')
            input_widget.foreground_color = colors.get('input_text')
            input_widget.disabled_foreground_color = colors.get('disabled_text')
        if 'status_label' in self.ids:
            self.update_status("Enter custom habit name." if is_custom else f"Selected: {selected_habit}", False)

    def add_habit(self):
        """Add a new habit."""
        if not self.app.user_id:
            self.update_status("Error: No user session", True)
            return

        habit_name = self.ids.add_habit_input.text.strip()
        if not habit_name and self.ids.predefined_spinner.text != 'Custom Habit':
            habit_name = self.ids.predefined_spinner.text

        if not habit_name:
            self.update_status("Please enter a habit name", True)
            return

        self.update_status("Adding habit...", False)
        url = f"{self.base_url}/add"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # include user_id in form data instead of headers
        req_body = urlencode({
            'name': habit_name,
            'user_id': str(self.app.user_id)
        })
        
        print(f"Attempting to add habit: {habit_name}")
        try:
            UrlRequest(url,
                      method='POST',
                      req_headers=headers,
                      req_body=req_body,
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_add_success, "Failed to add habit"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to send add request: {e}", True)
            self.show_popup("Error", f"Failed to add habit: {e}")

    def on_add_success(self, result):
        """Handle successful habit addition."""
        print(f"Add habit response: {result}")
        if result.get('habit'):
            self.update_status("Habit added successfully!", False)
            self.ids.add_habit_input.text = ""
            self.ids.predefined_spinner.text = "Select Habit"
            Clock.schedule_once(self.go_to_dashboard, 0.5)
        else:
            error_msg = result.get('message', 'Unknown error occurred')
            self.update_status(f"Error: {error_msg}", True)

    def go_to_dashboard(self, *args):
        self.manager.transition = FadeTransition(duration=0.2); self.manager.current = 'dashboard'

# inbox screen
class InboxScreen(BaseScreen):
    month_names = ListProperty([calendar.month_name[i] for i in range(1, 13)])
    year_values = ListProperty([])
    day_values = ListProperty([str(i) for i in range(1, 32)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.update_year_spinner()
        Clock.schedule_once(self._bind_spinners, 0.1)

    def _bind_spinners(self, dt):
         if hasattr(self, 'ids'):
             if 'month_spinner' in self.ids: self.ids.month_spinner.bind(text=self.update_day_spinner)
             if 'year_spinner' in self.ids: self.ids.year_spinner.bind(text=self.update_day_spinner)

    def update_year_spinner(self):
         current_year = datetime.date.today().year
         self.year_values = [str(i) for i in range(current_year, current_year + 6)]

    def update_day_spinner(self, *args):

        if not hasattr(self, 'ids') or not all(k in self.ids for k in ['year_spinner', 'month_spinner', 'day_spinner']): return
        year_str = self.ids.year_spinner.text; month_name = self.ids.month_spinner.text; current_day = self.ids.day_spinner.text
        if year_str == "Year" or month_name == "Month": self.day_values = [str(i) for i in range(1, 32)]
        else:
            try: year = int(year_str); month = list(calendar.month_name).index(month_name); num_days = calendar.monthrange(year, month)[1]; self.day_values = [str(i) for i in range(1, num_days + 1)]
            except: self.day_values = [str(i) for i in range(1, 32)]
        if current_day == "Day" or current_day not in self.day_values : self.ids.day_spinner.text = "Day"
        else: self.ids.day_spinner.text = current_day

    def apply_theme_widgets(self):
        super().apply_theme_widgets(); colors = self.app.theme_colors
        if not hasattr(self, 'ids') or not self.app: return
        if 'message_input' in self.ids: self.ids.message_input.background_color = colors.get('input_background'); self.ids.message_input.foreground_color = colors.get('input_text')
        spinner_bg = colors.get('secondary')
        if 'year_spinner' in self.ids: self.ids.year_spinner.background_color = spinner_bg
        if 'month_spinner' in self.ids: self.ids.month_spinner.background_color = spinner_bg
        if 'day_spinner' in self.ids: self.ids.day_spinner.background_color = spinner_bg
        if 'save_button' in self.ids: self.ids.save_button.background_color = colors.get('primary'); self.ids.save_button.color = colors.get('primary_text')
        if 'back_button' in self.ids: self.ids.back_button.background_color = colors.get('secondary'); self.ids.back_button.color = colors.get('secondary_text')
        if 'messages_grid' in self.ids:
            for item in self.ids.messages_grid.children:
                if isinstance(item, MessageItem): item.apply_theme()
                elif isinstance(item, Label): item.color = colors.get('secondary_text')

    def on_enter(self, *args):
        super().on_enter(*args); self.set_default_date()
        self.fetch_data()

    def fetch_data(self, *args):
        """Fetch messages for the inbox."""
        if not self.app.user_id:
            self.update_status("Error: No user session", True)
            return

        self.update_status("Loading messages...", False)
        url = f"{self.base_url}/get_messages?user_id={self.app.user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Attempting to fetch messages from: {url}")
        
        try:
            UrlRequest(url,
                      req_headers=headers,
                      on_success=lambda req, res: self.handle_network_response(req, res, self.parse_messages_success, "Failed to parse messages"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to initiate message fetch: {e}", True)
            self.show_popup("Error", f"Failed to request messages: {e}")

    def set_default_date(self):
        today = datetime.date.today()
        if hasattr(self, 'ids'):
             year_to_set = str(today.year); month_to_set = calendar.month_name[today.month]; day_to_set = str(today.day)
             if year_to_set not in self.year_values: year_to_set = self.year_values[0] if self.year_values else "Year"
             if 'year_spinner' in self.ids: self.ids.year_spinner.text = year_to_set
             if 'month_spinner' in self.ids: self.ids.month_spinner.text = month_to_set
             self.update_day_spinner()
             if day_to_set not in self.day_values: day_to_set = "Day"
             if 'day_spinner' in self.ids: self.ids.day_spinner.text = day_to_set

    def parse_messages_success(self, result):
        """Process successful message fetch response."""
        print("Messages fetched successfully.")
        if not hasattr(self, 'ids') or 'messages_grid' not in self.ids:
            print("UI Error")
            return
        
        messages_grid = self.ids.messages_grid
        messages_grid.clear_widgets()
        self.update_status("", False)
        
        try:
            messages = result.get('messages', [])
            if not messages:
                messages_grid.add_widget(Label(
                    text="No messages saved yet.",
                    color=self.app.theme_colors.get('secondary_text', (0.5, 0.5, 0.5, 1))
                ))
                return
                
            for msg_data in messages:
                item = Factory.MessageItem(message_data=msg_data)
                messages_grid.add_widget(item)
                
        except Exception as e:
            print(f"Error populating messages grid: {e}")
            self.update_status(f"Error displaying messages: {e}", True)
            
        self.apply_theme_widgets()

    def save_message(self, *args):
        """Save a new message."""
        if not self.app.user_id:
            self.update_status("Error: No user session", True)
            return

        if not hasattr(self, 'ids'):
            return

        message = self.ids.message_input.text.strip()
        year = self.ids.year_spinner.text
        month_name = self.ids.month_spinner.text
        day = self.ids.day_spinner.text

        if not message or "Year" in year or "Month" in month_name or "Day" in day:
            self.show_popup("Input Error", "Please write a message and select a valid date.")
            return

        try:
            month_number = list(calendar.month_name).index(month_name)
            day_int = int(day)
            year_int = int(year)
            num_days = calendar.monthrange(year_int, month_number)[1]
            if not 1 <= day_int <= num_days:
                raise ValueError("Invalid day for month.")
            date_str = f"{year}-{month_number:02d}-{day_int:02d}"
            selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            if selected_date <= today:
                raise ValueError("Select a future date.")
        except ValueError as e:
            self.show_popup("Input Error", f"Invalid date: {e}")
            return
        except Exception as e:
            self.show_popup("Input Error", f"Date error: {e}")
            return

        self.update_status("Saving message...", False)
        url = f"{self.base_url}/inbox"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # include user_id in form data
        req_body = urlencode({
            'message': message,
            'date': date_str,
            'user_id': str(self.app.user_id)
        })
        
        print(f"Sending save message request to {url} with data: {req_body}")

        try:
            UrlRequest(url,
                      method='POST',
                      req_headers=headers,
                      req_body=req_body,
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_save_success, "Save failed"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to send save request: {e}", True)
            self.show_popup("Error", f"Failed to save message: {e}")

    def on_save_success(self, result):
        message = result.get('message', 'Message saved!'); error = result.get('error')
        if error: self.update_status(f"Error: {error}", True); self.show_popup("Save Error", error)
        else: self.update_status(message, False); self.ids.message_input.text = ""; self.fetch_data()

    def delete_message(self, message_id):
        """Delete a message."""
        if not self.app.user_id:
            self.update_status("Error: No user session", True)
            return

        self.update_status("Deleting message...", False)
        url = f"{self.base_url}/delete_message/{message_id}?user_id={self.app.user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Sending delete message request for ID {message_id} to {url}")
        
        try:
            UrlRequest(url,
                      method='DELETE',
                      req_headers=headers,
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_delete_message_success, "Delete failed"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to send delete request: {e}", True)
            self.show_popup("Error", f"Failed to delete message: {e}")

    def on_delete_message_success(self, result):
        self.update_status("Message deleted.", False); self.fetch_data()

    def go_to_dashboard(self, *args):
        self.manager.transition = FadeTransition(duration=0.2); self.manager.current = 'dashboard'

# profile screen
class ProfileScreen(BaseScreen):
    def on_enter(self, *args):
        """Called when the screen is entered"""
        super().on_enter(*args)
        self.load_profile_data()

    def load_profile_data(self):
        """Load and display the user's profile data"""
        try:
            app = App.get_running_app()
            if not app or not app.username:
                print("No user logged in")
                self.manager.current = 'login'
                return
                
            print(f"Loading profile data - Username: {app.username}")
            
            # Update the username display
            if hasattr(self, 'ids') and 'username_display' in self.ids:
                self.ids.username_display.text = app.username
                
        except Exception as e:
            print(f"Error loading profile data: {str(e)}")
            if hasattr(self, 'manager'):
                self.manager.current = 'login'

    def logout(self, *args):
        """Handle user logout"""
        print("Logging out user...")
        app = App.get_running_app()
        
        # Clear the stored credentials
        if app.store:
            app.store.delete('session')
        
        # clear the app's username and session data
        app.username = None
        app.user_id = None
        app.session_cookie = None
        
        # navigate to login screen
        self.manager.current = 'login'

    def go_to_dashboard(self, *args):
        """Navigate back to the dashboard"""
        self.manager.current = 'dashboard'

    def apply_theme_widgets(self):
        """Apply theme to profile screen widgets."""
        super().apply_theme_widgets()
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return

        if 'username_label' in self.ids: self.ids.username_label.color = colors.get('secondary_text')
        if 'username_input' in self.ids:
             self.ids.username_input.background_color = colors.get('input_background')
             self.ids.username_input.foreground_color = colors.get('input_text')
        if 'save_profile_button' in self.ids:
            self.ids.save_profile_button.background_color = colors.get('primary')
            self.ids.save_profile_button.color = colors.get('primary_text')
        if 'back_button' in self.ids:
            self.ids.back_button.background_color = colors.get('secondary')
            self.ids.back_button.color = colors.get('secondary_text')
        if 'logout_button' in self.ids:
            self.ids.logout_button.background_color = colors.get('error')
            self.ids.logout_button.color = colors.get('primary_text')

    def save_profile(self, *args):
        """Save username to local storage and navigate."""
        if not hasattr(self, 'ids') or 'username_input' not in self.ids: return
        username = self.ids.username_input.text.strip()

        if not re.match("^[A-Za-z0-9_]{3,15}$", username):
            self.update_status("Invalid username (3-15 chars, A-Z, a-z, 0-9, _)", True)
            self.show_popup("Invalid Username", "Username must be 3-15 characters long and contain only letters, numbers, or underscores.")
            return

        print(f"Saving profile for username: {username}")
        print(f"DEBUG save_profile: Check 1 - self.app is {self.app}")

        if self.app is None:
            print("save_profile: Check Failed - self.app is None!")
            self.update_status("Error: App reference lost.", True)
            return

        print(f"DEBUG save_profile: Check 2 - self.app.store is {getattr(self.app, 'store', 'N/A')}")
        if not hasattr(self.app, 'store') or self.app.store is None:
            print(f"save_profile: Store access failed!")
            self.update_status("Error: Cannot access storage.", True)
            return

        try:
            print(f"save_profile: Attempting to write to store: {self.app.store.filename}")
            self.app.store.put('profile', username=username)
            print("save_profile: Store put successful.")
            self.update_status("Profile saved successfully!", False)
            print("Navigating to dashboard after profile save.")
            Clock.schedule_once(self.go_to_dashboard, 0.5)
        except Exception as e:
            print(f"ERROR during store.put: {e}")
            self.update_status(f"Error writing to storage: {e}", True)
            self.show_popup("Storage Error", f"Could not save profile data: {e}")

# --- Login Screen ---
class LoginScreen(BaseScreen):
    def on_enter(self, *args):
        super().on_enter(*args)
        if hasattr(self, 'ids'):
            if 'login_username' in self.ids: self.ids.login_username.text = ""
            if 'login_password' in self.ids: self.ids.login_password.text = ""
            Clock.schedule_once(lambda dt: setattr(self.ids.login_username, 'focus', True), 0.2)

    def apply_theme_widgets(self):
        """Apply theme to login screen widgets."""
        super().apply_theme_widgets()
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return

        if 'login_username' in self.ids:
            self.ids.login_username.background_color = colors.get('input_background')
            self.ids.login_username.foreground_color = colors.get('input_text')
        if 'login_password' in self.ids:
            self.ids.login_password.background_color = colors.get('input_background')
            self.ids.login_password.foreground_color = colors.get('input_text')
        if 'login_button' in self.ids:
            self.ids.login_button.background_color = colors.get('primary')
            self.ids.login_button.color = colors.get('primary_text')
        if 'register_button' in self.ids:
            self.ids.register_button.background_color = colors.get('secondary')
            self.ids.register_button.color = (1, 1, 1, 1)  # White text

    def do_login(self):
        if not hasattr(self, 'ids'): return
        username = self.ids.login_username.text.strip()
        password = self.ids.login_password.text

        if not username or not password:
            self.update_status("Please enter both username and password", True)
            return

        if not re.match("^[A-Za-z0-9_]{3,15}$", username):
            self.update_status("Invalid username format (3-15 chars, letters, numbers, _)", True)
            return

        self.update_status("Logging in...", False)
        url = f"{self.base_url}/login"
        req_body = urlencode({
            'username': username,
            'password': password
        })
        print(f"Sending login request to {url} with data: {req_body}")

        try:
            UrlRequest(url, method='POST',
                      req_body=req_body,
                      req_headers={'Content-Type': 'application/x-www-form-urlencoded'},
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_login_success, "Login failed"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to send login request: {e}", True)
            self.show_popup("Error", f"Failed to login: {e}")

    def on_login_success(self, result):
        if not result.get('success'):
            error_msg = result.get('message', 'Login failed.')
            self.update_status(error_msg, True)
            if "No account found" in error_msg:
                self.show_popup("Account Not Found", 
                              f"{error_msg}\n\nWould you like to register a new account?")
            elif "Incorrect password" in error_msg:
                self.show_popup("Login Failed", error_msg)
            return

        # Store session data
        self.app.user_id = str(result.get('user_id'))
        self.app.username = self.ids.login_username.text.strip()
        self.app.session_cookie = result.get('session_cookie', '')

        try:
            self.app.store.put('session',
                             user_id=self.app.user_id,
                             username=self.app.username,
                             session_cookie=self.app.session_cookie)
            self.update_status("Login successful!", False)

            # Fetch scheduled messages for this user
            def show_scheduled_popup(messages):
                if not messages:
                    self.manager.transition = FadeTransition(duration=0.2)
                    self.manager.current = 'dashboard'
                    Clock.schedule_once(lambda dt: self.manager.get_screen('dashboard').fetch_data(), 0.5)
                    return
                # Show the first message in a pretty popup
                msg = messages[0]
                class BlueBox(BoxLayout):
                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)
                        with self.canvas.before:
                            Color(0.2, 0.6, 0.8, 1)  # Blue
                            self.bg_rect = RoundedRectangle(radius=[20], pos=self.pos, size=self.size)
                        self.bind(pos=self._update_bg, size=self._update_bg)
                    def _update_bg(self, *args):
                        self.bg_rect.pos = self.pos
                        self.bg_rect.size = self.size
                content = BlueBox(orientation='vertical', padding=30, spacing=20, size_hint=(1, 1), height=350)
                title_label = Label(
                    text=f"[b][i]Scheduled Message[/i][/b]",
                    font_size='22sp',
                    color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=50,
                    halign='center',
                    valign='middle',
                    text_size=(self.app.root.width * 0.8, None),
                    markup=True
                )
                fact_label = Label(
                    text=msg['message'],
                    font_size='17sp',
                    color=(1, 1, 1, 1),
                    text_size=(self.app.root.width * 0.8, 200),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=200
                )
                close_button = Button(
                    text='Close',
                    size_hint=(None, None),
                    size=(120, 48),
                    pos_hint={'center_x': 0.5},
                    background_color=(0.1, 0.5, 0.2, 1),
                    color=(1,1,1,1),
                    bold=True,
                    font_size='16sp',
                    background_normal='',
                    background_down='',
                )
                content.add_widget(title_label)
                content.add_widget(fact_label)
                content.add_widget(close_button)
                popup = Popup(
                    title='',
                    content=content,
                    size_hint=(0.9, None),
                    height=420,
                    auto_dismiss=True,
                    background_color=(0,0,0,0),  # Fully transparent
                    separator_height=0,
                )
                def after_close(instance):
                    # Optionally, delete the message from the server so it doesn't show again
                    url = f"{self.app.base_url}/delete_message/{msg['id']}?user_id={self.app.user_id}"
                    UrlRequest(url, method='DELETE')
                    # If there are more messages, show the next one
                    if len(messages) > 1:
                        show_scheduled_popup(messages[1:])
                    else:
                        self.manager.transition = FadeTransition(duration=0.2)
                        self.manager.current = 'dashboard'
                        Clock.schedule_once(lambda dt: self.manager.get_screen('dashboard').fetch_data(), 0.5)
                close_button.bind(on_release=lambda inst: (popup.dismiss(), after_close(inst)))
                popup.open()
        except Exception as e:
            # Suppress error message if session saving fails, but continue as normal
            self.update_status("Login successful!", False)
            self.manager.transition = FadeTransition(duration=0.2)
            self.manager.current = 'dashboard'

    def go_to_dashboard(self, *args):
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'dashboard'

    def go_to_register(self, *args):
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'register'

# --- Register Screen ---
class RegisterScreen(BaseScreen):
    def on_enter(self, *args):
        super().on_enter(*args)
        if hasattr(self, 'ids'):
            if 'register_username' in self.ids: self.ids.register_username.text = ""
            if 'register_password' in self.ids: self.ids.register_password.text = ""
            if 'confirm_password' in self.ids: self.ids.confirm_password.text = ""
            Clock.schedule_once(lambda dt: setattr(self.ids.register_username, 'focus', True), 0.2)

    def apply_theme_widgets(self):
        """Apply theme to register screen widgets."""
        super().apply_theme_widgets()
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return

        if 'register_username' in self.ids:
            self.ids.register_username.background_color = colors.get('input_background')
            self.ids.register_username.foreground_color = colors.get('input_text')
        if 'register_password' in self.ids:
            self.ids.register_password.background_color = colors.get('input_background')
            self.ids.register_password.foreground_color = colors.get('input_text')
        if 'confirm_password' in self.ids:
            self.ids.confirm_password.background_color = colors.get('input_background')
            self.ids.confirm_password.foreground_color = colors.get('input_text')
        if 'register_button' in self.ids:
            self.ids.register_button.background_color = colors.get('primary')
            self.ids.register_button.color = colors.get('primary_text')
        if 'login_button' in self.ids:
            self.ids.login_button.background_color = colors.get('secondary')
            self.ids.login_button.color = (1, 1, 1, 1)  # White text

    def do_register(self):
        if not hasattr(self, 'ids'): return
        username = self.ids.register_username.text.strip()
        password = self.ids.register_password.text
        confirm_password = self.ids.confirm_password.text

        if not username or not password or not confirm_password:
            self.update_status("All fields are required.", True)
            return

        if not re.match("^[A-Za-z0-9_]{3,15}$", username):
            self.update_status("Username: 3-15 chars (letters, numbers, _).", True)
            return

        if not re.match("^[A-Za-z0-9]{4,}$", password):
            self.update_status("Password: 4+ chars (letters, numbers).", True)
            return

        if password != confirm_password:
            self.update_status("Passwords do not match.", True)
            return

        self.update_status("Registering...", False)
        url = f"{self.base_url}/register"
        req_body = urlencode({
            'username': username,
            'password': password
        })
        print(f"Sending registration request to {url} with data: {req_body}")

        try:
            UrlRequest(url, method='POST',
                      req_body=req_body,
                      req_headers={'Content-Type': 'application/x-www-form-urlencoded'},
                      on_success=lambda req, res: self.handle_network_response(req, res, self.on_register_success, "Registration failed"),
                      on_failure=self.on_network_failure,
                      on_error=self.on_network_error,
                      timeout=10)
        except Exception as e:
            self.update_status(f"Failed to send registration request: {e}", True)
            self.show_popup("Error", f"Failed to register: {e}")

    def on_register_success(self, result):
        if not result.get('success'):
            self.update_status(result.get('message', 'Registration failed.'), True)
            return

        # Store session data - convert user_id to string
        self.app.user_id = str(result.get('user_id'))  # Convert to string
        self.app.username = self.ids.register_username.text.strip()
        self.app.session_cookie = result.get('session_cookie', '')

        try:
            self.app.store.put('session',
                             user_id=self.app.user_id,
                             username=self.app.username,
                             session_cookie=self.app.session_cookie)
            self.update_status("Registration successful!", False)
            # Navigate to dashboard and ensure habits are fetched
            self.manager.transition = FadeTransition(duration=0.2)
            self.manager.current = 'dashboard'
            # Schedule habit fetch after navigation
            Clock.schedule_once(lambda dt: self.manager.get_screen('dashboard').fetch_data(), 0.5)
        except Exception as e:
            # Suppress error message if session saving fails, but continue as normal
            self.update_status("Registration successful!", False)
            self.manager.transition = FadeTransition(duration=0.2)
            self.manager.current = 'dashboard'

    def go_to_dashboard(self, *args):
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'dashboard'

    def go_to_login(self, *args):
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'login'

# --- Message Screen ---
class MessageScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_id = None
        self.message_text = None

    def on_enter(self, *args):
        """Called when the screen is entered"""
        super().on_enter(*args)
        if hasattr(self, 'ids'):
            if 'message_content' in self.ids:
                self.ids.message_content.text = self.message_text if self.message_text else "No message content"

    def apply_theme_widgets(self):
        """Apply theme to message screen widgets."""
        super().apply_theme_widgets()
        if not self.app: return
        colors = self.app.theme_colors
        if not hasattr(self, 'ids'): return

        if 'message_content' in self.ids:
            self.ids.message_content.color = colors.get('secondary_text')
        if 'back_button' in self.ids:
            self.ids.back_button.background_color = colors.get('secondary')
            self.ids.back_button.color = colors.get('secondary_text')

    def go_to_inbox(self, *args):
        """Navigate back to inbox screen"""
        self.manager.transition = FadeTransition(duration=0.2)
        self.manager.current = 'inbox'

# --- Main App Class (Line ~915 approx) ---
class HabitApp(App):
    user_id = StringProperty('')
    base_url = StringProperty(BASE_URL)
    theme_colors = DictProperty(light_theme)
    
    def build(self):
        # set window title
        self.title = 'Habit Free'
        
        # create screen manager
        sm = ScreenManager(transition=FadeTransition())
        
        # add screens
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(AddHabitScreen(name='add_habit'))
        sm.add_widget(InboxScreen(name='inbox'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(MessageScreen(name='message'))
        return sm
    
    def on_start(self):
        # check if user is already logged in
        store = JsonStore('habitapp.json')
        if store.exists('user'):
            user_data = store.get('user')
            self.user_id = user_data.get('user_id', '')
            if self.user_id:
                self.root.current = 'dashboard'

# --- Run App (Line ~966 approx) ---
if __name__ == '__main__':
    print("Starting HabitApp...")
    HabitApp().run()

# --- End of Complete app_kivy.py ---