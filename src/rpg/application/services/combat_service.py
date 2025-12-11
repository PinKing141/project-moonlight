import random
from dataclasses import dataclass, replace
from typing import List

from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity


@dataclass
class CombatLogEntry:
    text: str


@dataclass
class CombatResult:
    player: Character
    enemy: Entity
    log: List[CombatLogEntry]
    player_won: bool


def roll_die(spec: str) -> int:
    if not spec or not isinstance(spec, str):
        return 1
    if spec.startswith("d"):
        try:
            sides = int(spec[1:])
            return random.randint(1, max(2, sides))
        except ValueError:
            return 1
    try:
        sides = int(spec)
        return random.randint(1, max(2, sides))
    except ValueError:
        return 1


class CombatService:
    def _player_attack(self, player: Character, foe: Entity, log: List[CombatLogEntry]) -> None:
        roll = random.randint(1, 20)
        total = roll + player.attack_bonus
        if roll == 20:
            dmg = roll_die(player.damage_die) + roll_die(player.damage_die)
            dmg = max(int(dmg * getattr(player, "outgoing_damage_multiplier", 1.0)), 1)
            foe.hp_current = max(0, foe.hp_current - dmg)
            log.append(
                CombatLogEntry(
                    f"Critical hit! You roll a natural 20 and deal {dmg} damage ({foe.hp_current}/{foe.hp_max} HP left)."
                )
            )
        elif total >= foe.armour_class:
            dmg = roll_die(player.damage_die)
            dmg = max(int(dmg * getattr(player, "outgoing_damage_multiplier", 1.0)), 1)
            foe.hp_current = max(0, foe.hp_current - dmg)
            log.append(
                CombatLogEntry(
                    f"You roll {roll} + {player.attack_bonus} = {total} and hit for {dmg} damage ({foe.hp_current}/{foe.hp_max} HP left)."
                )
            )
        else:
            log.append(
                CombatLogEntry(f"You roll {roll} + {player.attack_bonus} = {total} and miss.")
            )

    def _enemy_attack(self, player: Character, foe: Entity, log: List[CombatLogEntry]) -> None:
        roll = random.randint(1, 20)
        total = roll + foe.attack_bonus
        if roll == 20:
            dmg = roll_die(foe.damage_die) + roll_die(foe.damage_die)
            dmg = max(int(dmg * getattr(player, "incoming_damage_multiplier", 1.0)), 1)
            player.hp_current = max(0, player.hp_current - dmg)
            log.append(
                CombatLogEntry(
                    f"Critical! The {foe.name} lands a brutal blow for {dmg} damage ({player.hp_current}/{player.hp_max} HP left)."
                )
            )
        elif total >= player.armour_class:
            dmg = roll_die(foe.damage_die)
            dmg = max(int(dmg * getattr(player, "incoming_damage_multiplier", 1.0)), 1)
            player.hp_current = max(0, player.hp_current - dmg)
            log.append(
                CombatLogEntry(
                    f"The {foe.name} rolls {roll} + {foe.attack_bonus} = {total} and hits for {dmg} damage ({player.hp_current}/{player.hp_max} HP left)."
                )
            )
        else:
            log.append(
                CombatLogEntry(
                    f"The {foe.name} rolls {roll} + {foe.attack_bonus} = {total} and misses you."
                )
            )

    def fight_simple(self, player: Character, enemy: Entity) -> CombatResult:
        log: List[CombatLogEntry] = []

        foe = replace(enemy)
        foe.hp_max = getattr(foe, "hp_max", foe.hp)
        foe.hp_current = getattr(foe, "hp_current", foe.hp_max)

        self._player_attack(player, foe, log)

        if foe.hp_current <= 0:
            xp_gain = max(getattr(foe, "level", 1) * 5, 1)
            player.xp += xp_gain
            log.append(CombatLogEntry(f"The {foe.name} collapses. (+{xp_gain} XP)"))
            return CombatResult(player, foe, log, player_won=True)

        self._enemy_attack(player, foe, log)

        player_won = player.hp_current > 0
        if not player_won:
            log.append(CombatLogEntry("You drop to the ground, consciousness fading..."))

        return CombatResult(player, foe, log, player_won=player_won)
