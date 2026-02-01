"""
Account Manager Tool - Entry Point

This is the main entry point for the Account Manager application.
Run this file to start the application.
"""

from src.gui.main_window import AccountManagerGUI


def main():
    """Initialize and run the Account Manager application"""
    app = AccountManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
