#
# THE BALL GAME - Database Module
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import os
import json
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy import create_engine, select, func, ForeignKey, String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

DATABASE_URL = "sqlite:///the_ball_game.db"
engine = create_engine(DATABASE_URL, echo=True)

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

    def __repr__(self) -> str:
        return f"<Player(name={self.name!r}, surname={self.surname!r}, team_id={self.team_id})>"

def init_db() -> None:
    """Initialize the database.
    
    Creates tables if they do not exist.
    If both teams and players tables are empty, seeds them from JSON files.
    """
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Check if rows exist in both team and player tables
        try:
            team_count = session.scalar(select(func.count()).select_from(Team))
            player_count = session.scalar(select(func.count()).select_from(Player))
        except Exception as e:
            logger.error(f"Error checking database tables: {e}")
            # If checking failed, we might have an inconsistent state, recreate tables
            Base.metadata.create_all(engine)
            team_count = 0
            player_count = 0

        # If both tables have at least one row, we do nothing
        if team_count is not None and team_count > 0 and player_count is not None and player_count > 0:
            logger.info(f"Database already initialized: found {team_count} teams and {player_count} players. Skipping seed.")
            return

        logger.info("Initializing database from JSON files...")

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

        # Clear any partial data to ensure clean seeding state
        try:
            session.query(Player).delete()
            session.query(Team).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clean database before seeding: {e}")
            return

        # Seed teams first
        team_map = {}
        for team_info in teams_data:
            team = Team(
                name=team_info["name"],
                city=team_info["city"],
                nation=team_info["nation"],
                stadium_name=team_info["stadium_name"]
            )
            session.add(team)
            # Flush to database so the database generates/assigns ID
            session.flush()
            team_map[team.name] = team.id

        # Seed players next
        for player_info in players_data:
            team_name = player_info["team"]
            team_id = team_map.get(team_name)
            if not team_id:
                logger.warning(f"Team '{team_name}' not found in team map. Skipping player {player_info['name']} {player_info['surname']}.")
                continue

            player = Player(
                name=player_info["name"],
                surname=player_info["surname"],
                team_id=team_id,
                physical_attributes=player_info["physical_attributes"]
            )
            session.add(player)

        try:
            session.commit()
            logger.success("Database successfully initialized and seeded.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to commit seeded database: {e}")
