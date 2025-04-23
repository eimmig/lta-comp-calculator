from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Player:
    name: str
    team: str
    cost: float
    value: float = 0.0
    avg_score: float = 0.0
    last_score: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0

@dataclass
class TeamComposition:
    top: Player
    jungle: Player
    mid: Player
    bottom: Player
    support: Player
    total_cost: float
    total_value: float
    remaining_budget: float = 0.0

    def __str__(self):
        return f"""Best Team Composition:
Top: {self.top.name} ({self.top.team}) - Cost: {self.top.cost} - Avg Score: {self.top.avg_score:.2f}
Jungle: {self.jungle.name} ({self.jungle.team}) - Cost: {self.jungle.cost} - Avg Score: {self.jungle.avg_score:.2f}
Mid: {self.mid.name} ({self.mid.team}) - Cost: {self.mid.cost} - Avg Score: {self.mid.avg_score:.2f}
Bottom: {self.bottom.name} ({self.bottom.team}) - Cost: {self.bottom.cost} - Avg Score: {self.bottom.avg_score:.2f}
Support: {self.support.name} ({self.support.team}) - Cost: {self.support.cost} - Avg Score: {self.support.avg_score:.2f}
Total Cost: {self.total_cost}
Remaining Budget: {self.remaining_budget}
Total Value: {self.total_value}"""