from rpg.application.services.game_service import GameService
from rpg.presentation.menu_controls import arrow_menu, clear_screen


def choose_existing_character(game_service: GameService):
    characters = game_service.list_characters()
    if not characters:
        clear_screen()
        print("No characters available.")
        input("Press ENTER to return to the menu...")
        return None

    options = [
        f"{char.name} (Level {char.level}){' [DEAD]' if not char.alive else ''}"
        for char in characters
    ]

    selection = arrow_menu("CONTINUE", options)
    if selection == -1:
        return None

    return characters[selection].id
