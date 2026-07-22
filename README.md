# The Ball Game

A desktop baseball simulator built in Python with PyQt6 and SQLAlchemy.

---

## Features

- **Isolated Save Files**: Per-career SQLite database files (`saves/savegame-DDMMYY-HHMMSS.db`) featuring clean startup state, Continue, and Load Game file browser.
- **Franchise & Career Startup**: Interactive team selector (`TeamSelectScreen`) to pick your managed franchise and persist game status (`GameStatus`).
- **Home Dashboard**: Central hub displaying your team's logo, stadium info, season progress, and action tiles.
- **Player Statistics & Roster Viewer**: Roster browser (`TeamRosterScreen`) with an instant mode toggle between **Physical Attributes** (height, weight, speed, power) and **Season Batting Statistics** (PA, AB, H, 2B, 3B, HR, RBI, R, BB, HBP, BA, OBP, OPS).
- **Screen Resolution Switching**: Configurable resolution presets (**1280 × 720** Default & **1920 × 1080** Full HD) with window auto-centering and responsive vector canvas scaling (`BaseballDiamondWidget`).
- **Modular Namespace Architecture**: Clean separation into `model/` (persistence), `game/` (logic), and `ui/` (PyQt6 interface).

---

## Setup & Running

This project is managed with `uv`.

```bash
# Sync dependencies
uv sync

# Run application
uv run python main.py
```

### PyCharm Setup

`Settings > Project > Python Interpreter` -> select `.venv/bin/python`.

---

## Technologies

- **UI Framework**: PyQt6 (Window management, screen stacking, vector animations via `QPainter`, responsive layouts)
- **ORM / Database**: SQLAlchemy with SQLite (Entity mapping, dynamic per-save database binding, initial seed generation)
- **Logging**: Loguru (Unified logging with custom standard library logging intercept handler)
- **Package Manager**: `uv`
