from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class CharacterClass(str, Enum):
    warrior = "warrior"
    rogue   = "rogue"
    mage    = "mage"
    cleric  = "cleric"
    ranger  = "ranger"


class CharacterStats(BaseModel):
    strength:     int = 10
    dexterity:    int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom:       int = 10
    charisma:     int = 10

    @property
    def dex_mod(self) -> int:
        return (self.dexterity - 10) // 2

    @property
    def ac(self) -> int:
        return 10 + self.dex_mod


CLASS_STAT_TEMPLATES: dict[CharacterClass, CharacterStats] = {
    CharacterClass.warrior: CharacterStats(strength=16, dexterity=12, constitution=15, intelligence=8,  wisdom=10, charisma=10),
    CharacterClass.rogue:   CharacterStats(strength=10, dexterity=17, constitution=12, intelligence=13, wisdom=12, charisma=14),
    CharacterClass.mage:    CharacterStats(strength=6,  dexterity=12, constitution=10, intelligence=18, wisdom=14, charisma=12),
    CharacterClass.cleric:  CharacterStats(strength=12, dexterity=10, constitution=13, intelligence=12, wisdom=17, charisma=14),
    CharacterClass.ranger:  CharacterStats(strength=13, dexterity=16, constitution=13, intelligence=12, wisdom=14, charisma=10),
}

CLASS_HP: dict[CharacterClass, int] = {
    CharacterClass.warrior: 28,
    CharacterClass.rogue:   20,
    CharacterClass.mage:    14,
    CharacterClass.cleric:  22,
    CharacterClass.ranger:  22,
}


class Item(BaseModel):
    item_id:    str
    name:       str
    item_type:  Literal["weapon", "armor", "potion", "quest", "misc"]
    damage_dice: str | None = None
    properties: dict = {}


class PlayerState(BaseModel):
    player_id:       str
    display_name:    str
    character_class: CharacterClass
    stats:           CharacterStats
    inventory:       list[Item] = []
    hp:              int
    max_hp:          int
    position:        str
    is_connected:    bool = True
    reconnect_token: str
