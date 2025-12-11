import random
from typing import Dict, List

from rpg.domain.models.character_class import CharacterClass
from rpg.domain.models.character_options import Background, DifficultyPreset, Race
from rpg.domain.repositories import CharacterRepository, ClassRepository, LocationRepository
from rpg.domain.services.character_factory import ABILITY_ALIASES, create_new_character


ABILITY_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]


class CharacterCreationService:
    def __init__(self, character_repo: CharacterRepository,
                 class_repo: ClassRepository,
                 location_repo: LocationRepository):
        self.character_repo = character_repo
        self.class_repo = class_repo
        self.location_repo = location_repo
        self.races: List[Race] = self._default_races()
        self.backgrounds: List[Background] = self._default_backgrounds()
        self.difficulties: List[DifficultyPreset] = self._default_difficulties()
        self.starting_equipment: Dict[str, List[str]] = self._default_starting_equipment()

    def list_classes(self) -> list[CharacterClass]:
        return self.class_repo.list_playable()

    def list_races(self) -> List[Race]:
        return list(self.races)

    def list_backgrounds(self) -> List[Background]:
        return list(self.backgrounds)

    def list_difficulties(self) -> List[DifficultyPreset]:
        return list(self.difficulties)

    def create_character(
        self,
        name: str,
        class_index: int,
        ability_scores: Dict[str, int] | None = None,
        race: Race | None = None,
        background: Background | None = None,
        difficulty: DifficultyPreset | None = None,
    ) -> "Character":
        name = self.sanitize_name(name)
        classes = self.class_repo.list_playable()
        if class_index < 0 or class_index >= len(classes):
            raise ValueError("Invalid class selection.")
        chosen = classes[class_index]

        if ability_scores is None:
            ability_scores = self.standard_array_for_class(chosen)

        starting_equipment = self.starting_equipment.get(
            chosen.slug, self.starting_equipment.get("_default", [])
        )
        character = create_new_character(
            name,
            chosen,
            ability_scores=ability_scores,
            race=race,
            background=background,
            difficulty=difficulty,
            starting_equipment=starting_equipment,
        )

        starting_location = self.location_repo.get_starting_location()
        character.location_id = starting_location.id if starting_location else None

        self.character_repo.create(character, character.location_id or 0)

        return character

    def standard_array_for_class(self, cls: CharacterClass) -> Dict[str, int]:
        primary_raw = cls.primary_ability or "STR"
        primary = ABILITY_ALIASES.get(primary_raw.lower(), primary_raw).upper()
        ordered = [primary] + [ability for ability in ABILITY_ORDER if ability != primary]
        allocation: Dict[str, int] = {}
        for ability, score in zip(ordered, STANDARD_ARRAY):
            allocation[ability] = score
        return allocation

    def roll_ability_scores(self, rng: random.Random | None = None) -> List[int]:
        rng = rng or random.Random()
        return [self._roll_4d6_drop_lowest(rng) for _ in range(6)]

    def validate_point_buy(self, scores: Dict[str, int], pool: int = 27) -> Dict[str, int]:
        normalized: Dict[str, int] = {ability: 8 for ability in ABILITY_ORDER}
        for key, raw_value in scores.items():
            canonical = ABILITY_ALIASES.get(key.lower(), key.lower()).upper()
            if canonical not in ABILITY_ORDER:
                continue
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                value = 8
            if value < 8 or value > 15:
                raise ValueError(f"{canonical} must be between 8 and 15.")
            normalized[canonical] = value

        cost = self._point_buy_cost(normalized)
        if cost > pool:
            raise ValueError(f"Point buy exceeds {pool} points (cost {cost}).")
        return normalized

    @staticmethod
    def _point_buy_cost(scores: Dict[str, int]) -> int:
        cost = 0
        for ability, value in scores.items():
            if ability.upper() not in ABILITY_ORDER:
                continue
            cost += POINT_BUY_COSTS.get(value, 0)
        return cost

    @staticmethod
    def _roll_4d6_drop_lowest(rng: random.Random) -> int:
        rolls = sorted([rng.randint(1, 6) for _ in range(4)], reverse=True)
        return sum(rolls[:3])

    @staticmethod
    def sanitize_name(raw: str, max_length: int = 20) -> str:
        trimmed = (raw or "").strip()
        cleaned = "".join(ch for ch in trimmed if ch.isprintable() and ch not in "\t\r\n")
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        return cleaned or "Nameless One"

    @staticmethod
    def _default_races() -> List[Race]:
        return [
            Race(name="Human", bonuses={key: 1 for key in ABILITY_ORDER}, speed=30, traits=["Versatile", "Adaptive"]),
            Race(name="Elf", bonuses={"DEX": 2, "INT": 1}, speed=30, traits=["Keen Senses", "Fey Ancestry"]),
            Race(name="Dwarf", bonuses={"CON": 2, "WIS": 1}, speed=25, traits=["Darkvision", "Stonecunning"]),
            Race(name="Halfling", bonuses={"DEX": 2, "CHA": 1}, speed=25, traits=["Lucky", "Brave"]),
        ]

    @staticmethod
    def _default_backgrounds() -> List[Background]:
        return [
            Background(
                name="Soldier",
                proficiencies=["Athletics", "Intimidation"],
                feature="Military Rank",
                faction="militia",
                starting_money=10,
            ),
            Background(
                name="Sage",
                proficiencies=["Arcana", "History"],
                feature="Researcher",
                starting_money=8,
            ),
            Background(
                name="Criminal",
                proficiencies=["Stealth", "Deception"],
                feature="Criminal Contact",
                faction="underworld",
                starting_money=12,
            ),
            Background(
                name="Acolyte",
                proficiencies=["Insight", "Religion"],
                feature="Shelter of the Faithful",
                faction="church",
                starting_money=6,
            ),
        ]

    @staticmethod
    def _default_difficulties() -> List[DifficultyPreset]:
        return [
            DifficultyPreset(
                slug="story",
                name="Story Mode",
                description="More HP, forgiving damage for a relaxed run.",
                hp_multiplier=1.3,
                incoming_damage_multiplier=0.75,
            ),
            DifficultyPreset(
                slug="normal",
                name="Standard",
                description="Baseline challenge.",
                hp_multiplier=1.0,
                incoming_damage_multiplier=1.0,
            ),
            DifficultyPreset(
                slug="hardcore",
                name="Hardcore",
                description="Harsher blows and slimmer HP.",
                hp_multiplier=0.8,
                incoming_damage_multiplier=1.25,
                outgoing_damage_multiplier=1.05,
            ),
        ]

    @staticmethod
    def _default_starting_equipment() -> Dict[str, List[str]]:
        return {
            "barbarian": ["Greataxe", "Explorer's Pack", "Javelin x4"],
            "bard": ["Rapier", "Lute", "Leather Armor", "Dagger"],
            "cleric": ["Mace", "Shield", "Chain Shirt", "Holy Symbol"],
            "druid": ["Scimitar", "Wooden Shield", "Herbalism Kit"],
            "fighter": ["Longsword", "Shield", "Chain Mail"],
            "monk": ["Quarterstaff", "Darts x10"],
            "paladin": ["Longsword", "Shield", "Chain Mail", "Holy Symbol"],
            "ranger": ["Longbow", "Shortsword x2", "Leather Armor"],
            "rogue": ["Shortsword", "Shortbow", "Leather Armor", "Thieves' Tools"],
            "sorcerer": ["Dagger", "Component Pouch", "Wand"],
            "warlock": ["Pact Rod", "Leather Armor", "Dagger x2"],
            "wizard": ["Spellbook", "Quarterstaff", "Component Pouch"],
            "artificer": ["Light Hammer", "Scale Mail", "Tinker Tools"],
            "_default": ["Traveler's Cloak", "Rations (3 days)", "Torch x3"],
        }
