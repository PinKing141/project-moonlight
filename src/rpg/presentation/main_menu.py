from rpg.application.services.character_creation_service import CharacterCreationService
from rpg.application.services.game_service import GameService
from rpg.presentation.character_creation_ui import run_character_creation
from rpg.presentation.game_loop import run_game_loop
from rpg.presentation.load_menu import choose_existing_character
from rpg.presentation.menu_controls import arrow_menu, clear_screen


def main_menu(game_service: GameService, creation_service: CharacterCreationService) -> None:
    options = ["New Game", "Continue", "Settings", "Credits", "Quit"]

    while True:
        choice_idx = arrow_menu("REALM OF BROKEN STARS", options)

        if choice_idx == 0:  # New Game
            character_id = run_character_creation(creation_service)
            if character_id is not None:
                run_game_loop(game_service, character_id)

        elif choice_idx == 1:  # Continue
            character_id = choose_existing_character(game_service)
            if character_id is not None:
                run_game_loop(game_service, character_id)

        elif choice_idx == 2:  # Settings
            clear_screen()
            print("Settings not implemented yet.")
            input("Press ENTER to return to the menu...")

        elif choice_idx == 3:  # Credits
            clear_screen()
            print("Made by You.")
            input("Press ENTER to return to the menu...")

        elif choice_idx == 4 or choice_idx == -1:  # Quit or ESC
            clear_screen()
            print("Goodbye.")
            break
