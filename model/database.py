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
import random
import glob
import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy import create_engine, select, func, Engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession, joinedload
from model.entities import Base, Team, Player, Position, GameStatus, PlayerStats, player_positions

# Forward standard logging to loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

SAVES_DIR = "saves"

# Global state for active database engine and session factory
_active_engine: Optional[Engine] = None
_active_session_factory: Optional[sessionmaker] = None
_active_save_path: Optional[str] = None

STANDARD_POSITIONS = [
    "Pitcher", "Catcher", "First Base", "Second Base", "Third Base",
    "Shortstop", "Left Field", "Center Field", "Right Field"
]

FIRST_NAMES = [
    # American (40)
    "Aaron", "Cody", "Dansby", "Freddie", "Gerrit", "Giancarlo", "Ian", "Jarren",
    "Juan", "Logan", "Matt", "Mike", "Mookie", "Nico", "Patrick", "Rafael",
    "Shohei", "Trevor", "Triston", "Clayton", "Buster", "Bryce", "Ronald", "Jose",
    "Francisco", "Corey", "Marcus", "Justin", "Max", "Paul", "Christian", "Corbin",
    "Bobby", "Adley", "Gunnar", "Yordan", "Kyle", "Zack", "Blake", "Dylan",
    # Mexican / Spanish (20)
    "Alejandro", "Carlos", "Mateo", "Diego", "Javier", "Santiago", "Gabriel", "Luis",
    "Fernando", "Rodrigo", "Miguel", "Eduardo", "Joaquin", "Adrian", "Ricardo", "Guillermo",
    "Andres", "Esteban", "Tomas", "Raul",
    # Italian (20)
    "Alessandro", "Lorenzo", "Leonardo", "Francesco", "Andrea", "Mattia", "Filippo", "Davide",
    "Marco", "Giuseppe", "Luca", "Antonio", "Federico", "Giovanni", "Stefano", "Roberto",
    "Jacopo", "Matteo", "Gianluigi", "Enrico",
    # French (20)
    "Antoine", "Jean", "Pierre", "Lucas", "Louis", "Hugo", "Alexandre", "Julien",
    "Maxime", "Nicolas", "Thomas", "Romain", "Arthur", "Baptiste", "Clement", "Mathieu",
    "Guillaume", "Theo", "Quentin", "Henri"
]

SURNAMES = [
    # American (40)
    "Devers", "Duran", "Casas", "Story", "Judge", "Soto", "Cole", "Stanton",
    "Ohtani", "Betts", "Freeman", "Kershaw", "Bellinger", "Swanson", "Hoerner",
    "Happ", "Webb", "Chapman", "Yastrzemski", "Bailey", "Acuna", "Trout", "Harper",
    "Lindor", "Seager", "Semien", "Scherzer", "Verlander", "Goldschmidt", "Yelich",
    "Carroll", "Witt", "Rutschman", "Henderson", "Alvarez", "Tucker", "Wheeler",
    "Snell", "Cease", "Arenado",
    # Mexican / Spanish (20)
    "Rodriguez", "Hernandez", "Gonzalez", "Martinez", "Garcia", "Lopez", "Perez", "Sanchez",
    "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Cruz", "Morales",
    "Reyes", "Gutierrez", "Ortiz", "Mendoza",
    # Italian (20)
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci",
    "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Mancini", "Costa",
    "Giordano", "Rizzo", "Lombardi", "Moretti",
    # French (20)
    "Martin", "Bernard", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau",
    "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand",
    "Fournier", "Girard", "Bonnet", "Dupont"
]


def generate_random_player(
    team_id: int, 
    pos_map: Dict[str, Position], 
    is_pitcher: bool = False,
    assigned_position: str = None
) -> Player:
    """Generate a single random Player instance with realistic physical attributes and positions."""
    first_name = random.choice(FIRST_NAMES)
    surname = random.choice(SURNAMES)
    
    height = random.randint(170, 210)
    weight = random.randint(70, 120)
    speed = random.randint(50, 99)
    power = random.randint(50, 99)
    
    physical_attributes = {
        "height_cm": height,
        "weight_kg": weight,
        "speed": speed,
        "power": power
    }
    
    chosen_positions = []
    if is_pitcher:
        chosen_positions.append(pos_map["Pitcher"])
    elif assigned_position and assigned_position in pos_map:
        chosen_positions.append(pos_map[assigned_position])
        secondary_candidates = [p for name, p in pos_map.items() if name != "Pitcher" and name != assigned_position]
        if random.random() < 0.3 and secondary_candidates:
            chosen_positions.append(random.choice(secondary_candidates))
    else:
        non_pitcher_positions = [p for name, p in pos_map.items() if name != "Pitcher"]
        chosen_positions.extend(random.sample(non_pitcher_positions, random.choice([1, 2])))
        
    seen = set()
    unique_preferred = []
    for p in chosen_positions:
        if p.name not in seen:
            seen.add(p.name)
            unique_preferred.append(p)
        
    return Player(
        name=first_name,
        surname=surname,
        team_id=team_id,
        physical_attributes=physical_attributes,
        preferred_positions=unique_preferred
    )


