#
# THE BALL GAME - Database Module
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import os
import json
import logging
import sys
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy import create_engine, select, func, ForeignKey, String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# Define InterceptHandler to forward standard logging messages to loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Configure standard logging to use InterceptHandler
logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)

# Set the sqlalchemy engine logger to INFO level so it emits logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

DATABASE_URL = "sqlite:///the_ball_game.db"
engine = create_engine(DATABASE_URL, echo=False)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass

class Team(Base):
    """Team database model."""
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    nation: Mapped[str] = mapped_column(String(100), nullable=False)
    stadium_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # One-to-many relationship: Team -> Players
    players: Mapped[List["Player"]] = relationship(
        "Player",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team(name={self.name!r}, city={self.city!r}, nation={self.nation!r}, stadium={self.stadium_name!r})>"

# Association table for Player <-> Position (Many-to-Many)
from sqlalchemy import Table, Column
player_positions = Table(
    "player_positions",
    Base.metadata,
    Column("player_id", ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
    Column("position_id", ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True)
)

class Position(Base):
    """Position database model."""
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Many-to-many back-reference
    players: Mapped[List["Player"]] = relationship(
        "Player",
        secondary=player_positions,
        back_populates="preferred_positions"
    )

    def __repr__(self) -> str:
        return f"<Position(name={self.name!r})>"

class Player(Base):
    """Player database model."""
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    
    # physical_attributes will store height, weight, speed, etc. as a JSON object
    physical_attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Many-to-one relationship: Player -> Team
    team: Mapped["Team"] = relationship("Team", back_populates="players")

    # Many-to-many relationship: Player -> Position
    preferred_positions: Mapped[List["Position"]] = relationship(
        "Position",
        secondary=player_positions,
        back_populates="players"
    )

    def __repr__(self) -> str:
        return f"<Player(name={self.name!r}, surname={self.surname!r}, team_id={self.team_id})>"

STANDARD_POSITIONS = [
    "Pitcher",
    "Catcher",
    "First Base",
    "Second Base",
    "Third Base",
    "Shortstop",
    "Left Field",
    "Center Field",
    "Right Field"
]

def init_db() -> None:
    """Initialize the database.
    
    Creates tables if they do not exist.
    If database tables are empty, seeds them from JSON files.
    """
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Check if rows exist in team, player, and position tables
        try:
            team_count = session.scalar(select(func.count()).select_from(Team))
            player_count = session.scalar(select(func.count()).select_from(Player))
            position_count = session.scalar(select(func.count()).select_from(Position))
        except Exception as e:
            logger.error(f"Error checking database tables: {e}")
            Base.metadata.create_all(engine)
            team_count = 0
            player_count = 0
            position_count = 0

        # If both teams and players have data, we skip seeding
        if team_count is not None and team_count > 0 and player_count is not None and player_count > 0:
            logger.info(
                f"Database already initialized: found {team_count} teams, "
                f"{player_count} players, and {position_count} positions. Skipping seed."
            )
            return

        logger.info("Initializing database and seeding records...")

        # 1. Seed positions first if not present
        pos_map = {}
        for pos_name in STANDARD_POSITIONS:
            pos = session.scalar(select(Position).where(Position.name == pos_name))
            if not pos:
                pos = Position(name=pos_name)
                session.add(pos)
                session.flush()
            pos_map[pos_name] = pos

        # Load team and player seed files
        teams_file = os.path.join("data", "teams.json")
        players_file = os.path.join("data", "players.json")

        if not os.path.exists(teams_file) or not os.path.exists(players_file):
            logger.warning(f"Initialization skipped: Seed files {teams_file} or {players_file} not found.")
            return

        try:
            with open(teams_file, "r", encoding="utf-8") as f:
                teams_data = json.load(f)
            with open(players_file, "r", encoding="utf-8") as f:
                players_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON seed files: {e}")
            return

        # 2. Clear existing players and teams for a clean seeding run
        try:
            session.query(Player).delete()
            session.query(Team).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clean database before seeding: {e}")
            return

        # 3. Seed teams
        team_map = {}
        for team_info in teams_data:
            team = Team(
                name=team_info["name"],
                city=team_info["city"],
                nation=team_info["nation"],
                stadium_name=team_info["stadium_name"]
            )
            session.add(team)
            session.flush()
            team_map[team.name] = team.id

        # 4. Seed players and link their preferred positions
        for player_info in players_data:
            team_name = player_info["team"]
            team_id = team_map.get(team_name)
            if not team_id:
                logger.warning(f"Team '{team_name}' not found in team map. Skipping player {player_info['name']} {player_info['surname']}.")
                continue

            pref_positions = []
            for pos_name in player_info.get("preferred_positions", []):
                pos_obj = pos_map.get(pos_name)
                if pos_obj:
                    pref_positions.append(pos_obj)
                else:
                    logger.warning(f"Position '{pos_name}' not found. Skipping preferred position for {player_info['name']} {player_info['surname']}.")

            player = Player(
                name=player_info["name"],
                surname=player_info["surname"],
                team_id=team_id,
                physical_attributes=player_info["physical_attributes"],
                preferred_positions=pref_positions
            )
            session.add(player)

        try:
            session.commit()
            logger.success("Database successfully initialized and seeded.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to commit seeded database: {e}")
