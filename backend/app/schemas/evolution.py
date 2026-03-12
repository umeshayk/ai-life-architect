from pydantic import BaseModel


class EvolutionSeries(BaseModel):
    topic: str
    values: list[int]


class EvolutionResponse(BaseModel):
    labels: list[str]
    series: list[EvolutionSeries]
