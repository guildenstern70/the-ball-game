# The Ball Game

This is a simple and fun baseball simulation.

## Setup

This project is configured for `uv`.

```bash
uv sync
uv run the-ball-game
```

### PyCharm

`Settings > Project > Python Interpreter` -> add/select `.venv/bin/python`

The checked-in run configuration is set to use that interpreter path directly.

You can also run the module directly:

```bash
uv run python main.py
```

## Technologies

This project uses the following technology stack:
* **Database**: SQLite (embedded SQL database, requires no external setup)
* **ORM**: SQLAlchemy (mature Python Object-Relational Mapping library)
* **UI**: PyQt6 (cross-platform GUI toolkit, used to create the game window, draw the field/HUD, and capture keyboard input)
