from rpg.application.services.character_creation_service import CharacterCreationService
from rpg.presentation.menu_controls import arrow_menu, clear_screen


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

    classes = creation_service.list_playable_classes()
    options = [
        f"{cls.name:<10} – {cls.primary_ability or 'Adventurer'}"
        for cls in classes
    ]

    class_idx = arrow_menu("CHOOSE YOUR CLASS", options)
    if class_idx == -1:
        return None

    chosen_class = classes[class_idx]
    character = creation_service.create_character(name, chosen_class.slug)

    clear_screen()
    print(f"You created: {character.name}, a level {character.level} {chosen_class.name}.")
    print(f"HP: {character.hp_current}/{character.hp_max}")
    print(f"Starting Location ID: {character.location_id}")
    print("")
    input("Press ENTER to begin your adventure...")

    return character.id
