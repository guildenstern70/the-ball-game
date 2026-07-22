#
# THE BALL GAME - Game Logic Manager
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

from typing import List, Dict, Any, Optional
from loguru import logger
from model import (
    create_new_save,
    get_most_recent_save,
    set_active_database,
    get_active_game_status,
    get_save_files
)


class GameManager:
    """Central orchestrator for game state, career creation, and save loading logic."""

    def __init__(self):
        self.active_save_path: Optional[str] = None
        logger.info("GameManager initialized.")

    def create_career(self, team_name: str) -> str:
        """Initialize a new career save game for the chosen team."""
        logger.info(f"GameManager creating career with team: '{team_name}'...")
        save_path = create_new_save(team_name)
        self.active_save_path = save_path
        return save_path

    def load_career(self, save_path: str) -> bool:
        """Load an existing career save game database."""
        logger.info(f"GameManager loading save: '{save_path}'...")
        set_active_database(save_path)
        self.active_save_path = save_path
        return True

    def continue_latest_career(self) -> Optional[str]:
        """Load the most recent career save game if available."""
        latest = get_most_recent_save()
        if latest:
            self.load_career(latest)
            return latest
        logger.warning("No save files found to continue.")
        return None

    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """Return career status for active loaded save."""
        return get_active_game_status()

    def has_save_games(self) -> bool:
        """Return True if at least one save file exists in the saves directory."""
        return len(get_save_files()) > 0
