from pydantic import BaseModel, Field


class Region(BaseModel):
    region_id:           str
    name:                str
    description:         str
    base_mood:           str
    connections:         list[str]
    npcs:                list[str]
    danger_level:        int = Field(default=1, ge=1, le=10)
    explored:            bool = False
    alignment_modifiers: dict = {}
    map_position:        dict = {}


class NPC(BaseModel):
    npc_id:                str
    name:                  str
    role:                  str
    region:                str
    base_disposition:      float = Field(default=0.0, ge=-1.0, le=1.0)
    alignment_sensitivity: dict = {}
    personality_tags:      list[str]
    backstory:             str
