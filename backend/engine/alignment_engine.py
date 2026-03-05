from models.alignment import WorldAlignment

MAX_SHIFT_PER_ACTION = 20.0


def apply_alignment_shift(current: WorldAlignment, shift: dict) -> WorldAlignment:
    def dampen(val: float, delta: float) -> float:
        delta      = max(-MAX_SHIFT_PER_ACTION, min(MAX_SHIFT_PER_ACTION, delta))
        resistance = abs(val) / 100.0
        effective  = delta * (1.0 - 0.5 * resistance)
        return max(-100.0, min(100.0, val + effective))

    return WorldAlignment(
        order_chaos  = dampen(current.order_chaos,  shift.get("order_chaos_shift",  0)),
        harm_harmony = dampen(current.harm_harmony, shift.get("harm_harmony_shift", 0)),
    )


def get_effective_disposition(npc: "NPC", world: WorldAlignment) -> float:
    order_inf   = (world.order_chaos  / 100.0) * npc.alignment_sensitivity.get("order_chaos",  0)
    harmony_inf = (world.harm_harmony / 100.0) * npc.alignment_sensitivity.get("harm_harmony", 0)
    raw = npc.base_disposition + (order_inf * 0.3) + (harmony_inf * 0.3)
    return max(-1.0, min(1.0, raw))
