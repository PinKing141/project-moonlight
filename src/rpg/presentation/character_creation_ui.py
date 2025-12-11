from rpg.application.services.character_creation_service import CharacterCreationService
from rpg.presentation.menu_controls import arrow_menu, clear_screen


CLASS_OPTIONS = [
    "Fighter   – Tough frontline warrior.",
    "Rogue     – Agile, sneaky and precise.",
    "Wizard    – Fragile, but powerful with magic.",
]

CLASS_KEYS = ["fighter", "rogue", "wizard"]


def run_character_creation(creation_service: CharacterCreationService):
    clear_screen()
    print("=" * 40)
    print(f"{'CHARACTER CREATION':^40}")
    print("=" * 40)
    print("")
    print("Enter your character's name:")
    print(">>> ", end="")
    name = input().strip()
    if not name:
        name = "Nameless One"

    class_idx = arrow_menu("CHOOSE YOUR CLASS", CLASS_OPTIONS)
    if class_idx == -1:
        return None

    class_name = CLASS_KEYS[class_idx]
    character = creation_service.create_character(name, class_name)

    clear_screen()
    print(f"You created: {character.name}, a level {character.level} {class_name.title()}.")
    print(f"HP: {character.hp_current}/{character.hp_max}")
    print(f"Starting Location ID: {character.location_id}")
    print("")
    input("Press ENTER to begin your adventure...")

    return character.id