def get_save_dir() -> str:
    """Ensure the saves directory exists and return its path."""
    os.makedirs(SAVES_DIR, exist_ok=True)
    return SAVES_DIR


def get_save_files() -> List[Dict[str, Any]]:
    """Scan saves/ directory for SQLite save files, sorted by modification time (newest first)."""
    save_dir = get_save_dir()
    pattern = os.path.join(save_dir, "*.db")
    filepaths = glob.glob(pattern)

    saves = []
    for fp in filepaths:
        filename = os.path.basename(fp)
        mtime = os.path.getmtime(fp)
        dt = datetime.datetime.fromtimestamp(mtime)
        formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
        saves.append({
            "filename": filename,
            "filepath": fp,
            "mtime": mtime,
            "formatted_time": formatted_time
        })

    saves.sort(key=lambda s: s["mtime"], reverse=True)
    return saves


def get_most_recent_save() -> Optional[str]:
    """Return the filepath of the most recently modified save game, or None if no save exists."""
    saves = get_save_files()
    if saves:
        return saves[0]["filepath"]
    return None


def get_teams_template_data() -> List[Dict[str, Any]]:
    """Return initial team seed template data directly from data/teams.json."""
    teams_file = os.path.join("data", "teams.json")
    if os.path.exists(teams_file):
        try:
            with open(teams_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading teams template JSON: {e}")
    return []


def set_active_database(save_path: str) -> None:
    """Set active SQLAlchemy engine and session factory for the given SQLite save file."""
    global _active_engine, _active_session_factory, _active_save_path

    dir_name = os.path.dirname(save_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    db_url = f"sqlite:///{save_path}"
    _active_engine = create_engine(db_url, echo=False)
    _active_session_factory = sessionmaker(bind=_active_engine)
    _active_save_path = save_path
    logger.info(f"Active database set to {save_path}")


def get_engine() -> Optional[Engine]:
    """Return the active SQLAlchemy engine."""
    return _active_engine


def get_active_save_path() -> Optional[str]:
    """Return the file path of the currently loaded save game."""
    return _active_save_path


def Session(*args, **kwargs) -> SQLAlchemySession:
    """Context manager / factory returning a new Session bound to the active database engine."""
    if _active_session_factory is None:
        raise RuntimeError("No active database engine initialized. Call set_active_database() or create_new_save() first.")
    return _active_session_factory(*args, **kwargs)


def create_new_save(user_team_name: str) -> str:
    """Create a new save file named savegame-ddmmyy-hhmmss.db, seed rosters, and set the user's chosen team."""
    save_dir = get_save_dir()
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%d%m%y-%H%M%S")
    filename = f"savegame-{timestamp_str}.db"
    save_path = os.path.join(save_dir, filename)

    set_active_database(save_path)
    init_db_schema_and_seed()

    # Persist initial GameStatus with the selected team
    with Session() as session:
        team = session.scalar(select(Team).where(Team.name == user_team_name))
        if not team:
            team = session.scalar(select(Team))

        status = GameStatus(
            user_team_id=team.id,
            season=2026,
            current_date="2026-04-01"
        )
        session.add(status)
        session.commit()
        logger.info(f"GameStatus persisted: team '{team.name}' (ID: {team.id}) in save {save_path}")

    return save_path


def get_active_game_status() -> Optional[Dict[str, Any]]:
    """Return active game status dictionary (user team info, season, current date) or None if no status."""
    if _active_engine is None:
        return None

    try:
        with Session() as session:
            status = session.scalar(
                select(GameStatus).options(joinedload(GameStatus.user_team))
            )
            if status and status.user_team:
                return {
                    "user_team_id": status.user_team.id,
                    "team_name": status.user_team.name,
                    "city": status.user_team.city,
                    "nation": status.user_team.nation,
                    "stadium_name": status.user_team.stadium_name,
                    "season": status.season,
                    "current_date": status.current_date
                }
    except Exception as e:
        logger.error(f"Error fetching active game status: {e}")
    return None


def get_user_team_roster_with_stats() -> List[Dict[str, Any]]:
    """Return list of player data dicts for the active user team with positions, physical attrs, and stats."""
    if _active_engine is None:
        return []

    results = []
    try:
        with Session() as session:
            status = session.scalar(select(GameStatus))
            if not status:
                return []

            players = session.scalars(
                select(Player)
                .where(Player.team_id == status.user_team_id)
                .options(
                    joinedload(Player.preferred_positions),
                    joinedload(Player.stats)
                )
            ).unique().all()

            for p in players:
                pos_str = ", ".join(pos.name for pos in p.preferred_positions)
                stats_obj = p.stats
                
                results.append({
                    "id": p.id,
                    "name": p.name,
                    "surname": p.surname,
                    "full_name": f"{p.name} {p.surname}",
                    "positions": pos_str,
                    "physical": p.physical_attributes or {},
                    "stats": {
                        "pa": stats_obj.plate_appearances if stats_obj else 0,
                        "ab": stats_obj.at_bats if stats_obj else 0,
                        "h": stats_obj.hits if stats_obj else 0,
                        "doubles": stats_obj.doubles if stats_obj else 0,
                        "triples": stats_obj.triples if stats_obj else 0,
                        "hr": stats_obj.home_runs if stats_obj else 0,
                        "rbi": stats_obj.runs_batted_in if stats_obj else 0,
                        "r": stats_obj.runs if stats_obj else 0,
                        "bb": stats_obj.walks if stats_obj else 0,
                        "hbp": stats_obj.hit_by_pitch if stats_obj else 0,
                        "ba": stats_obj.batting_average if stats_obj else 0.000,
                        "obp": stats_obj.on_base_percentage if stats_obj else 0.000,
                        "ops": stats_obj.on_base_plus_slugging if stats_obj else 0.000
                    }
                })
    except Exception as e:
        logger.error(f"Error fetching user team roster: {e}")

    return results


def init_db_schema_and_seed() -> None:
    """Initialize database tables and seed initial rosters into the active database."""
    if _active_engine is None:
        raise RuntimeError("Cannot initialize database without an active database engine.")

    EXPECTED_TEAMS = 12
    PLAYERS_PER_TEAM = 26
    EXPECTED_TOTAL_PLAYERS = EXPECTED_TEAMS * PLAYERS_PER_TEAM  # 312

    Base.metadata.create_all(_active_engine)

    with Session() as session:
        try:
            team_count = session.scalar(select(func.count()).select_from(Team))
            player_count = session.scalar(select(func.count()).select_from(Player))
            position_count = session.scalar(select(func.count()).select_from(Position))
        except Exception as e:
            logger.error(f"Error checking database tables: {e}")
            Base.metadata.create_all(_active_engine)
            team_count = 0
            player_count = 0
            position_count = 0

        if team_count == EXPECTED_TEAMS and player_count == EXPECTED_TOTAL_PLAYERS:
            logger.info(
                f"Database initialized with complete rosters: found {team_count} teams, "
                f"{player_count} players, and {position_count} positions. Skipping seed."
            )
            return

        logger.info(f"Initializing save database and seeding rosters ({EXPECTED_TEAMS} teams x {PLAYERS_PER_TEAM} players = {EXPECTED_TOTAL_PLAYERS} total)...")

        # 1. Seed positions
        pos_map: Dict[str, Position] = {}
        for pos_name in STANDARD_POSITIONS:
            pos = session.scalar(select(Position).where(Position.name == pos_name))
            if not pos:
                pos = Position(name=pos_name)
                session.add(pos)
                session.flush()
            pos_map[pos_name] = pos

        # Load team seed file
        teams_file = os.path.join("data", "teams.json")
        if not os.path.exists(teams_file):
            logger.warning(f"Initialization skipped: Seed file {teams_file} not found.")
            return

        try:
            with open(teams_file, "r", encoding="utf-8") as f:
                teams_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON seed file: {e}")
            return

        # 2. Clean tables for clean seeding
        try:
            session.execute(player_positions.delete())
            session.query(PlayerStats).delete()
            session.query(Player).delete()
            session.query(Team).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clean database before seeding: {e}")
            return

        # 3. Seed teams
        team_ids = []
        for team_info in teams_data:
            team = Team(
                name=team_info["name"],
                city=team_info["city"],
                nation=team_info["nation"],
                stadium_name=team_info["stadium_name"]
            )
            session.add(team)
            session.flush()
            team_ids.append(team.id)

        # 4. Generate 26-player rosters & default PlayerStats
        POSITION_PLAYER_ROLES = [
            "Catcher", "First Base", "Second Base", "Third Base",
            "Shortstop", "Left Field", "Center Field", "Right Field"
        ]

        generated_players = []
        for team_id in team_ids:
            for _ in range(13):
                p = generate_random_player(team_id, pos_map, is_pitcher=True)
                session.add(p)
                generated_players.append(p)

            for i in range(13):
                pos_name = POSITION_PLAYER_ROLES[i] if i < len(POSITION_PLAYER_ROLES) else random.choice(POSITION_PLAYER_ROLES)
                p = generate_random_player(team_id, pos_map, is_pitcher=False, assigned_position=pos_name)
                session.add(p)
                generated_players.append(p)

        session.flush()

        # Add initial zero stats for each player
        for p in generated_players:
            stats = PlayerStats(player_id=p.id, season=2026)
            session.add(stats)

        try:
            session.commit()
            logger.success(f"Database successfully seeded at '{_active_save_path}' with {len(team_ids)} teams, {len(generated_players)} players, and default PlayerStats.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to commit seeded database: {e}")
