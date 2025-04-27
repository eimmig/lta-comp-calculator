from typing import Dict, List, Optional
from itertools import product
from src.domain.models import Player, TeamComposition, Role
from src.domain.exceptions import InvalidBudgetError, InvalidTeamCompositionError, OpponentConflictError
from src.services.match_analysis import MatchAnalysisService
from src.utils.calculators import is_easy_match

class TeamCompositionService:
    def __init__(self, match_analysis_service: MatchAnalysisService):
        self.match_analysis = match_analysis_service
        self.opponent_multipliers = {
            'very_weak': 1.4,    # 40% bonus para oponentes muito fracos
            'weak': 1.2,         # 20% bonus para oponentes fracos
            'average': 1.0,      # sem ajuste para oponentes médios
            'strong': 0.9,       # -10% para oponentes fortes
            'very_strong': 0.8   # -20% para oponentes muito fortes
        }

    def _get_opponent_strength_category(self, player: Player) -> str:
        """Categoriza a força do oponente"""
        if not hasattr(player, 'opponent_strength'):
            return 'average'
            
        if player.opponent_strength < 0.75:
            return 'very_weak'
        elif player.opponent_strength < 0.85:
            return 'weak'
        elif player.opponent_strength < 1.15:
            return 'average'
        elif player.opponent_strength < 1.25:
            return 'strong'
        else:
            return 'very_strong'

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
        
        # Aplica multiplicador baseado na força do oponente
        opponent_category = self._get_opponent_strength_category(player)
        score *= self.opponent_multipliers[opponent_category]
        
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

    def _is_valid_team_composition(self, players: List[Player]) -> bool:
        """Verifica se a composição é válida considerando as regras de times e oponentes"""
        team_counts = {}
        for p in players:
            team_counts[p.team] = team_counts.get(p.team, 0) + 1
            
        for team_id, count in team_counts.items():
            if count > 3:
                # Permite mais de 3 jogadores apenas se TODOS tiverem confronto contra time fraco
                team_players = [p for p in players if p.team == team_id]
                if not all(self._get_opponent_strength_category(p) in ['very_weak', 'weak'] for p in team_players):
                    return False
        return True

    def _calculate_weak_opponent_bonus(self, players: List[Player]) -> float:
        """Calcula o bônus baseado na quantidade de jogadores contra times fracos"""
        weak_opponent_count = sum(1 for p in players if self._get_opponent_strength_category(p) in ['very_weak', 'weak'])
        return 1.0 + (weak_opponent_count * 0.1)  # Até 50% de bônus para 5 jogadores

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
        
        print("Calculando stats...")
        # Get all possible combinations of players for each role
        combinations = product(
            role_players[Role.TOP],
            role_players[Role.JUNGLE],
            role_players[Role.MID],
            role_players[Role.BOTTOM],
            role_players[Role.SUPPORT]
        )
        
        for top, jungle, mid, bottom, support in combinations:
            players = [top, jungle, mid, bottom, support]
            total_cost = sum(p.cost for p in players)
            
            # Skip if combination exceeds budget
            if total_cost > budget:
                continue

            # Verifica se a composição é válida considerando regras de time
            if not self._is_valid_team_composition(players):
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
            
            # Calcula pontuação base
            team_score = self.calculate_team_score(composition, opponent_dict)
            
            # Aplica bônus por jogadores contra times fracos
            team_score *= self._calculate_weak_opponent_bonus(players)
            
            if team_score > best_score:
                best_score = team_score
                composition.total_value = team_score
                best_composition = composition
        
        if best_composition is None:
            raise InvalidTeamCompositionError("Could not find a valid team composition")
        
        print("\nMelhor composição encontrada:")
        print(f"Pontuação total: {best_composition.total_value:.2f}")
        print(f"Custo total: {best_composition.total_cost:.2f}")
        print(f"Orçamento restante: {best_composition.remaining_budget:.2f}")
        
        print("\nDetalhes dos jogadores:")
        for role, player in [
            ("TOP", best_composition.top),
            ("JUNGLE", best_composition.jungle),
            ("MID", best_composition.mid),
            ("BOTTOM", best_composition.bottom),
            ("SUPPORT", best_composition.support)
        ]:
            print(f"\n{role}:")
            print(f"  Nome: {player.name}")
            print(f"  Time: {player.team}")
            print(f"  Custo: {player.cost:.2f}")
            if hasattr(player, 'stats'):
                print(f"  Média: {player.stats.avg_score:.2f}")
                print(f"  Tendência: {player.stats.trend:+.2f}")
                print(f"  Consistência: {player.stats.consistency:.2f}")
            if hasattr(player, 'opponent_strength'):
                print(f"  Força do oponente: {player.opponent_strength:.2f}")
            
        return best_composition