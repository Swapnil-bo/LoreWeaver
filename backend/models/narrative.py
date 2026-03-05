from pydantic import BaseModel, Field


class MoralChoice(BaseModel):
    text:               str
    order_chaos_shift:  float = Field(default=0.0, ge=-20.0, le=20.0)
    harm_harmony_shift: float = Field(default=0.0, ge=-20.0, le=20.0)


class NPCUpdate(BaseModel):
    npc_id:      str
    mood_change: str
    new_memory:  str


class DMResponse(BaseModel):
    narrative:   str = Field(max_length=2000)
    choices:     list[MoralChoice] = Field(min_length=2, max_length=3)
    npc_updates: list[NPCUpdate] = []
    world_event: str | None = None


DM_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string"},
        "choices": {
            "type": "array", "minItems": 2, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "text":               {"type": "string"},
                    "order_chaos_shift":  {"type": "number", "minimum": -20, "maximum": 20},
                    "harm_harmony_shift": {"type": "number", "minimum": -20, "maximum": 20},
                },
                "required": ["text", "order_chaos_shift", "harm_harmony_shift"],
            },
        },
        "npc_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "npc_id":      {"type": "string"},
                    "mood_change": {"type": "string"},
                    "new_memory":  {"type": "string"},
                },
                "required": ["npc_id", "mood_change", "new_memory"],
            },
        },
        "world_event": {"type": ["string", "null"]},
    },
    "required": ["narrative", "choices"],
}
