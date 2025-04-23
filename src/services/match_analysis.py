from typing import Dict, List, Set, Tuple
from src.domain.models import Player, Role
from src.domain.exceptions import OpponentConflictError

class MatchAnalysisService:
    @staticmethod
    def check_opposing_teams(players: List[Player], opponent_dict: Dict[str, List[str]]) -> bool:
        """Verifica se há jogadores de times que se enfrentarão"""
        if not opponent_dict:
            return False
            
        player_teams = {player.team for player in players}
        for team in player_teams:
            if team in opponent_dict:
                opponents = opponent_dict[team]
                if any(opponent in player_teams for opponent in opponents):
                    return True
        return False

    @staticmethod
    def _calculate_jungle_mid_synergy(player1: Player, player2: Player) -> float:
        """Calcula sinergia entre jungle e mid"""
        if player1.team != player2.team:
            return 0.0
            
        synergy = 3.0
        # Penaliza diferença muito grande na força dos oponentes
        opp_diff = abs(player1.opponent_strength - player2.opponent_strength)
        if opp_diff > 0.3:  # Se diferença maior que 30%
            synergy *= (1 - min(opp_diff, 0.5))  # Reduz até 50% da sinergia
        return synergy

    @staticmethod
    def _calculate_bot_support_synergy(adc: Player, support: Player) -> float:
        """Calcula sinergia entre ADC e support"""
        base_synergy = 4.0 if adc.team == support.team else 1.5
        
        # Verifica consistência do support
        if support.stats and support.stats.consistency < 0.4:
            return base_synergy * 0.5
            
        # Verifica consistência do ADC
        if adc.stats and adc.stats.consistency < 0.3:
            return base_synergy * 0.7
            
        return base_synergy

    @staticmethod
    def calculate_role_synergy(player1: Player, player2: Player) -> float:
        """Calcula sinergia entre duas posições específicas"""
        if player1.role not in Role or player2.role not in Role:
            return 0.0

        roles = {player1.role, player2.role}
        
        # Sinergia jungle-mid apenas quando do mesmo time
        if roles == {Role.JUNGLE, Role.MID}:
            jungle = player1 if player1.role == Role.JUNGLE else player2
            mid = player2 if player1.role == Role.JUNGLE else player1
            return MatchAnalysisService._calculate_jungle_mid_synergy(jungle, mid)
                
        # Sinergia bottom-support com ênfase em consistência
        elif roles == {Role.BOTTOM, Role.SUPPORT}:
            adc = player1 if player1.role == Role.BOTTOM else player2
            support = player2 if player1.role == Role.BOTTOM else player1
            return MatchAnalysisService._calculate_bot_support_synergy(adc, support)
                
        return 0.0

    @staticmethod
    def calculate_team_synergies(players: List[Player]) -> float:
        """Calcula todas as sinergias entre os jogadores do time"""
        total_synergy = 0.0
        
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                synergy = MatchAnalysisService.calculate_role_synergy(players[i], players[j])
                total_synergy += synergy
                
        return total_synergy

    @staticmethod
    def process_match_data(matches: List[List[str]]) -> Dict[str, List[str]]:
        """Processa dados de partidas e retorna dicionário de oponentes"""
        opponent_dict = {}
        
        for team1, team2 in matches:
            opponent_dict.setdefault(team1, []).append(team2)
            opponent_dict.setdefault(team2, []).append(team1)
            
        return opponent_dict