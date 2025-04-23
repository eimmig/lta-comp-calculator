from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum

class Role(Enum):
    TOP = "top"
    JUNGLE = "jungle"
    MID = "mid"
    BOTTOM = "bottom"
    SUPPORT = "support"

@dataclass
class PlayerStats:
    avg_score: float = 0.0
    last_score: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0
    
    @property
    def trend(self) -> float:
        """Calcula a tendência de performance do jogador"""
        return self.last_score - self.avg_score if self.avg_score > 0 else 0.0
    
    @property
    def consistency(self) -> float:
        """Calcula o índice de consistência do jogador"""
        if self.avg_score <= 0:
            return 0.0
        variance = (self.max_score - self.min_score) / self.avg_score
        return 1 - min(1, variance)

@dataclass
class Player:
    name: str
    team: str
    cost: float
    role: Role
    value: float = 0.0
    stats: Optional[PlayerStats] = None
    opponent_strength: float = 1.0

    @property
    def cost_efficiency(self) -> float:
        """Calcula a eficiência de custo do jogador"""
        if not self.stats or self.cost <= 0:
            return 0.0
        return self.stats.avg_score / self.cost

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

    @property
    def players(self) -> List[Player]:
        """Retorna lista de jogadores na composição"""
        return [self.top, self.jungle, self.mid, self.bottom, self.support]
    
    @property
    def avg_score(self) -> float:
        """Calcula score médio do time"""
        valid_scores = [p.stats.avg_score for p in self.players if p.stats and p.stats.avg_score > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    
    def __str__(self):
        def format_player(player: Player) -> str:
            avg_score = player.stats.avg_score if player.stats else 0.0
            return f"{player.name} ({player.team}) - Cost: {player.cost} - Avg Score: {avg_score:.2f}"

        return f"""Best Team Composition:
Top: {format_player(self.top)}
Jungle: {format_player(self.jungle)}
Mid: {format_player(self.mid)}
Bottom: {format_player(self.bottom)}
Support: {format_player(self.support)}
Total Cost: {self.total_cost}
Remaining Budget: {self.remaining_budget}
Total Value: {self.total_value}"""