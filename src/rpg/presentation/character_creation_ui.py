import random
from typing import Dict, List

from rpg.application.services.character_creation_service import ABILITY_ORDER, POINT_BUY_COSTS
from rpg.domain.services.class_profiles import CLASS_COMBAT_PROFILE, CLASS_DESCRIPTIONS, DEFAULT_COMBAT_PROFILE
from rpg.presentation.menu_controls import arrow_menu, clear_screen, read_key
from rpg.presentation.rolling_ui import roll_attributes_with_animation, ATTR_ORDER


ABILITY_NAME_MAP = {
    "STR": "strength",
    "DEX": "dexterity",
    "CON": "constitution",
    "INT": "intelligence",
    "WIS": "wisdom",
    "CHA": "charisma",
}


def _format_attr_line(attrs: Dict[str, int]) -> str:
    parts: List[str] = []
    for abbr, full in ABILITY_NAME_MAP.items():
        value = attrs.get(abbr, attrs.get(abbr.lower(), attrs.get(full)))
        if value is not None:
            parts.append(f"{abbr} {value}")
    if not parts and attrs:
        sample_keys = list(attrs.keys())[:3]
        parts = [f"{k.upper()} {attrs[k]}" for k in sample_keys]
    return " / ".join(parts) if parts else "Balanced stats"


def _show_class_detail(chosen_class) -> bool:
    """Return True if player confirms the class (arrow-key driven)."""
    profile = CLASS_COMBAT_PROFILE.get(chosen_class.slug, DEFAULT_COMBAT_PROFILE)
    recommended = _format_attr_line(chosen_class.base_attributes)
    desc = CLASS_DESCRIPTIONS.get(chosen_class.slug, "Adventurer ready for the unknown.")
    options = ["Choose this class", "Back"]
    selected = 0

    while True:
        clear_screen()
        print("=" * 40)
        print(f"{('Class: ' + chosen_class.name):^40}")
        print("=" * 40)
        print(desc)
        print("")
        print(f"Primary Ability : {chosen_class.primary_ability or 'None'}")
        print(f"Hit Die         : {chosen_class.hit_die or 'd8'}")
        print(f"Combat Profile  : AC {profile['ac']}, +{profile['attack_bonus']} to hit, damage {profile['damage_die']}")
        if recommended:
            print(f"Recommended     : {recommended}")
        print("")
        for idx, opt in enumerate(options):
            prefix = "> " if idx == selected else "  "
            print(f"{prefix}{opt}")
        print("")
        print("-" * 40)
        print("Use arrow keys to move, ENTER to select, ESC to cancel.")
        print("-" * 40)

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % len(options)
        elif key == "DOWN":
            selected = (selected + 1) % len(options)
        elif key == "ENTER":
            return selected == 0
        elif key == "ESC":
            return False


def _format_bonus_line(bonuses: Dict[str, int]) -> str:
    if not bonuses:
        return "+0 all"
    unique_values = set(bonuses.values())
    # Handle uniform bonuses like STR+1, DEX+1, etc.
    if len(unique_values) == 1 and len(bonuses) >= len(ABILITY_NAME_MAP):
        val = list(unique_values)[0]
        prefix = "+" if val > 0 else ""
        return f"{prefix}{val} to All Stats"

    parts: List[str] = []
    for abbr, full in ABILITY_NAME_MAP.items():
        value = bonuses.get(abbr, bonuses.get(abbr.lower(), bonuses.get(full)))
        if value:
            prefix = "+" if value > 0 else ""
            parts.append(f"{abbr}{prefix}{value}")
    if not parts:
        parts = [f"{k.upper()}+{v}" for k, v in list(bonuses.items())[:3]]
    return ", ".join(parts)


def _choose_race(creation_service):
    races = creation_service.list_races()
    options = [
        f"{race.name:<10} | {_format_bonus_line(race.bonuses):<18} | Speed {race.speed} | {', '.join(race.traits)}"
        for race in races
    ]
    idx = arrow_menu("CHOOSE YOUR RACE", options)
    if idx < 0:
        return None
    return races[idx]


def _choose_background(creation_service):
    backgrounds = creation_service.list_backgrounds()
    options = []
    for bg in backgrounds:
        profs = ", ".join(bg.proficiencies) if bg.proficiencies else "No profs"
        feature = bg.feature or "No feature"
        options.append(f"{bg.name:<10} | {profs:<25} | {feature}")
    idx = arrow_menu("PICK A BACKGROUND", options)
    if idx < 0:
        return None
    return backgrounds[idx]


def _choose_difficulty(creation_service):
    difficulties = creation_service.list_difficulties()
    options = [
        f"{mode.name:<12} | {mode.description}"
        for mode in difficulties
    ]
    idx = arrow_menu("DIFFICULTY", options)
    if idx < 0:
        return None
    return difficulties[idx]


def _point_buy_cost(scores: Dict[str, int]) -> int:
    return sum(POINT_BUY_COSTS.get(scores.get(abbr, 8), 0) for abbr in ABILITY_ORDER)


