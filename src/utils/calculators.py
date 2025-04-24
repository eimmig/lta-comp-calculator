from typing import List, Dict
from src.domain.models import Player

def calculate_role_average_cost(players: List[Dict]) -> float:
    """Calculate average cost for a specific role"""
    costs = [p["cost"] for p in players if p.get("cost")]
    return sum(costs) / len(costs) if costs else 0.0

def calculate_team_efficiency(players: List[Player]) -> float:
    """Calculate overall team efficiency (points per cost)"""
    total_efficiency = 0.0
    valid_players = 0
    
    for player in players:
        if player.stats and player.stats.avg_score > 0 and player.cost > 0:
            total_efficiency += player.cost_efficiency
            valid_players += 1
            
    return total_efficiency / valid_players if valid_players > 0 else 0.0

def normalize_score(score: float, min_score: float, max_score: float) -> float:
    """Normalize a score to a 0-1 range"""
    if max_score == min_score:
        return 0.5
    return (score - min_score) / (max_score - min_score)

def weighted_average(values: List[float], weights: List[float]) -> float:
    """Calculate weighted average of values"""
    if not values or not weights or len(values) != len(weights):
        return 0.0
        
    total = sum(v * w for v, w in zip(values, weights))
    weight_sum = sum(weights)
    
    return total / weight_sum if weight_sum > 0 else 0.0

def is_easy_match(player: Player) -> bool:
    """Retorna True se o confronto do jogador for considerado fácil com base em opponent_strength."""
    # Considera fácil se a força do adversário for 15% menor que a média
    return hasattr(player, 'opponent_strength') and player.opponent_strength < 0.85