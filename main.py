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

from game import GameManager
from ui import WelcomeScreen, TeamSelectScreen, HomeScreen


def main() -> None:
    logger.info("The Ball Game v.0.1.0")

    app = QApplication(sys.argv)
    game_manager = GameManager()

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

    # Screen Transition Slots
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

    # Action Handlers delegating to GameManager
    def handle_new_game_start():
        show_team_select()

    def handle_team_chosen(team_name: str):
        game_manager.create_career(team_name)
        show_home()

    def handle_continue():
        if game_manager.continue_latest_career():
            show_home()
        else:
            show_team_select()

    def handle_load_game(save_path: str):
        game_manager.load_career(save_path)
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
