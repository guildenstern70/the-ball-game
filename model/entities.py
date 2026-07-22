#
# THE BALL GAME - Model Entities
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

from typing import List, Dict, Any, Optional
from sqlalchemy import String, JSON, ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

    # physical_attributes will store height, weight, speed, power as JSON
    physical_attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Many-to-one relationship: Player -> Team
    team: Mapped["Team"] = relationship("Team", back_populates="players")

    # Many-to-many relationship: Player -> Position
    preferred_positions: Mapped[List["Position"]] = relationship(
        "Position",
        secondary=player_positions,
        back_populates="players"
    )

    # One-to-one relationship: Player -> PlayerStats
    stats: Mapped[Optional["PlayerStats"]] = relationship(
        "PlayerStats",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Player(name={self.name!r}, surname={self.surname!r}, team_id={self.team_id})>"


class PlayerStats(Base):
    """Player statistics model storing batting & offensive metrics."""
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True)
    season: Mapped[int] = mapped_column(default=2026)

    # Basic Counting Statistics
    plate_appearances: Mapped[int] = mapped_column(default=0)  # PA
    at_bats: Mapped[int] = mapped_column(default=0)            # AB
    hits: Mapped[int] = mapped_column(default=0)               # H / HITS
    doubles: Mapped[int] = mapped_column(default=0)            # 2B
    triples: Mapped[int] = mapped_column(default=0)            # 3B
    home_runs: Mapped[int] = mapped_column(default=0)          # HR
    runs_batted_in: Mapped[int] = mapped_column(default=0)     # RBI
    runs: Mapped[int] = mapped_column(default=0)               # R
    walks: Mapped[int] = mapped_column(default=0)              # BB
    hit_by_pitch: Mapped[int] = mapped_column(default=0)       # HBP

    # Relationship to Player
    player: Mapped["Player"] = relationship("Player", back_populates="stats")

    # Calculated Statistics Properties
    @property
    def batting_average(self) -> float:
        """BA = Hits / At Bats"""
        if self.at_bats > 0:
            return round(self.hits / self.at_bats, 3)
        return 0.000

    @property
    def on_base_percentage(self) -> float:
        """OBP = (Hits + Walks + HBP) / (At Bats + Walks + HBP)"""
        denom = self.at_bats + self.walks + self.hit_by_pitch
        if denom > 0:
            return round((self.hits + self.walks + self.hit_by_pitch) / denom, 3)
        return 0.000

    @property
    def slugging_percentage(self) -> float:
        """SLG = Total Bases / At Bats"""
        if self.at_bats > 0:
            singles = self.hits - (self.doubles + self.triples + self.home_runs)
            total_bases = singles + (2 * self.doubles) + (3 * self.triples) + (4 * self.home_runs)
            return round(total_bases / self.at_bats, 3)
        return 0.000

    @property
    def on_base_plus_slugging(self) -> float:
        """OPS = OBP + SLG"""
        return round(self.on_base_percentage + self.slugging_percentage, 3)

    def __repr__(self) -> str:
        return f"<PlayerStats(player_id={self.player_id}, H={self.hits}, AB={self.at_bats}, HR={self.home_runs}, RBI={self.runs_batted_in})>"


class GameStatus(Base):
    """Game status database model storing the user's active career state."""
    __tablename__ = "game_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    season: Mapped[int] = mapped_column(default=2026)
    current_date: Mapped[str] = mapped_column(String(10), default="2026-04-01")

    user_team: Mapped["Team"] = relationship("Team")

    def __repr__(self) -> str:
        return f"<GameStatus(user_team_id={self.user_team_id}, season={self.season}, date={self.current_date!r})>"
