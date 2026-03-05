from enum import Enum

from pydantic import BaseModel, Field


class EnemyBehavior(str, Enum):
    reckless  = "reckless"
    tactical  = "tactical"
    defensive = "defensive"
    erratic   = "erratic"


class EnemyState(BaseModel):
    enemy_id:       str
    name:           str
    hp:             int
    max_hp:         int
    ac:             int = Field(ge=5, le=25)
    damage_dice:    str
    behavior:       EnemyBehavior = EnemyBehavior.reckless
    status_effects: list[str] = []
    is_alive:       bool = True


class CombatState(BaseModel):
    combat_id:          str
    enemies:            list[EnemyState]
    initiative_order:   list[str]
    current_turn_index: int = 0
    round_number:       int = 1
    log:                list[str] = []

    @property
    def current_actor(self) -> str:
        return self.initiative_order[self.current_turn_index % len(self.initiative_order)]

    @property
    def all_enemies_dead(self) -> bool:
        return all(not e.is_alive for e in self.enemies)
