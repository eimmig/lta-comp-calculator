from typing import Dict, List, Optional
from itertools import product
from src.domain.models import Player, TeamComposition, Role
from src.domain.exceptions import InvalidBudgetError, InvalidTeamCompositionError, OpponentConflictError
from src.services.match_analysis import MatchAnalysisService

class TeamCompositionService:
    def __init__(self, match_analysis_service: MatchAnalysisService):
        self.match_analysis = match_analysis_service

    def _calculate_base_multiplier(self, role: Role, consistency: float) -> float:
        """Calculate base multiplier for a role based on consistency"""
        if role in [Role.MID, Role.BOTTOM]:
            return 4.0 + (consistency * 2.0)  # 4.0 a 6.0 para carries
        elif role == Role.SUPPORT:
            return 3.0 + (consistency * 3.0)  # 3.0 a 6.0 para support
        return 3.0 + (consistency * 2.0)  # 3.0 a 5.0 para outros

    def _calculate_efficiency_weight(self, role: Role, consistency: float) -> float:
        """Calculate efficiency weight for a role based on consistency"""
        if role in [Role.MID, Role.BOTTOM]:
            return 12 + (2 * consistency)  # 12 a 14 para carries
        elif role == Role.SUPPORT:
            return 8 + (4 * consistency)   # 8 a 12 para support
        return 10 + (2 * consistency)      # 10 a 12 para outros

    def _calculate_trend_weight(self, role: Role, consistency: float) -> float:
        """Calculate trend weight for a role based on consistency"""
        if role == Role.SUPPORT:
            return 1.0 + (consistency * 2.0)  # 1.0 a 3.0 para support
        return 1.5 + (consistency * 1.5)      # 1.5 a 3.0 para outros

    def calculate_player_score(self, player: Player) -> float:
        """Calcula a pontuação individual do jogador"""
        if not player.stats or player.stats.avg_score <= 0:
            return 0.0
            
        # Base score com peso dinâmico baseado na consistência
        base_multiplier = self._calculate_base_multiplier(player.role, player.stats.consistency)
        score = player.stats.avg_score * base_multiplier
        
        # Eficiência de custo com peso dinâmico
        if player.cost > 0:
            efficiency_weight = self._calculate_efficiency_weight(player.role, player.stats.consistency)
            score += player.cost_efficiency * efficiency_weight
        
        # Tendência de performance
        if player.stats.trend > 0:
            trend_weight = self._calculate_trend_weight(player.role, player.stats.consistency)
            if player.stats.last_score > (player.stats.avg_score * 1.5):
                score += player.stats.trend * (trend_weight * 0.5)  # Reduz peso para outliers
            else:
                score += player.stats.trend * trend_weight
        else:
            # Penaliza tendências negativas mais fortemente em carries
            multiplier = 1.5 if player.role in [Role.MID, Role.BOTTOM] else 1.0
            score += player.stats.trend * multiplier
                
        return score

    def calculate_team_score(self, composition: TeamComposition, opponent_dict: Dict[str, List[str]] = None) -> float:
        """Calcula a pontuação total da composição do time"""
        # Verifica conflitos de times que se enfrentam
        if opponent_dict and self.match_analysis.check_opposing_teams(composition.players, opponent_dict):
            return float('-inf')
        
        # Calcula pontuação base dos jogadores
        player_scores = []
        for player in composition.players:
            score = self.calculate_player_score(player)
            if score <= 0:
                return float('-inf')
            player_scores.append(score)
            
        if not player_scores:
            return float('-inf')
            
        # Calcula média e aplica multiplicador
        avg_score = sum(player_scores) / len(player_scores)
        score_multiplier = 1.0 + (avg_score / 20)  # Crescimento mais gradual
        
        # Adiciona bônus de sinergia
        synergy_score = self.match_analysis.calculate_team_synergies(composition.players)
        
        final_score = (sum(player_scores) / len(player_scores)) * score_multiplier
        final_score += synergy_score
        
        return final_score

    def find_best_composition(
        self,
        role_players: Dict[Role, List[Player]],
        budget: float,
        opponent_dict: Dict[str, List[str]] = None
    ) -> Optional[TeamComposition]:
        """Encontra a melhor composição de time possível dentro do orçamento"""
        if budget <= 0:
            raise InvalidBudgetError("Budget must be positive")
            
        best_composition = None
        best_score = float('-inf')
        
        # Get all possible combinations of players for each role
        combinations = product(
            role_players[Role.TOP],
            role_players[Role.JUNGLE],
            role_players[Role.MID],
            role_players[Role.BOTTOM],
            role_players[Role.SUPPORT]
        )
        
        for top, jungle, mid, bottom, support in combinations:
            total_cost = sum(p.cost for p in [top, jungle, mid, bottom, support])
            
            # Skip if combination exceeds budget
            if total_cost > budget:
                continue
                
            composition = TeamComposition(
                top=top,
                jungle=jungle,
                mid=mid,
                bottom=bottom,
                support=support,
                total_cost=total_cost,
                total_value=0.0,
                remaining_budget=budget - total_cost
            )
            
            team_score = self.calculate_team_score(composition, opponent_dict)
            
            if team_score > best_score:
                best_score = team_score
                composition.total_value = team_score
                best_composition = composition
        
        if best_composition is None:
            raise InvalidTeamCompositionError("Could not find a valid team composition")
            
        return best_composition