def _point_buy_prompt(creation_service, recommended: Dict[str, int]) -> Dict[str, int] | None:
    scores: Dict[str, int] = {ability: 8 for ability in ABILITY_ORDER}
    for ability in ABILITY_ORDER:
        default_val = recommended.get(ability, 8)
        while True:
            clear_screen()
            remaining = 27 - _point_buy_cost(scores)
            current_line = _format_attr_line(scores)
            print("POINT BUY (27 points)")
            print(f"Current: {current_line}")
            print(f"Points remaining: {remaining}")
            raw = input(f"Set {ability} (8-15, default {default_val}, 'q' to cancel): ").strip()
            if raw.lower() in {"q", "quit"}:
                return None
            value = default_val if raw == "" else raw
            try:
                proposed = int(value)
            except ValueError:
                print("Please enter a number between 8 and 15.")
                input("Press ENTER to retry...")
                continue

            prior = scores[ability]
            scores[ability] = proposed
            try:
                scores = creation_service.validate_point_buy(scores, pool=27)
            except ValueError as exc:
                scores[ability] = prior
                print(f"Invalid choice: {exc}")
                input("Press ENTER to retry...")
                continue
            break
    return scores


def _roll_prompt(creation_service) -> Dict[str, int] | None:
    rolled = roll_attributes_with_animation()
    scores: Dict[str, int] = {}
    for abbr in ATTR_ORDER:
        value = rolled.get(abbr, 8)
        scores[abbr] = value
    return scores


def _choose_abilities(creation_service, chosen_class):
    methods = [
        "Class template (standard array)",
        "Point buy (27 points)",
        "Roll 4d6 drop lowest",
    ]
    method = arrow_menu("ABILITY SCORES", methods)
    if method < 0:
        return None

    if method == 1:
        recommended = creation_service.standard_array_for_class(chosen_class)
        return _point_buy_prompt(creation_service, recommended)
    if method == 2:
        return _roll_prompt(creation_service)

    return creation_service.standard_array_for_class(chosen_class)


def _show_cancelled():
    clear_screen()
    print("Character creation canceled.")
    input("Press ENTER to return to the menu...")


def run_character_creation(game_service):
    creation_service = game_service.character_creation_service
    if creation_service is None:
        raise RuntimeError("Character creation is unavailable.")

    while True:  # name loop
        clear_screen()
        print("=" * 40)
        print(f"{'CHARACTER CREATION':^40}")
        print("=" * 40)
        print("")
        print("Enter your character's name (max 20 chars):")
        print(">>> ", end="")
        raw_name = input()
        name = creation_service.sanitize_name(raw_name)

        # Race selection
        while True:
            race = _choose_race(creation_service)
            if race is None:
                # Back to name entry
                break

            classes = creation_service.list_classes()
            if not classes:
                clear_screen()
                print("No classes available.")
                input("Press ENTER to return to the menu...")
                return None

            options = [cls.name for cls in classes]

            # Class selection (with back to race)
            while True:
                idx = arrow_menu("CHOOSE YOUR CLASS", options)
                if idx < 0:
                    # back to race
                    break
                chosen_class = classes[idx]
                if not _show_class_detail(chosen_class):
                    continue

                # Ability + following steps; allow back to class on cancel
                while True:
                    ability_scores = _choose_abilities(creation_service, chosen_class)
                    if ability_scores is None:
                        # back to class selection
                        break

                    # Background (back to abilities)
                    background = _choose_background(creation_service)
                    if background is None:
                        continue

                    # Difficulty (back to background)
                    difficulty = _choose_difficulty(creation_service)
                    if difficulty is None:
                        continue

                    character = creation_service.create_character(
                        name=name,
                        class_index=idx,
                        ability_scores=ability_scores,
                        race=race,
                        background=background,
                        difficulty=difficulty,
                    )

                    location_name = "Starting Town"
                    if getattr(character, "location_id", None) is not None:
                        try:
                            starting_location = game_service.location_repo.get_by_id(character.location_id)
                            location_name = starting_location.name
                        except Exception:
                            pass

                    clear_screen()
                    print(f"You created: {character.name}, a level {character.level} {character.class_name.title()}.")
                    print(f"Race: {character.race} (Speed {character.speed})")
                    print(f"Background: {character.background or 'None'}")
                    print(f"Difficulty: {character.difficulty.title() if character.difficulty else 'Normal'}")
                    print(f"HP: {character.hp_current}/{character.hp_max}")
                    print(f"Abilities: {_format_attr_line(character.attributes)}")
                    if character.race_traits:
                        print(f"Race Traits: {', '.join(character.race_traits)}")
                    if character.background_features:
                        print(f"Background Feature: {', '.join(character.background_features)}")
                    if character.inventory:
                        print(f"Starting Gear: {', '.join(character.inventory)}")
                    print(f"Starting Location: {location_name}")
                    print("")
                    input("Press ENTER to begin your adventure...")

                    return character.id

                # end ability+ flow
            # end class loop
        # end race loop (back to name)

            # unreachable: we should have returned after creating character
