from typing import Dict, List, Optional
from src.domain.models import Player, PlayerStats, Role
from src.domain.exceptions import PlayerNotFoundError, InvalidPlayerStatsError

class PlayerAnalysisService:
    @staticmethod
    def create_player_stats(stats_data: Dict) -> Optional[PlayerStats]:
        """Creates PlayerStats object from raw stats data"""
        if not stats_data:
            return None
            
        return PlayerStats(
            avg_score=float(stats_data.get("averageRoundScore") or 0),
            last_score=float(stats_data.get("lastRoundScore") or 0),
            max_score=float(stats_data.get("maxRoundScore") or 0),
            min_score=float(stats_data.get("minRoundScore") or 0)
        )

    @staticmethod
    def calculate_opponent_strength(
        team: str,
        opponent_dict: Dict[str, List[str]],
        team_avg_cost: Dict[str, float],
        role_avg_cost: float
    ) -> float:
        """Calculate the relative strength of a team's opponents."""
        if team not in opponent_dict:
            return 1.0
            
        opponent_strengths = []
        for opponent in opponent_dict[team]:
            if opponent in team_avg_cost:
                # Normalize team strength relative to role average
                opponent_strengths.append(team_avg_cost[opponent] / role_avg_cost)
        
        return sum(opponent_strengths) / len(opponent_strengths) if opponent_strengths else 1.0

    @staticmethod
    def create_player(
        name: str,
        team: str,
        cost: float,
        role: Role,
        value: float = 0.0,
        stats_data: Dict = None,
        opponent_dict: Dict[str, List[str]] = None,
        team_avg_cost: Dict[str, float] = None,
        role_avg_cost: float = None
    ) -> Player:
        """Creates a Player object with all necessary calculations"""
        stats = PlayerAnalysisService.create_player_stats(stats_data) if stats_data else None
        
        opponent_strength = 1.0
        if all([opponent_dict, team_avg_cost, role_avg_cost]):
            opponent_strength = PlayerAnalysisService.calculate_opponent_strength(
                team, opponent_dict, team_avg_cost, role_avg_cost
            )
            
        return Player(
            name=name,
            team=team,
            cost=cost,
            role=role,
            value=value,
            stats=stats,
            opponent_strength=opponent_strength
        )

    @staticmethod
    def filter_valid_players(players: List[Player], min_avg_score: float = 5.0) -> List[Player]:
        """Filters players based on minimum performance criteria"""
        return [
            p for p in players 
            if p.stats and p.stats.avg_score >= min_avg_score
        ]