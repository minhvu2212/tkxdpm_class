from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import json
import random
import time
import threading

class Activity:
    def __init__(self, name: str, duration: int, description: str, category: str):
        self.name = name
        self.duration = duration
        self.description = description
        self.category = category

    def get_instructions(self) -> str:
        return f"{self.name} ({self.duration} phút): {self.description}"

class ActivityManager:
    def __init__(self):
        self.activities = [
            Activity("Bài tập mắt", 2, "Nhắm mắt 20 giây, nhìn xa 20 giây", "Thể dục"),
            Activity("Yoga cơ bản", 5, "Thực hiện các động tác căng cơ đơn giản", "Thể dục"),
            Activity("Nghe nhạc thư giãn", 5, "Nghe một bài nhạc nhẹ nhàng", "Giải trí"),
            Activity("Đi bộ", 3, "Đi bộ quanh phòng hoặc hành lang", "Thể dục"),
            Activity("Uống nước", 1, "Uống một cốc nước lớn", "Sức khỏe")
        ]

    def get_random_activity(self) -> Activity:
        return random.choice(self.activities)

class Settings:
    def __init__(self):
        self.work_duration = 50  # minutes
        self.break_duration = 10  # minutes
        self.force_break = True
        self.notification_sound = True
        
    def save_settings(self):
        settings_dict = {
            "work_duration": self.work_duration,
            "break_duration": self.break_duration,
            "force_break": self.force_break,
            "notification_sound": self.notification_sound
        }
        with open("settings.json", "w") as f:
            json.dump(settings_dict, f)

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings_dict = json.load(f)
                self.__dict__.update(settings_dict)
        except FileNotFoundError:
            pass  # Use default settings

class Break:
    def __init__(self, duration: int):
        self.duration = duration
        self.start_time = None
        self.end_time = None
        self.activity = None
        self.completed = False

    def start_break(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration)

    def end_break(self):
        self.completed = True

class WorkSession:
    def __init__(self, duration: int):
        self.duration = duration
        self.start_time = None
        self.breaks_taken = []
        self.status = "inactive"

    def start_session(self):
        self.start_time = datetime.now()
        self.status = "active"

    def add_break(self, break_obj: Break):
        self.breaks_taken.append(break_obj)

class ForceBreakWindow:
    def __init__(self, duration: int, activity: Activity):
        self.window = tk.Tk()
        self.window.title("Thời gian nghỉ giải lao!")
        self.window.attributes('-fullscreen', True)
        self.time_remaining = duration * 60
        self.activity = activity
        self.setup_ui()

    def setup_ui(self):
        self.window.configure(bg='lightblue')
        
        # Title
        title = tk.Label(
            self.window,
            text="Đã đến giờ nghỉ giải lao!",
            font=("Arial", 24, "bold"),
            bg='lightblue'
        )
        title.pack(pady=50)

        # Activity
        activity_text = tk.Label(
            self.window,
            text=f"Hoạt động đề xuất:\n{self.activity.get_instructions()}",
            font=("Arial", 18),
            bg='lightblue',
            wraplength=600
        )
        activity_text.pack(pady=30)

        # Timer
        self.timer_label = tk.Label(
            self.window,
            font=("Arial", 20),
            bg='lightblue'
        )
        self.timer_label.pack(pady=20)

    def update_timer(self):
        if self.time_remaining > 0:
            mins, secs = divmod(self.time_remaining, 60)
            self.timer_label.config(text=f"Thời gian còn lại: {mins:02d}:{secs:02d}")
            self.time_remaining -= 1
            self.window.after(1000, self.update_timer)
        else:
            self.window.destroy()

    def show(self):
        self.update_timer()
        self.window.mainloop()

class NotificationManager:
    def __init__(self, sound_enabled: bool):
        self.sound_enabled = sound_enabled

    def show_notification(self, title: str, message: str):
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()

    def show_force_break(self, duration: int, activity: Activity):
        break_window = ForceBreakWindow(duration, activity)
        break_window.show()

class BreakReminder:
    def __init__(self):
        self.settings = Settings()
        self.settings.load_settings()
        self.activity_manager = ActivityManager()
        self.notification_manager = NotificationManager(self.settings.notification_sound)
        self.current_session = None
        self.running = False

    def start_monitoring(self):
        self.running = True
        self.current_session = WorkSession(self.settings.work_duration)
        self.current_session.start_session()
        
        monitoring_thread = threading.Thread(target=self._monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()

    def _monitoring_loop(self):
        while self.running:
            time.sleep(self.settings.work_duration * 60)  # Convert to seconds
            
            if not self.running:
                break

            # Create and start break
            break_obj = Break(self.settings.break_duration)
            activity = self.activity_manager.get_random_activity()
            break_obj.activity = activity
            
            # Show notification
            self.notification_manager.show_notification(
                "Thời gian nghỉ giải lao",
                f"Đã đến lúc nghỉ {self.settings.break_duration} phút!"
            )

            if self.settings.force_break:
                self.notification_manager.show_force_break(
                    self.settings.break_duration,
                    activity
                )

            # Add break to session
            self.current_session.add_break(break_obj)

    def stop_monitoring(self):
        self.running = False
        if self.current_session:
            self.current_session.status = "inactive"

if __name__ == "__main__":
    reminder = BreakReminder()
    reminder.start_monitoring()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reminder.stop_monitoring()