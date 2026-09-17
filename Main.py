import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import time, threading, psutil, csv, random
from datetime import datetime, timedelta

# Optional plotting dependency for statistics visualization
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

HISTORY_FILE = "history.csv"
SETTINGS_FILE = "settings.json"

# Default games to monitor
GAMES = ["RobloxPlayerBeta.exe", "valorant.exe", "Minecraft.exe"]

# Retro neon palette
COLORS = {
    "bg": "#243447",
    "sidebar": "#541388",
    "highlight": "#ffd400",
    "text": "#e5e5e5",
    "card1": "#1b998b",
    "card2": "#ff006e",
    "card3": "#3a86ff"
}

# Health recommendations
HEALTH_TIPS = [
    "💧 Hydration Check: Drink some water!",
    "👀 Eye Care: Look away from the screen for 20 seconds",
    "🧘 Posture Check: Sit up straight and adjust your posture",
    "🤸 Stretch Break: Stand up and stretch your arms and legs",
    "🌬️ Deep Breathing: Take 3 deep breaths",
    "🚶 Movement: Walk around for a minute",
    "💪 Quick Exercise: Do 10 jumping jacks or squats",
    "🧠 Mental Break: Close your eyes and relax for 30 seconds",
    "👐 Hand Exercise: Flex and stretch your fingers",
    "🦴 Neck Roll: Gently roll your neck in circles"
]

class GamerGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GamerGuard – Enhanced Edition")
        self.geometry("1100x650")
        self.configure(bg=COLORS["bg"])
        
        # Global session state
        self.running = False
        self.start_time = None
        self.current_game = None
        self.history = []  # list of dicts: {'user', 'game', 'duration', 'start', 'end', 'date'}
        self.daily_limit = 120
        self.health_interval = 30
        self.last_health_tip = None
        self.break_reminder = 60
        self.last_break_reminder = None
        self.notifications_enabled = True
        self.sound_alerts = True
        self.limit_reached_notified = False
        self.predicted_playtime = 0
        self.addiction_risk = "Low"
        self.adapted_limit_last_checked = None

        self.monitored_games = list(GAMES)
        self.current_user = None
        self.load_settings()

        # Sidebar
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="🎮 GamerGuard", fg=COLORS["highlight"],
                 bg=COLORS["sidebar"], font=("Press Start 2P", 14)).pack(pady=30)
        
        buttons = [("Dashboard", self.show_dashboard),
                   ("Live Monitor", self.show_monitor),
                   ("History", self.show_history),
                   ("Settings", self.show_settings),
                   ("Statistics", self.show_statistics),
                   ("About", self.show_about)]
        
        for text, cmd in buttons:
            tk.Button(sidebar, text=text, command=cmd,
                      fg=COLORS["text"], bg=COLORS["sidebar"], relief="flat",
                      font=("Press Start 2P", 10),
                      activebackground=COLORS["highlight"], height=2).pack(pady=10, fill="x")
        
        self.container = tk.Frame(self, bg=COLORS["bg"])
        self.container.pack(side="left", fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        
        self.pages = {}
        for PageClass in (LoginPage, SignUpPage, DashboardPage, MonitorPage, HistoryPage, SettingsPage, StatisticsPage, AboutPage):
            page = PageClass(self.container, self)
            self.pages[PageClass.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.load_history()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.show_page("LoginPage")
    
    def show_page(self, page_name):
        page = self.pages[page_name]
        page.update_page()
        page.tkraise()
    
    def show_dashboard(self): self.show_page("DashboardPage")
    def show_monitor(self): self.show_page("MonitorPage")
    def show_history(self): self.show_page("HistoryPage")
    def show_settings(self): self.show_page("SettingsPage")
    def show_statistics(self): self.show_page("StatisticsPage")
    def show_about(self): self.show_page("AboutPage")
    def show_login(self): self.show_page("LoginPage")
    def show_signup(self): self.show_page("SignUpPage")
    def logout(self):
        self.current_user = None
        self.load_settings()  # reload global/default settings
        self.show_login()
    
    def start_monitoring(self):
        if self.running: return
        self.running = True
        self.limit_reached_notified = False
        self.last_health_tip = time.time()
        self.last_break_reminder = time.time()
        self.after(0, lambda: self.pages["MonitorPage"].status_var.set("Monitoring..."))
        self.pages["MonitorPage"].start_btn.config(state="disabled")
        self.pages["MonitorPage"].stop_btn.config(state="normal")
        self.pages["MonitorPage"].pause_btn.config(state="normal")
        threading.Thread(target=self.monitor_games, daemon=True).start()
    
    def stop_monitoring(self):
        if self.running and self.current_game and self.start_time:
            end_time = time.time()
            duration = int((end_time - self.start_time) / 60)
            if duration >= 0:
                start_dt = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
                end_dt = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                session = {
                    'user': self.current_user or '',
                    'game': self.current_game,
                    'duration': duration,
                    'start': start_dt,
                    'end': end_dt,
                    'date': date_str
                }
                self.history.append(session)
                self.save_history_record(self.current_game, duration, start_dt, end_dt, date_str)
                if 'HistoryPage' in self.pages:
                    self.pages['HistoryPage'].add_entry(session)
                self.adapt_daily_limit()
                self.assess_addiction_risk()

        self.running = False
        self.current_game = None
        self.start_time = None

        self.after(0, lambda: self.pages["MonitorPage"].status_var.set("Stopped"))
        self.after(0, lambda: self.pages["MonitorPage"].timer_var.set("00:00"))
        self.pages["MonitorPage"].update_progress(0, 0)
        self.pages["MonitorPage"].start_btn.config(state="normal")
        self.pages["MonitorPage"].stop_btn.config(state="disabled")
        self.pages["MonitorPage"].pause_btn.config(state="disabled")
        self.save_settings()
    
    def pause_monitoring(self):
        if self.running:
            self.running = False
            paused_msg = "Paused"
            if self.current_game:
                paused_msg = f"{self.current_game} (Paused)"
            self.after(0, lambda: self.pages["MonitorPage"].status_var.set(paused_msg))
            self.pages["MonitorPage"].pause_btn.config(text="RESUME")
        else:
            self.running = True
            game = self.detect_game()
            self.after(0, lambda: self.pages["MonitorPage"].status_var.set(f"{game} Running"))
            self.pages["MonitorPage"].pause_btn.config(text="PAUSE")
            threading.Thread(target=self.monitor_games, daemon=True).start()

    def on_closing(self):
        # Save any running session and settings on exit
        if self.running:
            self.stop_monitoring()
        else:
            self.save_settings()

        self.destroy()
    
    def monitor_games(self):
        while self.running:
            game = self.detect_game()
            
            if game and not self.current_game:
                self.current_game = game
                self.start_time = time.time()
                self.after(0, lambda: self.pages["MonitorPage"].status_var.set(f"{game} Running"))
            
            elif not game and self.current_game:
                end_time = time.time()
                duration = int((end_time - self.start_time) / 60)
                start_dt = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
                end_dt = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                session = {
                    'user': self.current_user or '',
                    'game': self.current_game,
                    'duration': duration,
                    'start': start_dt,
                    'end': end_dt,
                    'date': date_str
                }
                self.history.append(session)
                self.save_history_record(self.current_game, duration, start_dt, end_dt, date_str)

                self.pages["HistoryPage"].add_entry(session)
                self.adapt_daily_limit()
                self.assess_addiction_risk()
                self.after(0, lambda: self.pages["MonitorPage"].status_var.set(f"Game Closed"))
                self.current_game = None
            
            if self.current_game:
                elapsed = int(time.time() - self.start_time)
                
                # Health tip notification
                if self.notifications_enabled and time.time() - self.last_health_tip >= self.health_interval * 60:
                    self.show_health_tip()
                    self.last_health_tip = time.time()
                
                # Break reminder
                if self.notifications_enabled and time.time() - self.last_break_reminder >= self.break_reminder * 60:
                    self.show_break_reminder()
                    self.last_break_reminder = time.time()
                
                # Daily limit check
                today_total, _, _ = self.get_today_stats()
                current_session_mins = elapsed // 60
                total_today = today_total + current_session_mins
                
                if self.notifications_enabled and total_today >= self.daily_limit and not self.limit_reached_notified:
                    self.show_limit_notification()
                    self.limit_reached_notified = True
            else:
                elapsed = 0
            
            mins, secs = divmod(elapsed, 60)
            self.after(0, lambda: self.pages["MonitorPage"].timer_var.set(f"{mins:02d}:{secs:02d}"))
            
            # Update progress bar
            today_total, _, _ = self.get_today_stats()
            current_session_mins = elapsed // 60
            total_today = today_total + current_session_mins
            progress = min(100, (total_today / self.daily_limit) * 100)
            self.after(0, lambda: self.pages["MonitorPage"].update_progress(progress, total_today))
            
            time.sleep(1)
    
    def detect_game(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in self.monitored_games:
                    return proc.info["name"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def _show_topmost_message(self, fn, title, msg):
        self.attributes("-topmost", True)
        fn(title, msg, parent=self)
        self.attributes("-topmost", False)

    def show_health_tip(self):
        tip = random.choice(HEALTH_TIPS)
        self.after(0, lambda: self._show_topmost_message(messagebox.showinfo, "Health Reminder", tip))
        if self.sound_alerts:
            self.bell()

    def show_break_reminder(self):
        self.after(0, lambda: self._show_topmost_message(messagebox.showwarning, "Break Time!", "🛑 You've been gaming for a while.\nTake a 5-minute break!"))
        if self.sound_alerts:
            self.bell()

    def show_limit_notification(self):
        self.after(0, lambda: self._show_topmost_message(messagebox.showwarning, "Daily Limit Reached", 
                              f"⚠️ You've reached your daily limit of {self.daily_limit} minutes!\n\nConsider taking a longer break."))
        if self.sound_alerts:
            self.bell()

    def load_settings(self):
        # Load global settings and (optionally) user-specific settings
        if not os.path.isfile(SETTINGS_FILE):
            return

        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)

            # Global defaults
            self.daily_limit = int(cfg.get('daily_limit', self.daily_limit))
            self.health_interval = int(cfg.get('health_interval', self.health_interval))
            self.break_reminder = int(cfg.get('break_reminder', self.break_reminder))
            self.notifications_enabled = bool(cfg.get('notifications_enabled', self.notifications_enabled))
            self.sound_alerts = bool(cfg.get('sound_alerts', self.sound_alerts))

            global_games = cfg.get('games', [])
            if isinstance(global_games, list) and global_games:
                self.monitored_games = list(global_games)
                global GAMES
                GAMES = list(global_games)

            if self.current_user:
                self.load_user_settings()
        except Exception:
            pass

    def load_user_settings(self):
        if not self.current_user:
            return

        if not os.path.isfile(SETTINGS_FILE):
            return

        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)

            users_cfg = cfg.get('users', {})
            user_cfg = users_cfg.get(self.current_user, {})
            if user_cfg:
                self.daily_limit = int(user_cfg.get('daily_limit', self.daily_limit))
                self.health_interval = int(user_cfg.get('health_interval', self.health_interval))
                self.break_reminder = int(user_cfg.get('break_reminder', self.break_reminder))
                self.notifications_enabled = bool(user_cfg.get('notifications_enabled', self.notifications_enabled))
                self.sound_alerts = bool(user_cfg.get('sound_alerts', self.sound_alerts))

            if isinstance(user_cfg.get('games'), list) and user_cfg.get('games'):
                self.monitored_games = list(user_cfg.get('games'))
                global GAMES
                GAMES = list(user_cfg.get('games'))
        except Exception:
            pass

    def save_settings(self):
        try:
            cfg = {}
            if os.path.isfile(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    try:
                        cfg = json.load(f)
                    except Exception:
                        cfg = {}

            # Global settings
            cfg.setdefault('games', self.monitored_games)
            cfg['games'] = list(self.monitored_games)

            cfg['daily_limit'] = self.daily_limit
            cfg['health_interval'] = self.health_interval
            cfg['break_reminder'] = self.break_reminder
            cfg['notifications_enabled'] = self.notifications_enabled
            cfg['sound_alerts'] = self.sound_alerts

            if self.current_user:
                cfg.setdefault('users', {})
                cfg['users'][self.current_user] = {
                    'daily_limit': self.daily_limit,
                    'health_interval': self.health_interval,
                    'break_reminder': self.break_reminder,
                    'notifications_enabled': self.notifications_enabled,
                    'sound_alerts': self.sound_alerts,
                    'games': list(self.monitored_games)
                }

            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def load_history(self):
        if not os.path.isfile(HISTORY_FILE) or os.path.getsize(HISTORY_FILE) == 0:
            # Preload history.csv with sample data for display
            now = datetime.now()
            sample_sessions = [
                {
                    'User': 'player1',
                    'Game': 'RobloxPlayerBeta.exe',
                    'Duration': 45,
                    'Start': (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                    'End': (now - timedelta(hours=2, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                    'Date': (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
                },
                {
                    'User': 'player1',
                    'Game': 'Minecraft.exe',
                    'Duration': 30,
                    'Start': (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                    'End': (now - timedelta(days=1, hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                    'Date': (now - timedelta(days=1, hours=2)).strftime("%Y-%m-%d %H:%M")
                },
                {
                    'User': 'player2',
                    'Game': 'valorant.exe',
                    'Duration': 60,
                    'Start': (now - timedelta(days=2, hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
                    'End': (now - timedelta(days=2, hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                    'Date': (now - timedelta(days=2, hours=4)).strftime("%Y-%m-%d %H:%M")
                }
            ]
            try:
                with open(HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['User', 'Game', 'Duration', 'Start', 'End', 'Date']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for entry in sample_sessions:
                        writer.writerow(entry)
            except Exception as e:
                print(f"Failed to create initial history file: {e}")

        try:
            with open(HISTORY_FILE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_obj = {
                        'user': row.get('User', ''),
                        'game': row.get('Game', ''),
                        'duration': int(row.get('Duration', 0)),
                        'start': row.get('Start', ''),
                        'end': row.get('End', ''),
                        'date': row.get('Date', '')
                    }
                    self.history.append(row_obj)
                    if 'HistoryPage' in self.pages:
                        self.pages['HistoryPage'].add_entry(row_obj)
        except Exception as e:
            print(f"Failed to load history: {e}")

    def save_history_record(self, game, duration, start_ts, end_ts, date_str):
        record = {
            'User': self.current_user or '',
            'Game': game,
            'Duration': duration,
            'Start': start_ts,
            'End': end_ts,
            'Date': date_str
        }

        header_needed = not os.path.isfile(HISTORY_FILE)
        try:
            with open(HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['User', 'Game', 'Duration', 'Start', 'End', 'Date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if header_needed:
                    writer.writeheader()
                writer.writerow(record)
        except Exception as e:
            print(f"Failed to save history record: {e}")

    def get_current_user_history(self):
        if self.current_user:
            return [s for s in self.history if s.get('user', '') == self.current_user]
        return self.history

    def get_today_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        user_history = self.get_current_user_history()
        today_sessions = [s for s in user_history if s.get('date', '').startswith(today)]
        total = sum(s.get('duration', 0) for s in today_sessions)
        longest = max((s.get('duration', 0) for s in today_sessions), default=0)
        breaks = len(today_sessions)
        return total, longest, breaks
    
    def get_week_stats(self):
        week_ago = datetime.now() - timedelta(days=7)
        week_sessions = []
        for s in self.get_current_user_history():
            try:
                if datetime.strptime(s.get('start', ''), "%Y-%m-%d %H:%M:%S") >= week_ago:
                    week_sessions.append(s)
            except Exception:
                continue
        total = sum(s.get('duration', 0) for s in week_sessions)
        avg = total // 7 if week_sessions else 0
        return total, avg, len(week_sessions)

    def predict_today_playtime(self):
        today_total, _, _ = self.get_today_stats()
        # use historical daily totals to estimate
        day_counts = {}
        for s in self.history:
            date = s.get('date', '').split(' ')[0]
            if date:
                day_counts.setdefault(date, 0)
                day_counts[date] += s.get('duration', 0)

        values = list(day_counts.values())
        if not values:
            self.predicted_playtime = today_total
            return today_total

        avg_day = sum(values) / len(values)
        predicted = int((today_total + avg_day) / 2 if today_total > 0 else avg_day)
        self.predicted_playtime = max(today_total, predicted)
        return self.predicted_playtime

    def adapt_daily_limit(self):
        now = datetime.now().date()
        if self.adapted_limit_last_checked == now:
            return

        self.adapted_limit_last_checked = now
        day_totals = {}
        for s in self.get_current_user_history():
            d = s.get('date', '').split(' ')[0]
            if d:
                day_totals.setdefault(d, 0)
                day_totals[d] += s.get('duration', 0)

        last_7_days = sorted(day_totals.items(), reverse=True)[:7]
        over_count = sum(1 for _, total in last_7_days if total > self.daily_limit)
        disciplined_count = sum(1 for _, total in last_7_days if total <= self.daily_limit)

        if over_count >= 3:
            self.daily_limit = max(30, int(self.daily_limit * 0.9))
        elif disciplined_count >= 5:
            self.daily_limit = min(240, int(self.daily_limit * 1.05) + 1)

        # Retain integer and avoid value drift
        self.daily_limit = int(self.daily_limit)

    def assess_addiction_risk(self):
        today_total, _, sessions = self.get_today_stats()
        last_week_total, _, last_week_sessions = self.get_week_stats()

        score = 0
        score += min(5, sessions // 2)
        score += min(5, today_total // 30)

        no_breaks = sessions <= 1 and today_total > 90
        if no_breaks:
            score += 2

        long_sessions = sum(1 for s in self.get_current_user_history() if s.get('duration', 0) >= 90 and s.get('date', '').startswith(datetime.now().strftime('%Y-%m-%d')))
        score += min(3, long_sessions)

        if today_total > self.daily_limit * 1.2 or last_week_total > self.daily_limit * 5:
            score += 2

        if score >= 12:
            self.addiction_risk = "Critical"
        elif score >= 8:
            self.addiction_risk = "High"
        elif score >= 4:
            self.addiction_risk = "Medium"
        else:
            self.addiction_risk = "Low"

        return self.addiction_risk

    def get_smart_tip(self, session_minutes):
        hour = datetime.now().hour
        if session_minutes >= 60:
            return "Long session detected – take a 10-minute break, drink water, and stretch."
        if 22 <= hour or hour < 6:
            return "It’s late—consider winding down and getting sleep soon."
        if session_minutes <= 20:
            return "Short session: do a light stretch and maintain good posture for the next play."

        # else pick an existing tip with priority for healthy maintenance
        return random.choice(HEALTH_TIPS)

    def show_health_tip(self):
        elapsed = 0
        if self.current_game and self.start_time:
            elapsed = int((time.time() - self.start_time) / 60)

        tip = self.get_smart_tip(elapsed)
        self.after(0, lambda: messagebox.showinfo("Health Reminder", tip))
        if self.sound_alerts:
            self.bell()

    def export_history(self):
        if not self.history:
            self.after(0, lambda: messagebox.showinfo("Export", "No history to export!"))
            return
        
        filename = f"gamerguard_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['User', 'Game', 'Duration', 'Start', 'End', 'Date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for session in self.history:
                    writer.writerow({
                        'User': session.get('user', ''),
                        'Game': session.get('game', ''),
                        'Duration': session.get('duration', 0),
                        'Start': session.get('start', ''),
                        'End': session.get('end', ''),
                        'Date': session.get('date', '')
                    })
            self.after(0, lambda: messagebox.showinfo("Export Successful", f"History exported to {filename}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Export Failed", f"Error: {str(e)}"))

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True)

        tk.Label(container, text="🎮 GAMERGUARD LOGIN",
                 fg=COLORS["highlight"], bg=COLORS["bg"],
                 font=("Press Start 2P", 20)).pack(pady=20)

        tk.Label(container, text="Username", bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=5)
        self.username = tk.Entry(container)
        self.username.pack(pady=5)

        tk.Label(container, text="Password", bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=5)
        self.password = tk.Entry(container, show="*")
        self.password.pack(pady=5)

        tk.Button(container, text="LOGIN",
                  command=self.login,
                  bg=COLORS["highlight"]).pack(pady=20)

    def login(self):
        user = self.username.get()
        pwd = self.password.get()
        print(type(self.controller))

        with open("users.csv") as f:
            for line in f.readlines()[1:]:
                u, p = line.strip().split(",")
                if u == user and p == pwd:
                    self.controller.current_user = user
                    self.controller.load_user_settings()
                    self.controller.show_dashboard()
                    return

        messagebox.showerror("Login Failed", "Invalid credentials")

    def update_page(self):
        pass


class SignUpPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True)

        tk.Label(container, text="📝 SIGN UP",
                 fg=COLORS["highlight"], bg=COLORS["bg"],
                 font=("Press Start 2P", 20)).pack(pady=20)

        tk.Label(container, text="Username", bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
        self.username = tk.Entry(container)
        self.username.pack(pady=5)

        tk.Label(container, text="Password", bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
        self.password = tk.Entry(container, show="*")
        self.password.pack(pady=5)

        tk.Label(container, text="Confirm Password", bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
        self.confirm = tk.Entry(container, show="*")
        self.confirm.pack(pady=5)

        tk.Button(container, text="CREATE ACCOUNT", command=self.signup,
                  bg=COLORS["highlight"], fg="black").pack(pady=20)

        tk.Button(container, text="BACK TO LOGIN", command=controller.show_login,
                  bg=COLORS["card2"], fg="black").pack(pady=5)

    def signup(self):
        username = self.username.get().strip()
        password = self.password.get().strip()
        confirm = self.confirm.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return

        users_file = "users.csv"
        existing = set()
        if os.path.isfile(users_file):
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    parts = line.strip().split(",")
                    if parts:
                        existing.add(parts[0].strip())
            except Exception:
                pass

        if username in existing:
            messagebox.showerror("Error", "Username already exists")
            return

        try:
            write_header = not os.path.isfile(users_file)
            with open(users_file, 'a', newline='', encoding='utf-8') as f:
                if write_header:
                    f.write("username,password\n")
                f.write(f"{username},{password}\n")
            self.controller.current_user = username
            self.controller.load_user_settings()
            messagebox.showinfo("Success", "Account created successfully")
            self.controller.show_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save user data: {e}")

    def update_page(self):
        self.username.delete(0, "end")
        self.password.delete(0, "end")
        self.confirm.delete(0, "end")


class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True, fill="both")

        top_bar = tk.Frame(container, bg=COLORS["bg"])
        top_bar.pack(fill="x", pady=10, padx=20)

        self.user_label = tk.Label(top_bar, text=f"User: {controller.current_user or 'Guest'}",
                                   fg=COLORS["text"], bg=COLORS["bg"], font=("Press Start 2P", 10))
        self.user_label.pack(side="left")

        auth_frame = tk.Frame(top_bar, bg=COLORS["bg"])
        auth_frame.pack(side="right")
        tk.Button(auth_frame, text="Login", command=controller.show_login,
                  fg="black", bg=COLORS["card1"], font=("Press Start 2P", 9), width=10).pack(side="left", padx=5)
        tk.Button(auth_frame, text="Sign Up", command=controller.show_signup,
                  fg="black", bg=COLORS["card2"], font=("Press Start 2P", 9), width=10).pack(side="left", padx=5)
        tk.Button(auth_frame, text="Logout", command=controller.logout,
                  fg="black", bg=COLORS["card3"], font=("Press Start 2P", 9), width=10).pack(side="left", padx=5)

        title = tk.Label(container, text="📊 DASHBOARD", fg=COLORS["highlight"],
                         bg=COLORS["bg"], font=("Press Start 2P", 22))
        title.pack(pady=20)
        
        cards = tk.Frame(container, bg=COLORS["bg"])
        cards.pack(pady=30)
        
        self.stats1 = self.make_card(cards, "Today's Playtime", COLORS["card1"])
        self.stats1.pack(side="left", padx=30)
        self.stats2 = self.make_card(cards, "Longest Session", COLORS["card2"])
        self.stats2.pack(side="left", padx=30)
        self.stats3 = self.make_card(cards, "Sessions Today", COLORS["card3"])
        self.stats3.pack(side="left", padx=30)

        self.prediction_label = tk.Label(container, text="Predicted Playtime: 0 min", fg=COLORS["highlight"], bg=COLORS["bg"], font=("Press Start 2P", 12))
        self.prediction_label.pack(pady=10)

        self.risk_label = tk.Label(container, text="Addiction Risk: Low", fg="#ff726f", bg=COLORS["bg"], font=("Press Start 2P", 12))
        self.risk_label.pack(pady=5)
    
    def make_card(self, parent, title, color):
        frame = tk.Frame(parent, bg=color, bd=6, relief="ridge", width=220, height=150)
        frame.pack_propagate(False)
        tk.Label(frame, text=title, fg="black", bg=color,
                 font=("Press Start 2P", 10), anchor="center", justify="center").pack(pady=10)
        value = tk.Label(frame, text="0", fg="black", bg=color,
                         font=("Press Start 2P", 16), anchor="center", justify="center")
        value.pack(expand=True)
        frame.value = value
        return frame
    
    def update_page(self):
        self.user_label.config(text=f"User: {self.controller.current_user or 'Guest'}")
        self.controller.adapt_daily_limit()
        predicted = self.controller.predict_today_playtime()
        risk = self.controller.assess_addiction_risk()

        total, longest, sessions = self.controller.get_today_stats()
        self.stats1.value.config(text=f"{total} min")
        self.stats2.value.config(text=f"{longest} min")
        self.stats3.value.config(text=str(sessions))

        self.prediction_label.config(text=f"Predicted Playtime Today: {predicted} min")
        self.risk_label.config(text=f"Addiction Risk: {risk}")

class MonitorPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True)
        
        tk.Label(container, text="🎮 LIVE MONITOR", fg=COLORS["highlight"],
                 bg=COLORS["bg"], font=("Press Start 2P", 22)).pack(pady=20)
        
        self.status_var = tk.StringVar(value="Stopped")
        self.timer_var = tk.StringVar(value="00:00")
        
        tk.Label(container, textvariable=self.status_var, fg="lime",
                 bg=COLORS["bg"], font=("Press Start 2P", 16), anchor="center", justify="center").pack(pady=10)
        tk.Label(container, textvariable=self.timer_var, fg="cyan",
                 bg=COLORS["bg"], font=("Press Start 2P", 26), anchor="center", justify="center").pack(pady=20)
        
        # Progress bar
        progress_frame = tk.Frame(container, bg=COLORS["bg"])
        progress_frame.pack(pady=20)
        
        tk.Label(progress_frame, text="Daily Progress:", fg=COLORS["text"],
                 bg=COLORS["bg"], font=("Press Start 2P", 12)).pack()
        
        self.progress_canvas = tk.Canvas(progress_frame, width=400, height=30, bg=COLORS["sidebar"], highlightthickness=0)
        self.progress_canvas.pack(pady=10)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 30, fill="lime", outline="")
        
        self.progress_label = tk.Label(progress_frame, text="0 / 120 min (0%)", fg=COLORS["text"],
                                       bg=COLORS["bg"], font=("Press Start 2P", 10))
        self.progress_label.pack()
        
        btn_frame = tk.Frame(container, bg=COLORS["bg"])
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(btn_frame, text="START", command=controller.start_monitoring,
                                   fg="black", bg="lime", font=("Press Start 2P", 12), width=10, height=2)
        self.start_btn.pack(side="left", padx=15)
        
        self.pause_btn = tk.Button(btn_frame, text="PAUSE", command=controller.pause_monitoring,
                                   fg="black", bg="orange", font=("Press Start 2P", 12),
                                   width=10, height=2, state="disabled")
        self.pause_btn.pack(side="left", padx=15)
        
        self.stop_btn = tk.Button(btn_frame, text="STOP", command=controller.stop_monitoring,
                                  fg="black", bg="red", font=("Press Start 2P", 12),
                                  width=10, height=2, state="disabled")
        self.stop_btn.pack(side="left", padx=15)
    
    def update_progress(self, percentage, current_mins):
        width = int((percentage / 100) * 400)
        self.progress_canvas.coords(self.progress_bar, 0, 0, width, 30)
        
        if percentage >= 100:
            self.progress_canvas.itemconfig(self.progress_bar, fill="red")
        elif percentage >= 80:
            self.progress_canvas.itemconfig(self.progress_bar, fill="orange")
        else:
            self.progress_canvas.itemconfig(self.progress_bar, fill="lime")
        
        self.progress_label.config(text=f"{current_mins} / {self.controller.daily_limit} min ({int(percentage)}%)")
    
    def update_page(self): pass

class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True, fill="both")
        
        tk.Label(container, text="📜 HISTORY", fg=COLORS["highlight"],
                 bg=COLORS["bg"], font=("Press Start 2P", 22)).pack(pady=20)
        
        btn_frame = tk.Frame(container, bg=COLORS["bg"])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Export to CSV", command=controller.export_history,
                 fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 10),
                 width=15).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="Clear History", command=self.clear_history,
                 fg="black", bg=COLORS["card2"], font=("Press Start 2P", 10),
                 width=15).pack(side="left", padx=10)
        
        frame = tk.Frame(container, bg=COLORS["card3"], bd=6, relief="ridge")
        frame.pack(expand=True, fill="both", padx=60, pady=20)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        self.summary_label = tk.Label(container, text="Sessions: 0 | Games played: 0", fg=COLORS["text"], bg=COLORS["bg"], font=("Press Start 2P", 10), anchor="center", justify="center")
        self.summary_label.pack(pady=5)

        self.history_box = tk.Listbox(frame, fg="black", bg=COLORS["card3"],
                                      font=("Press Start 2P", 10), yscrollcommand=scrollbar.set, justify="center")
        self.history_box.pack(fill="both", expand=True, padx=20, pady=20)
        scrollbar.config(command=self.history_box.yview)
    
    def add_entry(self, session):
        game = session.get('game', '')
        duration = session.get('duration', 0)
        date_str = session.get('date', '')
        start = session.get('start', '')
        end = session.get('end', '')
        self.history_box.insert("end", f"{date_str} | {game} | {duration}m | {start} - {end}")

    def update_page(self):
        user_history = self.controller.get_current_user_history()
        self.history_box.delete(0, "end")
        for session in user_history:
            self.add_entry(session)

        games_played = len(set(x.get('game', '') for x in user_history if x.get('game')))
        self.summary_label.config(text=f"Sessions: {len(user_history)} | Games played: {games_played}")

    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            self.controller.history.clear()
            self.history_box.delete(0, "end")
            self.summary_label.config(text="Sessions: 0 | Games played: 0")
    
    def update_page(self):
        user_history = self.controller.get_current_user_history()
        self.history_box.delete(0, "end")
        for session in user_history:
            self.add_entry(session)

        unique_games = set([s.get('game', '') for s in user_history if s.get('game', '')])
        self.summary_label.config(text=f"Sessions: {len(user_history)} | Games played: {len(unique_games)}")

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        
        # Scrollable container
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((450, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        container = tk.Frame(scrollable_frame, bg=COLORS["bg"])
        container.pack(pady=20)
        
        tk.Label(container, text="⚙ SETTINGS", fg=COLORS["highlight"],
                 bg=COLORS["bg"], font=("Press Start 2P", 22), anchor="center", justify="center").pack(pady=20)
        
        # Daily limit
        limit_frame = tk.Frame(container, bg=COLORS["card1"], bd=6, relief="ridge")
        limit_frame.pack(pady=15, padx=40, fill="x")
        
        tk.Label(limit_frame, text="Daily Limit (min):", fg="black", bg=COLORS["card1"],
                 font=("Press Start 2P", 10), anchor="center", justify="center").pack(pady=10)
        self.limit_entry = tk.Entry(limit_frame, font=("Press Start 2P", 10), width=15, justify="center")
        self.limit_entry.insert(0, str(controller.daily_limit))
        self.limit_entry.pack(pady=5)
        
        tk.Button(limit_frame, text="Save", command=self.save_limit,
                  fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 10),
                  width=12).pack(pady=10)
        
        # Health interval
        health_frame = tk.Frame(container, bg=COLORS["card2"], bd=6, relief="ridge")
        health_frame.pack(pady=15, padx=40, fill="x")
        
        tk.Label(health_frame, text="Health Tips Interval (min):", fg="black", bg=COLORS["card2"],
                 font=("Press Start 2P", 10), anchor="center", justify="center").pack(pady=10)
        self.health_entry = tk.Entry(health_frame, font=("Press Start 2P", 10), width=15, justify="center")
        self.health_entry.insert(0, str(controller.health_interval))
        self.health_entry.pack(pady=5)
        
        tk.Button(health_frame, text="Save", command=self.save_health,
                  fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 10),
                  width=12).pack(pady=10)
        
        # Break reminder
        break_frame = tk.Frame(container, bg=COLORS["card3"], bd=6, relief="ridge")
        break_frame.pack(pady=15, padx=40, fill="x")
        
        tk.Label(break_frame, text="Break Reminder (min):", fg="black", bg=COLORS["card3"],
                 font=("Press Start 2P", 10), anchor="center", justify="center").pack(pady=10)
        self.break_entry = tk.Entry(break_frame, font=("Press Start 2P", 10), width=15, justify="center")
        self.break_entry.insert(0, str(controller.break_reminder))
        self.break_entry.pack(pady=5)
        
        tk.Button(break_frame, text="Save", command=self.save_break,
                  fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 10),
                  width=12).pack(pady=10)
        
        # Notifications toggle
        notif_frame = tk.Frame(container, bg=COLORS["card1"], bd=6, relief="ridge")
        notif_frame.pack(pady=15, padx=40, fill="x")
        
        self.notif_var = tk.BooleanVar(value=controller.notifications_enabled)
        tk.Checkbutton(notif_frame, text="Enable Notifications", variable=self.notif_var,
                      command=self.toggle_notifications, fg="black", bg=COLORS["card1"],
                      font=("Press Start 2P", 10), selectcolor="gray").pack(pady=15)
        
        self.sound_var = tk.BooleanVar(value=controller.sound_alerts)
        tk.Checkbutton(notif_frame, text="Enable Sound Alerts", variable=self.sound_var,
                      command=self.toggle_sound, fg="black", bg=COLORS["card1"],
                      font=("Press Start 2P", 10), selectcolor="gray").pack(pady=15)
        
        # Games management
        games_frame = tk.Frame(container, bg=COLORS["card2"], bd=6, relief="ridge")
        games_frame.pack(pady=15, padx=40, fill="both", expand=True)
        
        tk.Label(games_frame, text="Monitored Games:", fg="black", bg=COLORS["card2"],
                 font=("Press Start 2P", 10), anchor="center", justify="center").pack(pady=10)
        
        self.games_box = tk.Listbox(games_frame, fg="black", bg=COLORS["card2"],
                                    font=("Press Start 2P", 9), height=6, justify="center")
        self.games_box.pack(fill="both", expand=True, padx=20, pady=5)
        self.refresh_games_list()
        
        btn_frame = tk.Frame(games_frame, bg=COLORS["card2"])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Add Game", command=self.add_game,
                 fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 9),
                 width=12).pack(side="left", padx=5)
        
        self.add_entry = tk.Entry(btn_frame, font=("Press Start 2P", 9), width=20)
        self.add_entry.pack(side="left", padx=5)
        self.add_entry.bind("<Return>", lambda e: self.add_game())
        
        tk.Button(btn_frame, text="Upload Game", command=self.upload_game,
                 fg="black", bg=COLORS["highlight"], font=("Press Start 2P", 9),
                 width=12).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Remove Game", command=self.remove_game,
                 fg="black", bg="red", font=("Press Start 2P", 9),
                 width=12).pack(side="left", padx=5)
    
    def save_limit(self):
        try:
            self.controller.daily_limit = int(self.limit_entry.get())
            self.controller.save_settings()
            messagebox.showinfo("Success", "Daily limit updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def save_health(self):
        try:
            self.controller.health_interval = int(self.health_entry.get())
            self.controller.save_settings()
            messagebox.showinfo("Success", "Health tips interval updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def save_break(self):
        try:
            self.controller.break_reminder = int(self.break_entry.get())
            self.controller.save_settings()
            messagebox.showinfo("Success", "Break reminder updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def toggle_notifications(self):
        self.controller.notifications_enabled = self.notif_var.get()
        self.controller.save_settings()
    
    def toggle_sound(self):
        self.controller.sound_alerts = self.sound_var.get()
        self.controller.save_settings()
    
    def refresh_games_list(self):
        self.games_box.delete(0, "end")
        for g in self.controller.monitored_games:
            self.games_box.insert("end", g)
    
    def add_game(self):
        game = self.add_entry.get().strip()
        if not game:
            game = simpledialog.askstring("Add Game", "Enter game executable name\n(e.g., game.exe):")
        if game and game not in self.controller.monitored_games:
            self.controller.monitored_games.append(game)
            self.controller.monitored_games = list(dict.fromkeys(self.controller.monitored_games))
            global GAMES
            GAMES = list(self.controller.monitored_games)
            self.refresh_games_list()
            self.add_entry.delete(0, 'end')
            self.controller.save_settings()
    
    def upload_game(self):
        file_path = filedialog.askopenfilename(
            title="Select Game Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            game_name = os.path.basename(file_path)
            if game_name and game_name not in self.controller.monitored_games:
                self.controller.monitored_games.append(game_name)
                self.controller.monitored_games = list(dict.fromkeys(self.controller.monitored_games))
                global GAMES
                GAMES = list(self.controller.monitored_games)
                self.refresh_games_list()
                self.controller.save_settings()
                messagebox.showinfo("Success", f"Added {game_name} to monitored games!")
            elif game_name in self.controller.monitored_games:
                messagebox.showwarning("Warning", f"{game_name} is already in the list!")
    
    def remove_game(self):
        selection = self.games_box.curselection()
        if selection:
            game = self.games_box.get(selection[0])
            if messagebox.askyesno("Remove Game", f"Remove {game}?"):
                if game in self.controller.monitored_games:
                    self.controller.monitored_games.remove(game)
                global GAMES
                GAMES = list(self.controller.monitored_games)
                self.controller.save_settings()
                self.refresh_games_list()
    
    def update_page(self):
        self.limit_entry.delete(0, "end")
        self.limit_entry.insert(0, str(self.controller.daily_limit))

        self.health_entry.delete(0, "end")
        self.health_entry.insert(0, str(self.controller.health_interval))

        self.break_entry.delete(0, "end")
        self.break_entry.insert(0, str(self.controller.break_reminder))

        self.notif_var.set(self.controller.notifications_enabled)
        self.sound_var.set(self.controller.sound_alerts)

        self.refresh_games_list()

class StatisticsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller

        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(expand=True, fill="both")

        tk.Label(container, text="📈 STATISTICS", fg=COLORS["highlight"],
                 bg=COLORS["bg"], font=("Press Start 2P", 22)).pack(pady=20)

        # Charts at top
        chart_area = tk.Frame(container, bg=COLORS["bg"])
        chart_area.pack(fill="both", expand=False, padx=40, pady=(0, 10))

        if MATPLOTLIB_AVAILABLE:
            self.pie_figure = Figure(figsize=(6, 3), dpi=90, facecolor=COLORS["bg"])
            self.pie_ax_day = self.pie_figure.add_subplot(121, facecolor=COLORS["card2"])
            self.pie_ax_week = self.pie_figure.add_subplot(122, facecolor=COLORS["card2"])
            for ax in [self.pie_ax_day, self.pie_ax_week]:
                ax.tick_params(colors=COLORS["text"])
                ax.title.set_color(COLORS["text"])

            self.pie_canvas = FigureCanvasTkAgg(self.pie_figure, master=chart_area)
            self.pie_canvas.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)

            self.bar_figure = Figure(figsize=(4, 3), dpi=90, facecolor=COLORS["bg"])
            self.bar_ax = self.bar_figure.add_subplot(111, facecolor=COLORS["card2"])
            self.bar_ax.tick_params(colors=COLORS["text"])
            self.bar_ax.title.set_color(COLORS["text"])
            self.bar_ax.yaxis.label.set_color(COLORS["text"])
            self.bar_ax.xaxis.label.set_color(COLORS["text"])

            self.bar_canvas = FigureCanvasTkAgg(self.bar_figure, master=chart_area)
            self.bar_canvas.get_tk_widget().pack(side="left", fill="both", expand=True, padx=10)
        else:
            tk.Label(chart_area, text="Install matplotlib to view charts.", fg=COLORS["text"],
                     bg=COLORS["bg"], font=("Press Start 2P", 12)).pack(pady=10)

        # Scrollable section for stats below charts
        scroll_container = tk.Frame(container, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.stats_frame = tk.Frame(canvas, bg=COLORS["bg"])
        canvas.create_window((0, 0), window=self.stats_frame, anchor="nw")

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.stats_frame.bind("<Configure>", update_scroll_region)

        # Weekly stats card
        week_frame = tk.Frame(self.stats_frame, bg=COLORS["card1"], bd=6, relief="ridge")
        week_frame.pack(pady=10, fill="x")

        tk.Label(week_frame, text="📅 Weekly Stats", fg="black", bg=COLORS["card1"],
                 font=("Press Start 2P", 14)).pack(pady=15)

        self.week_total = tk.Label(week_frame, text="Total: 0 min", fg="black", bg=COLORS["card1"],
                                   font=("Press Start 2P", 11), anchor="center", justify="center")
        self.week_total.pack(pady=5)

        self.week_avg = tk.Label(week_frame, text="Daily Avg: 0 min", fg="black", bg=COLORS["card1"],
                                font=("Press Start 2P", 11), anchor="center", justify="center")
        self.week_avg.pack(pady=5)

        self.week_sessions = tk.Label(week_frame, text="Sessions: 0", fg="black", bg=COLORS["card1"],
                                      font=("Press Start 2P", 11), anchor="center", justify="center")
        self.week_sessions.pack(pady=5, padx=20)

        # Game breakdown card
        games_frame = tk.Frame(self.stats_frame, bg=COLORS["card3"], bd=6, relief="ridge")
        games_frame.pack(pady=10, fill="both", expand=True)

        tk.Label(games_frame, text="🎮 Game Breakdown", fg="black", bg=COLORS["card3"],
                 font=("Press Start 2P", 14)).pack(pady=15)

        self.game_stats = tk.Text(games_frame, fg="black", bg=COLORS["card3"],
                                 font=("Press Start 2P", 10), height=10, wrap="word", spacing1=4, spacing3=4, relief="flat")
        self.game_stats.tag_configure("center", justify="center")
        self.game_stats.pack(pady=10, padx=20, fill="both", expand=True)

    def update_page(self):
        total, avg, sessions = self.controller.get_week_stats()
        self.week_total.config(text=f"Total: {total} min")
        self.week_avg.config(text=f"Daily Avg: {avg} min")
        self.week_sessions.config(text=f"Sessions: {sessions}")

        # Game breakdown
        user_history = self.controller.get_current_user_history()
        game_totals = {}
        for session in user_history:
            game = session.get('game', '')
            duration = session.get('duration', 0)
            game_totals[game] = game_totals.get(game, 0) + duration

        self.game_stats.delete("1.0", "end")
        if game_totals:
            for game, total_dur in sorted(game_totals.items(), key=lambda x: x[1], reverse=True):
                self.game_stats.insert("end", f"{game}:\n  {total_dur} minutes\n\n", "center")
        else:
            self.game_stats.insert("end", "No game data yet!", "center")

        if not MATPLOTLIB_AVAILABLE:
            return

        now = datetime.now()
        day_cutoff = now - timedelta(days=1)
        week_cutoff = now - timedelta(days=7)

        day_game_time = {}
        week_game_time = {}
        weekday_time = {i: 0 for i in range(7)}

        for session in user_history:
            start_str = session.get('start', '')
            duration = int(session.get('duration', 0))
            if not start_str or duration <= 0:
                continue
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            if start_dt >= week_cutoff:
                week_game_time[session.get('game', '')] = week_game_time.get(session.get('game', ''), 0) + duration
                weekday_time[start_dt.weekday()] += duration

            if start_dt >= day_cutoff:
                day_game_time[session.get('game', '')] = day_game_time.get(session.get('game', ''), 0) + duration

        self.pie_ax_day.clear()
        self.pie_ax_week.clear()
        if day_game_time:
            labels_day = list(day_game_time.keys())
            values_day = list(day_game_time.values())
            self.pie_ax_day.pie(values_day, labels=labels_day, autopct="%1.1f%%", startangle=90)
            self.pie_ax_day.set_title("Last 24h Game Time")
        else:
            self.pie_ax_day.text(0.5, 0.5, "No data in last 24h", ha='center', va='center', color=COLORS["text"])
            self.pie_ax_day.set_title("Last 24h")

        if week_game_time:
            labels_week = list(week_game_time.keys())
            values_week = list(week_game_time.values())
            self.pie_ax_week.pie(values_week, labels=labels_week, autopct="%1.1f%%", startangle=90)
            self.pie_ax_week.set_title("Last 7d Game Time")
        else:
            self.pie_ax_week.text(0.5, 0.5, "No data in last 7d", ha='center', va='center', color=COLORS["text"])
            self.pie_ax_week.set_title("Last 7d")

        self.pie_canvas.draw()

        self.bar_ax.clear()
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        values = [weekday_time[i] for i in range(7)]
        self.bar_ax.bar(days, values, color=COLORS["highlight"])
        self.bar_ax.set_title("Time Played by Weekday (last 7d)")
        self.bar_ax.set_ylabel("Minutes")
        self.bar_ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
        self.bar_canvas.draw()

class AboutPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg"])
        
        # Scrollable container
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def center_window(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", center_window)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        container = tk.Frame(scrollable_frame, bg=COLORS["bg"])
        container.pack(pady=20)
        
        tk.Label(container, text="ℹ ABOUT", fg=COLORS["highlight"],
                 bg=COLORS["bg"], font=("Press Start 2P", 22)).pack(pady=20)
        
        # Main info frame
        frame = tk.Frame(container, bg=COLORS["card3"], bd=6, relief="ridge")
        frame.pack(pady=20, padx=60)
        
        info = """GamerGuard Enhanced
Retro-inspired tool to balance
gaming & life.

⚡ Features:
• Live game tracking
• Timer & daily limits
• History logging & export
• Health habit reminders
• Break notifications
• Weekly statistics
• Custom game management
• Progress tracking

👾 Stay healthy while gaming!"""
        
        tk.Label(frame, text=info, fg="black", bg=COLORS["card3"],
                 font=("Press Start 2P", 10), justify="center").pack(padx=30, pady=30)
        
        # Health tips frame
        tips_frame = tk.Frame(container, bg=COLORS["card1"], bd=6, relief="ridge")
        tips_frame.pack(pady=20, padx=60, fill="both")
        
        tk.Label(tips_frame, text="💚 Health Tips Included:", fg="black", bg=COLORS["card1"],
                 font=("Press Start 2P", 12)).pack(pady=15)
        
        tips_text = tk.Text(tips_frame, fg="black", bg=COLORS["card1"],
                           font=("Press Start 2P", 8), height=15, width=50, wrap="word")
        tips_text.pack(pady=10, padx=20, fill="both")
        
        for tip in HEALTH_TIPS:
            tips_text.insert("end", f"• {tip}\n\n")
        
        tips_text.config(state="disabled")
        
        tk.Label(tips_frame, text="These reminders appear at\nregular intervals while gaming!",
                 fg="black", bg=COLORS["card1"], font=("Press Start 2P", 8),
                 justify="center").pack(pady=15)
    
    def update_page(self): pass

if __name__ == "__main__":
    app = GamerGuardApp()
    app.mainloop()