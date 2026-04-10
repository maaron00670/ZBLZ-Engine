#!/usr/bin/env python3
"""
ZBLZ Engine - Main Entry Point
A Linux desktop application for process analysis and speed manipulation.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from views.main_window import MainWindow
from controllers.main_controller import MainController
from models.app_state import AppState


def main():
    """Initialize and run the ZBLZ Engine application."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("ZBLZ Engine")
    app.setApplicationVersion("0.1.0")
    
    # Initialize MVC components
    model = AppState()
    controller = MainController(model)
    view = MainWindow(controller)
    
    # Connect controller to view for updates
    controller.set_view(view)

    # Stop global hotkey listener when the application exits
    app.aboutToQuit.connect(controller.hotkey_manager.stop)
    
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
