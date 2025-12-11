from rpg.bootstrap import create_game_service
from rpg.presentation.main_menu import main_menu


def main():
    game_service = create_game_service()
    main_menu(game_service)


if __name__ == "__main__":
    main()
