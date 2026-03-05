from enum import Enum

from pydantic import BaseModel

from models.alignment import WorldAlignment
from models.characters import PlayerState
from models.combat import CombatState


class ScenePhase(str, Enum):
    exploration = "exploration"
    combat      = "combat"
    dialogue    = "dialogue"
    cutscene    = "cutscene"


class SceneState(BaseModel):
    scene_id:     str
    region_id:    str
    description:  str
    active_npcs:  list[str]
    turn_count:   int = 0
    phase:        ScenePhase = ScenePhase.exploration
    combat_state: CombatState | None = None


class GameSession(BaseModel):
    session_id:    str
    players:       dict[str, PlayerState]
    world_state:   WorldAlignment
    current_scene: SceneState
    turn_order:    list[str]
    current_turn:  int = 0
    party_leader:  str
    phase:         ScenePhase = ScenePhase.exploration
    created_at:    float
    is_generating: bool = False
