from pydantic import BaseModel, Field, computed_field


class WorldAlignment(BaseModel):
    order_chaos:  float = Field(default=0.0, ge=-100.0, le=100.0)
    harm_harmony: float = Field(default=0.0, ge=-100.0, le=100.0)

    @computed_field
    @property
    def quadrant(self) -> str:
        if self.order_chaos >= 0 and self.harm_harmony >= 0:   return "justice"
        elif self.order_chaos >= 0 and self.harm_harmony < 0:  return "tyranny"
        elif self.order_chaos < 0  and self.harm_harmony >= 0: return "mercy"
        else:                                                   return "anarchy"

    @computed_field
    @property
    def intensity(self) -> float:
        return min(100.0, (self.order_chaos**2 + self.harm_harmony**2) ** 0.5)

    @computed_field
    @property
    def mood_descriptor(self) -> str:
        prefix = "deeply " if self.intensity > 70 else "somewhat " if self.intensity > 35 else "mildly "
        return f"{prefix}{self.quadrant}"
