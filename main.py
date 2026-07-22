#
# THE BALL GAME
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from loguru import logger
from database import create_new_save, get_most_recent_save, set_active_database
from welcome_screen import WelcomeScreen, TeamSelectScreen, HomeScreen

def main() -> None:
    logger.info("The Ball Game v.0.1.0")

    app = QApplication(sys.argv)

    # Initialize the main PyQt6 window
    window = QMainWindow()
    window.setWindowTitle("The Ball Game")
    window.resize(900, 680)
    window.setStyleSheet("QMainWindow, QWidget, QStackedWidget { background-color: #000000; }")

    # Create stacked widget for navigation between screens
    stacked_widget = QStackedWidget()
    window.setCentralWidget(stacked_widget)

    welcome_screen = WelcomeScreen()
    team_select_screen = TeamSelectScreen()
    home_screen = HomeScreen()

    stacked_widget.addWidget(welcome_screen)
    stacked_widget.addWidget(team_select_screen)
    stacked_widget.addWidget(home_screen)

    # Transition slots
    def show_welcome():
        welcome_screen.refresh_menu()
        stacked_widget.setCurrentWidget(welcome_screen)
        welcome_screen.setFocus()
        logger.info("Navigated to Welcome Screen.")

    def show_team_select():
        stacked_widget.setCurrentWidget(team_select_screen)
        team_select_screen.setFocus()
        logger.info("Navigated to Team Selection Screen.")

    def show_home():
        home_screen.reload_data()
        stacked_widget.setCurrentWidget(home_screen)
        home_screen.setFocus()
        logger.info("Navigated to Home Screen.")

    # Action Handlers
    def handle_new_game_start():
        logger.info("User requested New Game. Opening Team Selection...")
        show_team_select()

    def handle_team_chosen(team_name: str):
        logger.info(f"Creating new save game with chosen team: '{team_name}'...")
        save_path = create_new_save(team_name)
        logger.info(f"Created and loaded new save game: {save_path}")
        show_home()

    def handle_continue():
        save_path = get_most_recent_save()
        if save_path:
            logger.info(f"Continuing save game: {save_path}")
            set_active_database(save_path)
            show_home()
        else:
            logger.warning("No save files found to continue. Redirecting to Team Selection...")
            show_team_select()

    def handle_load_game(save_path: str):
        logger.info(f"Loading selected save game: {save_path}")
        set_active_database(save_path)
        show_home()

    # Connect signals
    welcome_screen.new_game_requested.connect(handle_new_game_start)
    welcome_screen.continue_requested.connect(handle_continue)
    welcome_screen.load_game_requested.connect(handle_load_game)

    team_select_screen.back_to_welcome.connect(show_welcome)
    team_select_screen.team_chosen.connect(handle_team_chosen)

    home_screen.back_to_menu_requested.connect(show_welcome)
    home_screen.quit_game_requested.connect(app.quit)

    # Set initial view
    show_welcome()

    window.show()

    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
