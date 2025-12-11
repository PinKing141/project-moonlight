from pathlib import Path
import sys

# Ensure the src directory is on sys.path when running as a script
_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from rpg.bootstrap import create_game_service
from rpg.presentation.main_menu import main_menu


def main():
    game_service = create_game_service()
    main_menu(game_service)


if __name__ == "__main__":
    main()
