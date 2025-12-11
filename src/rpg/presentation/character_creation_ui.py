from rpg.presentation.menu_controls import arrow_menu, clear_screen


def run_character_creation(game_service):
    creation_service = game_service.character_creation_service

    # name
    clear_screen()
    print("=" * 40)
    print(f"{'CHARACTER CREATION':^40}")
    print("=" * 40)
    print("")
    print("Enter your character's name:")
    print(">>> ", end="")
    name = input().strip() or "Nameless One"

    # get classes
    classes = creation_service.list_classes()
    options = [
        f"{cls.name:<10} – {cls.primary_ability or 'Adventurer'}"
        for cls in classes
    ]

    idx = arrow_menu("CHOOSE YOUR CLASS", options)
    if idx < 0:
        return None

    character = creation_service.create_character(name, idx)

    # fake location name if needed
    location_name = "Starting Town"
    if getattr(character, "location_id", None) is not None:
        # if you have a real repo hooked:
        try:
            starting_location = game_service.location_repo.get_by_id(character.location_id)
            location_name = starting_location.name
        except Exception:
            pass

    clear_screen()
    print(f"You created: {character.name}, a level {character.level} {character.class_name.title()}.")
    print(f"HP: {character.hp_current}/{character.hp_max}")
    print(f"Starting Location: {location_name}")
    print("")
    input("Press ENTER to begin your adventure...")

    return character.id
