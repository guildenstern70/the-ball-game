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
| **GUI Framework** | PyQt6 (`>=6.11.0`) | Window management, widget layout, screen stacking, custom vector drawing (`QPainter`), animations, responsive UI scaling. |
| **ORM / Database** | SQLAlchemy (`>=2.0.0`) | SQLite ORM models (`Team`, `Player`, `Position`, `PlayerStats`, `GameStatus`), relationship mapping, dynamic engine binding. |
| **Database Engine** | SQLite (`saves/*.db`) | Isolated per-save database files (`saves/savegame-ddmmyy-hhmmss.db`). |
| **Logging** | Loguru (`>=0.7.3`) | Application logging with custom `InterceptHandler` forwarding Python logging and SQLAlchemy engine logs to Loguru. |

---

## 3. Codebase Architecture & File Structure

The project is structured into three clean namespaces: `model`, `game`, and `ui`.

```
TheBallGame/
├── GEMINI.md               # Context documentation for AI assistance
├── README.md               # User setup & feature documentation
├── pyproject.toml          # Project configuration, dependencies, and script entry points
├── uv.lock                 # Lockfile for dependency pinning
├── main.py                 # Application bootstrap entry point & QMainWindow controller
├── data/
│   ├── teams.json          # Initial team seed data template
│   └── logos/              # Team logo PNG assets
├── saves/                  # SQLite per-save database files (savegame-ddmmyy-hhmmss.db)
├── model/                  # Namespace: Models & Database persistence
│   ├── __init__.py         # Package exports
│   ├── entities.py         # SQLAlchemy ORM models (Team, Player, Position, PlayerStats, GameStatus)
│   └── database.py         # Save manager, active DB connection, seeding & query helpers
├── game/                   # Namespace: Game logic & orchestration
│   ├── __init__.py         # Package exports
│   └── manager.py          # GameManager career creation & state controller
└── ui/                     # Namespace: PyQt6 UI screens & components
    ├── __init__.py         # Package exports
    ├── diamond.py          # BaseballDiamondWidget vector pitch animation with QPainter scaling
    ├── dialogs.py          # SaveSelectorDialog & SettingsDialog (with resolution switcher)
    └── screens.py          # WelcomeScreen, TeamSelectScreen, HomeScreen, & TeamRosterScreen
```

### Key Components & Models Detailed

#### 1. Models (`model/entities.py` & `model/database.py`)
- **`Team`**: Name, city, nation, stadium name, relationship to rostered players.
- **`Player`**: Name, surname, team_id, JSON `physical_attributes` (height, weight, speed, power), relationship to positions & stats.
- **`Position`**: Standard baseball positions (Pitcher, Catcher, 1st Base, etc.).
- **`GameStatus`**: Tracks user's chosen franchise (`user_team_id`), current `season` (2026), and `current_date` ("2026-04-01").
- **`PlayerStats`**:
  - Counting stats: `hits` (H), `at_bats` (AB), `hit_by_pitch` (HBP), `home_runs` (HR), `plate_appearances` (PA), `runs` (R), `runs_batted_in` (RBI), `doubles` (2B), `triples` (3B), `walks` (BB).
  - Calculated properties: `batting_average` (BA), `on_base_percentage` (OBP), `slugging_percentage` (SLG), `on_base_plus_slugging` (OPS).
- **Save Manager**: Manages `saves/savegame-DDMMYY-HHMMSS.db` files, dynamic engine binding, and complete roster seeding (6 teams x 26 players = 156 total with default zero stats).

#### 2. Game Logic (`game/manager.py`)
- **`GameManager`**: Orchestrates high-level career setup, loading recent save files, saving state, and status queries.

#### 3. User Interface (`ui/`)
- **`WelcomeScreen`**: Displays title, vector animated diamond, and dynamic New/Continue/Load menu.
- **`TeamSelectScreen`**: Allows choosing a franchise from template cards to initialize a new career save.
- **`HomeScreen`**: Dashboard showing chosen team banner, season date, and action tiles.
- **`TeamRosterScreen`**: Interactive roster viewer with mode toggle between **📋 Physical Attributes** and **📊 Season Statistics**.
- **`SettingsDialog`**: Modal supporting screen resolution switching (**1280 × 720** & **1920 × 1080**), returning to Main Menu, and exiting game.
- **`BaseballDiamondWidget`**: Dynamic `QPainter.scale()` vector pitching and hit animation.

---

## 4. Design Aesthetics & Styling Guidelines

1. **Theme Palette**:
   - **Primary Background**: `#000000` (Pure Black) / `#0b140e` (Modal Dark)
   - **Card / Surface Fill**: `#111c15` (Dark Green Surface), `#1b3823` (Active Green Highlight)
   - **Grass Green**: `#1e3f20` (Outfield), `#2d6a4f` (Infield)
   - **Dirt Clay**: `#8c6239` (Infield track), `#a67c52` (Mound)
   - **Title Text**: `#e8f5e9` (Soft White)
   - **Secondary / Accent Text**: `#81c784` (Soft Green), `#a5d6a7` (Pulsing Light Green)
2. **PyQt6 Custom Widget Styling Rules**:
   - Always set `self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)` on custom `QWidget` subclasses so PyQt6 respects stylesheet `background-color` rules.
   - Use standard system fonts (`'Helvetica Neue', Arial, sans-serif`) in CSS `font-family` declarations.

---

## 5. Development & Execution Commands

- **Run Application**:
  ```bash
  uv run python main.py
  ```
- **Check Compilation / Syntax Across All Packages**:
  ```bash
  uv run python -m py_compile model/*.py game/*.py ui/*.py main.py
  ```
