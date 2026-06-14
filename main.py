"""AirBoard — entry point."""

from src.app.application import AirBoardApplication

if __name__ == "__main__":
    app = AirBoardApplication()
    raise SystemExit(app.run())
