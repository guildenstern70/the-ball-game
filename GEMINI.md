# GEMINI.md - Technical Context & Guidelines

This document provides project context, technical specifications, codebase architecture, and development guidelines for Gemini AI working on **The Ball Game**.

---

## 1. Project Overview

**The Ball Game** is a desktop baseball simulator built in Python using PyQt6 for the graphical user interface and SQLAlchemy with SQLite for database persistence and entity management.

- **Name**: `the-ball-game`
- **Version**: `0.1.0`
- **Language**: Python >= 3.11
- **Package Manager**: `uv` (managed via `pyproject.toml` & `uv.lock`)
- **License**: ISC License

---

## 2. Technology Stack & Dependencies

| Category | Technology | Usage / Purpose |
| :--- | :--- | :--- |
| **GUI Framework** | PyQt6 (`>=6.11.0`) | Window management, widget layout, screen stacking, custom vector drawing (`QPainter`), and animations. |
| **ORM / Database** | SQLAlchemy (`>=2.0.0`) | SQLite ORM models (`Team`, `Player`, `Position`), relationship mapping, and database seed logic. |
| **Database Engine** | SQLite (`the_ball_game.db`) | Local file database stored in project root. |
| **Logging** | Loguru (`>=0.7.3`) | Application logging, with custom `InterceptHandler` forwarding standard Python logging and SQLAlchemy engine logs to Loguru. |

---

## 3. Codebase Architecture & File Structure

```
TheBallGame/
├── GEMINI.md               # Context documentation for AI assistance
├── pyproject.toml          # Project configuration, dependencies, and script entry points
├── uv.lock                 # Lockfile for dependency pinning
├── main.py                 # Application entry point & QMainWindow controller
├── welcome_screen.py       # PyQt6 Welcome Screen, Baseball Diamond Animation, and Game Screen
├── database.py             # SQLAlchemy models, SQLite engine initialization, and seeding logic
├── the_ball_game.db        # SQLite database file
├── data/
│   └── teams.json          # Initial team seed data
└── LICENSE                 # Project license (ISC)
```

### Key Modules Detailed

#### `main.py`
- Entry point (`main()`) called via `uv run python main.py` or script command `the-ball-game`.
- Initializes database via `database.init_db()`.
- Sets up `QApplication` and `QMainWindow`.
- Manages view navigation using `QStackedWidget` between `WelcomeScreen` and `GameScreen`.
- Applies top-level black background styling (`QMainWindow, QWidget, QStackedWidget { background-color: #000000; }`).

#### `welcome_screen.py`
- **`BaseballDiamondWidget`**: Custom `QWidget` using `QPainter` to render a 400x400 vector baseball field (dirt track, grass diamond, bases, foul lines, pitcher's mound).
  - Uses a `QTimer` running at ~33 FPS (120-tick cycle) for pitch, swing & hit, contact flash, `"CRACK!"` text popup, and parabolic height arc for fly balls.
  - Background filled with solid `#000000` via `painter.fillRect(self.rect(), QColor("#000000"))`.
- **`WelcomeScreen`**:
  - Main welcome screen showing the title `"THE BALL GAME"`, subtitle `"A tiny baseball simulator"`, the centered animated diamond, and a breathing/pulsing `"HIT ANY KEY TO START"` prompt (animated via `QGraphicsOpacityEffect` and sine timer).
  - Captures keyboard presses (`keyPressEvent`) and mouse clicks (`mousePressEvent`) to emit the `started` signal.
  - Uses `self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)` for proper CSS rendering.
- **`GameScreen`**:
  - Placeholder game screen displaying team and player statistics queried live from SQLite.
  - Handles `ESC` key press to emit `back_to_menu` signal.

#### `database.py`
- SQLite database connection (`sqlite:///the_ball_game.db`).
- ORM Models:
  - `Team`: Name, city, nation, stadium name, relationship to `Player`.
  - `Player`: Name, surname, team_id, JSON `physical_attributes` (height, weight, speed, power), relationship to `Position`.
  - `Position`: Name (Pitcher, Catcher, 1st Base, etc.), many-to-many relationship to `Player` via `player_positions`.
- `init_db()`: Creates tables if missing and seeds initial 6 teams from `data/teams.json` and 156 players (complete MLB 26-player rosters per team: 13 pitchers & 13 position players).

---

## 4. Design Aesthetics & Styling Guidelines

1. **Theme Palette**:
   - **Primary Background**: `#000000` (Pure Black)
   - **Grass Green**: `#1e3f20` (Outfield), `#2d6a4f` (Infield)
   - **Dirt Clay**: `#8c6239` (Infield track), `#a67c52` (Mound)
   - **Title Text**: `#e8f5e9` (Soft White)
   - **Subtitle / Secondary Text**: `#81c784` (Soft Green)
   - **Prompt Text**: `#a5d6a7` (Pulsing Light Green)
2. **PyQt6 Custom Widget Styling Rules**:
   - Always set `self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)` on custom `QWidget` subclasses so PyQt6 respects stylesheet `background-color` rules.
   - Set `background-color: transparent` on `QLabel` elements overlaying dark backgrounds to prevent unwanted background card boxes.

---

## 5. Development & Execution Commands

- **Run Application**:
  ```bash
  uv run python main.py
  ```
- **Check Compilation / Syntax**:
  ```bash
  uv run python -m py_compile welcome_screen.py main.py database.py
  ```
