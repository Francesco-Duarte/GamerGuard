#GamerGuard

GamerGuard is a Python desktop application designed to help students
maintain a healthier balance between gaming, study, rest, and daily
responsibilities.

The application monitors selected games running on the computer, tracks
gaming sessions, provides daily playtime limits and break reminders,
stores gaming history, and presents statistics and simple rule-based
indicators for predicted playtime and gaming-risk patterns.

Features

User Login & Sign Up

Local user login and registration interface.

User-specific gaming history.

Live Game Monitoring

Detects selected games using psutil.

Currently supports monitoring:

Roblox

Valorant

Minecraft

Gaming Session Tracking

Records the game being played.

Tracks session start and end times.

Calculates session duration.

Stores the date of each session.

Daily Playtime Limit

Default daily limit: 120 minutes.

The limit can be customized through Settings.

The application can adapt the limit based on recent usage
patterns.

Health & Break Reminders

Provides reminders for breaks, hydration, posture, stretching,
eye care, movement, and other healthy habits.

Default health reminder interval: 30 minutes.

Default break reminder interval: 60 minutes.

Dashboard

Displays:

Today's playtime

Longest session

Sessions today

Predicted playtime

Gaming-risk indicator

History & CSV Export

Gaming sessions are stored locally in history.csv.

Users can export their history to a timestamped CSV file.

Statistics

Provides weekly usage information.

Uses Matplotlib when available for graphical statistics.

Playtime Prediction

Uses previous daily gaming totals and current-day activity to
estimate today's playtime.

This is a statistics/rule-based prediction, not a
machine-learning model.

Gaming-Risk Indicator

Uses rule-based conditions such as session count, daily
playtime, long sessions, break patterns, and weekly overuse.

The result is an application indicator for usage patterns and is
not a medical or clinical diagnosis.

Retro-Inspired Interface

Uses a dark blue/retro interface with contrasting neon-style
cards and highlights.

Designed to provide a simple student-friendly desktop
experience.

Technology Stack

Technology        Purpose

Python            Main programming language
Tkinter           Desktop graphical user interface
psutil            Detecting running game processes
CSV               Local gaming-history storage and export
JSON              Local application/settings storage
Matplotlib        Statistics and charts
threading         Background game-monitoring process
datetime / time   Session timing and date/time handling

How It Works

The basic workflow is:

User Login
    ↓
Dashboard
    ↓
Start Monitoring
    ↓
GamerGuard checks running processes
    ↓
Supported game detected
    ↓
Gaming session is tracked
    ↓
Session ends
    ↓
Session data is saved to history.csv
    ↓
Dashboard / Statistics are updated
    ↓
Playtime prediction and risk indicator are calculated

Installation

1. Install Python

Install Python 3.x on Windows.

Tkinter is normally included with standard Python installations on
Windows.

2. Install Dependencies

Open Command Prompt or PowerShell in the project directory and run:

pip install psutil matplotlib

matplotlib is used for graphical statistics. The application also
contains optional handling for Matplotlib, so the core interface can
still be used without charts if Matplotlib is unavailable.

3. Run the Application

Run the Python file containing the GamerGuardApp class and application
entry point.

For example, if the main file is named main.py:

python main.py

Replace main.py with the actual filename of your GamerGuard source
file.

Supported Games

The current process-monitoring configuration checks for these executable
names:

RobloxPlayerBeta.exe
valorant.exe
Minecraft.exe

Additional games can be added through the application's custom
game/settings functionality.

Data Storage

GamerGuard currently uses local files rather than a database or cloud
backend.

history.csv

Stores gaming session information including:

User

Game

Duration

Start time

End time

Date

settings.json

Stores application settings such as configured limits, reminder
settings, notification preferences, and monitored games.

Exported History

The application can create timestamped history exports using a filename
similar to:

gamerguard_history_YYYYMMDD_HHMMSS.csv

Playtime Prediction

GamerGuard calculates a simple prediction using historical daily gaming
totals.

The prediction considers:

Previous daily usage

Current day's usage

Average historical usage

If there is not enough historical data, the application falls back to
the available current-day information.

This approach is intentionally lightweight and does not require an
external machine-learning model.

Adaptive Daily Limit

The application can adjust the configured daily limit based on the
user's recent seven-day usage.

In the current implementation:

If multiple recent days exceed the configured limit, the limit can
be reduced.

If several recent days remain within the limit, the limit can be
increased.

The application keeps the adaptive limit within configured minimum
and maximum boundaries.

This feature is intended as a simple usage-management mechanism rather
than a clinical or behavioral assessment.

Risk Indicator

The risk indicator uses a rule-based score based on usage behavior such
as:

Number of sessions

Total minutes played today

Long gaming sessions

Break patterns

Daily and weekly overuse

The current levels are:

Low
Medium
High
Critical

These labels describe patterns detected by the application's rules. They
should not be interpreted as a medical diagnosis or as a determination
of addiction.

Health Tips

GamerGuard includes reminders and tips related to healthy computer-use
habits, including:

Drinking water

Taking breaks

Eye care

Maintaining posture

Stretching

Deep breathing

Moving around

Exercise

Hand exercises

Neck movement

Taking mental breaks

Project Structure

A typical project directory can look like:

GamerGuard/
│
├── <main_application_file>.py
├── history.csv              # Created/updated at runtime
├── settings.json            # Created/updated at runtime
└── gamerguard_history_*.csv # Optional exported history files

The exact source filename may vary depending on how the project is
organized.

Main Application Pages

GamerGuard includes the following major sections:

Dashboard

Overview of current gaming activity and statistics.

Live Monitor

Monitors supported game processes and active sessions.

History

Displays recorded gaming sessions and provides CSV export.

Settings

Allows customization of application preferences and monitored
games.

Statistics

Displays weekly usage information and charts where available.

About

Provides information about GamerGuard and its purpose.

Login / Sign Up

Handles the application's local user interface for account
access.

Project Goals

The main goals of GamerGuard are to:

Make students more aware of their gaming habits.

Track gaming time automatically.

Encourage regular breaks.

Provide simple usage statistics.

Help users set reasonable daily gaming limits.

Present gaming activity in an easy-to-understand dashboard.

Demonstrate practical Python desktop application development.

Future Improvements

Possible future improvements include:

Database-based storage such as MySQL or SQLite.

More supported games and automatic game discovery.

Improved analytics and visualizations.

More advanced prediction models.

Cross-device synchronization.

Cloud-based user accounts.

More configurable notification options.

Study-time and productivity tracking.

A mobile companion application.

More detailed reports and dashboards.

Privacy

GamerGuard is designed around local application data.

The current implementation stores gaming history and settings in local
files and does not require a cloud backend or external database.

Users should still review and manage the generated CSV/JSON files
appropriately because they may contain personal usage information.

Disclaimer

GamerGuard is an educational and productivity-oriented software project.

Its playtime prediction and gaming-risk features are simple
software-based indicators. They are not intended to diagnose addiction,
mental-health conditions, or any other medical condition.

Author

Francesco Duarte

Computer Engineering Student

License

No specific open-source license is currently defined for this project.

If the project is published publicly, an appropriate license such as MIT
can be added after deciding how the source code should be reused.
