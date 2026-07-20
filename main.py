#
# THE BALL GAME
# Copyright (c) 2026 Alessio Saltarin
#
# This software is distributed under ISC License.
# See LICENSE.
#

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

def main() -> None:
    print("The Ball Game v.0.1.0")
    
    app = QApplication(sys.argv)
    
    # Initialize the main PyQt6 window
    window = QMainWindow()
    window.setWindowTitle("The Ball Game")
    
    # Set default window size
    window.resize(800, 600)
    window.show()
    
    # Run the Qt application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
