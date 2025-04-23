from typing import Dict, List, Any
from src.domain.models import Player, TeamComposition

def format_player_stats(player: Player) -> str:
    """Format player statistics for display"""
    if not player.stats:
        return "no stats"
        
    return (f"avg:{player.stats.avg_score:.1f} "
            f"last:{player.stats.last_score:.1f} "
            f"trend:{player.stats.trend:+.1f} "
            f"consistency:{player.stats.consistency:.0%}")

def format_team_summary(composition: TeamComposition) -> str:
    """Format team summary statistics"""
    total_cost_eff = sum(p.cost_efficiency for p in composition.players if p.stats)
    avg_cost_eff = total_cost_eff / len(composition.players)
    
    total_trend = sum(p.stats.trend for p in composition.players if p.stats)
    avg_trend = total_trend / len(composition.players)
    
    total_consistency = sum(p.stats.consistency for p in composition.players if p.stats)
    avg_consistency = total_consistency / len(composition.players)
    
    return f"""Team Summary:
Average Cost Efficiency: {avg_cost_eff:.2f}
Overall Score Trend: {avg_trend:+.2f}
Team Consistency: {avg_consistency:.1%}
"""

def format_computation_details(computation: Dict[str, Any]) -> str:
    """Format computation details for display"""
    details = []
    
    if "base_score" in computation:
        details.append(f"base:{computation['base_score']:.1f}")
    if "efficiency" in computation:
        details.append(f"eff:{computation['efficiency']:.2f}")
    if "trend" in computation:
        details.append(f"trend:{computation['trend']:+.1f}")
    if "synergy" in computation:
        details.append(f"syn:{computation['synergy']:.1f}")
        
    return " ".join(details)

def format_match_table(matches: List[List[str]]) -> List[List[str]]:
    """Format match data into a table"""
    return [[f"{team1} vs {team2}"] for team1, team2 in matches]