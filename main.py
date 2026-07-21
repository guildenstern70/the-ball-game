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
from database import init_db
from welcome_screen import WelcomeScreen, GameScreen

def main() -> None:
    logger.info("The Ball Game v.0.1.0")
    
    # Initialize the database
    init_db()
    
    app = QApplication(sys.argv)
    
    # Initialize the main PyQt6 window
    window = QMainWindow()
    window.setWindowTitle("The Ball Game")
    window.resize(800, 600)
    window.setStyleSheet("QMainWindow, QWidget, QStackedWidget { background-color: #000000; }")
    
    # Create stacked widget to swap between welcome screen and game screen
    stacked_widget = QStackedWidget()
    window.setCentralWidget(stacked_widget)
    
    welcome_screen = WelcomeScreen()
    game_screen = GameScreen()
    
    stacked_widget.addWidget(welcome_screen)
    stacked_widget.addWidget(game_screen)
    
    # Transition slots
    def transition_to_game():
        stacked_widget.setCurrentWidget(game_screen)
        game_screen.setFocus()
        logger.info("Main window transitioned to game screen.")
        
    def transition_to_welcome():
        stacked_widget.setCurrentWidget(welcome_screen)
        welcome_screen.setFocus()
        logger.info("Main window transitioned to welcome screen.")
        
    # Connect signals
    welcome_screen.started.connect(transition_to_game)
    game_screen.back_to_menu.connect(transition_to_welcome)
    
    # Set active view
    stacked_widget.setCurrentWidget(welcome_screen)
    
    window.show()
    
    # Run the Qt application event loop
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
