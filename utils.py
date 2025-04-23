from typing import Dict, List
from models import Player, TeamComposition
from itertools import product

def calculate_team_averages(yamlfile: Dict) -> Dict[str, float]:
    """Returns a dictionary with the average cost of each team."""
    team_costs = {}
    roles = ["top", "jungle", "mid", "bottom", "support"]

    for role in roles:
        for player in yamlfile[role]:
            team = player["team"]
            cost = player["cost"]
            team_costs.setdefault(team, []).append(cost)

    return {team: sum(costs) / len(costs) for team, costs in team_costs.items()}

def create_player_objects(yamlfile: Dict, role_values: Dict[str, List[float]], player_stats_data: Dict = None) -> Dict[str, List[Player]]:
    """Creates Player objects from YAML data with calculated values and stats."""
    role_players = {
        "top": [], "jungle": [], "mid": [], "bottom": [], "support": []
    }
    
    for role in role_players.keys():
        for idx, player_dict in enumerate(yamlfile[role]):
            # Get player stats if available
            player_name = player_dict["name"]
            player_stats_entry = None
            
            if player_stats_data and "data" in player_stats_data:
                player_stats_entry = next(
                    (p for p in player_stats_data["data"]["players"] 
                     if p["playerName"].strip().lower() == player_name.strip().lower()),
                    None
                )
            
            player = Player(
                name=player_name,
                team=player_dict["team"],
                cost=player_dict["cost"],
                value=role_values[role][idx],
                avg_score=player_stats_entry["averageRoundScore"] if player_stats_entry else 0,
                last_score=player_stats_entry["lastRoundScore"] if player_stats_entry else 0,
                max_score=player_stats_entry["maxRoundScore"] if player_stats_entry else 0,
                min_score=player_stats_entry["minRoundScore"] if player_stats_entry else 0
            )
            role_players[role].append(player)
    
    return role_players

def pre_filter_players(role_players: Dict[str, List[Player]], min_avg_score: float = 5.0) -> Dict[str, List[Player]]:
    """Pre-filtra jogadores com base em critérios mínimos de performance."""
    filtered = {}
    for role, players in role_players.items():
        filtered[role] = [
            p for p in players 
            if p.avg_score and p.avg_score >= min_avg_score
        ]
    return filtered

def calculate_role_synergy(player1: Player, player2: Player, role1: str, role2: str) -> float:
    """Calcula sinergia entre duas posições específicas."""
    synergy = 0.0
    
    # Sinergia jungle-mid apenas quando do mesmo time
    if {role1, role2} == {'jungle', 'mid'}:
        if player1.team == player2.team:
            synergy = 3.0
            
            # Penaliza diferença muito grande na força dos oponentes
            if hasattr(player1, 'opponent_strength') and hasattr(player2, 'opponent_strength'):
                opp_diff = abs(player1.opponent_strength - player2.opponent_strength)
                if opp_diff > 0.3:  # Se diferença maior que 30%
                    synergy *= (1 - min(opp_diff, 0.5))  # Reduz até 50% da sinergia
            
    # Sinergia bottom-support com ênfase em consistência
    elif {role1, role2} == {'bottom', 'support'}:
        if player1.team == player2.team:
            synergy = 4.0
        else:
            synergy = 1.5
            
        # Ajusta sinergia baseado na consistência da dupla
        support = player1 if role1 == 'support' else player2
        adc = player2 if role1 == 'support' else player1
        
        # Calcula consistência de ambos
        support_consistency = 1 - min(1, (support.max_score - support.min_score) / support.avg_score) if support.avg_score > 0 else 0
        adc_consistency = 1 - min(1, (adc.max_score - adc.min_score) / adc.avg_score) if adc.avg_score > 0 else 0
        
        # Penaliza mais fortemente support inconsistente
        if support_consistency < 0.4:  # Support precisa ser consistente
            synergy *= 0.5
        elif adc_consistency < 0.3:  # ADC pode ser um pouco menos consistente
            synergy *= 0.7
            
    return synergy

def calculate_team_score(composition: list, opponent_dict: Dict[str, List[str]] = None) -> float:
    """
    Calcula uma pontuação para uma composição de time considerando:
    - Pontuação média dos jogadores (peso maior)
    - Média do time como um todo
    - Relação custo/benefício
    - Força dos oponentes
    - Tendência de pontuação (com ajuste para partidas contra times fracos)
    - Consistência
    - Sinergia entre posições (apenas para duos do mesmo time)
    - Penalização infinita para jogadores de times que se enfrentarão
    """
    # Check if any players are from teams that will face each other
    if opponent_dict:
        player_teams = {player.team for player in composition}
        for team in player_teams:
            if team in opponent_dict:
                opponents = opponent_dict[team]
                if any(opponent in player_teams for opponent in opponents):
                    return float('-inf')

    total_score = 0
    valid_players = 0
    team_avg_score = 0
    roles = ['top', 'jungle', 'mid', 'bottom', 'support']
    
    # Coletando médias para cálculo do multiplicador
    for player in composition:
        if player.avg_score and player.avg_score > 0:
            team_avg_score += float(player.avg_score)
            valid_players += 1

    if valid_players < len(composition):
        return float('-inf')
        
    team_avg_score = team_avg_score / valid_players if valid_players > 0 else 0
    
    # Bônus dinâmico baseado na média do time
    avg_score_multiplier = 1.0 + (team_avg_score / 20)  # Crescimento mais gradual
    
    # Calcula sinergias entre posições
    synergy_score = 0
    for i in range(len(composition)):
        for j in range(i + 1, len(composition)):
            synergy_score += calculate_role_synergy(
                composition[i], composition[j],
                roles[i], roles[j]
            )

    for idx, player in enumerate(composition):
        if not player.avg_score or player.avg_score <= 0:
            continue
            
        avg_score = float(player.avg_score)
        last_score = float(player.last_score) if player.last_score else avg_score
        max_score = float(player.max_score) if player.max_score else avg_score
        min_score = float(player.min_score) if player.min_score else avg_score
        cost = float(player.cost) if player.cost else 0
        role = roles[idx]
        
        # Score base com peso dinâmico baseado na consistência histórica
        consistency = 1 - min(1, (max_score - min_score) / avg_score) if avg_score > 0 else 0
        
        # Ajusta pesos base por role
        if role in ['mid', 'bottom']:
            base_multiplier = 4.0 + (consistency * 2.0)  # 4.0 a 6.0 para carries
        elif role == 'support':
            base_multiplier = 3.0 + (consistency * 3.0)  # 3.0 a 6.0 para support (mais ênfase em consistência)
        else:
            base_multiplier = 3.0 + (consistency * 2.0)  # 3.0 a 5.0 para outros
            
        player_score = avg_score * base_multiplier
        
        # Eficiência de custo com peso dinâmico por role
        if cost > 0:
            cost_efficiency = avg_score / cost
            if role in ['mid', 'bottom']:
                efficiency_weight = 12 + (2 * consistency)  # 12 a 14 para carries
            elif role == 'support':
                efficiency_weight = 8 + (4 * consistency)   # 8 a 12 para support
            else:
                efficiency_weight = 10 + (2 * consistency)  # 10 a 12 para outros
            player_score += cost_efficiency * efficiency_weight
        
        # Tendência de performance com peso dinâmico
        trend = last_score - avg_score
        if trend > 0:
            if role == 'support':
                # Supports precisam ser mais consistentes, então reduzimos peso de spikes
                trend_weight = 1.0 + (consistency * 2.0)  # 1.0 a 3.0
            else:
                trend_weight = 1.5 + (consistency * 1.5)  # 1.5 a 3.0
                
            if last_score > (avg_score * 1.5):
                player_score += trend * (trend_weight * 0.5)  # Reduz peso para outliers
            else:
                player_score += trend * trend_weight
        else:
            # Penaliza tendências negativas mais fortemente em carries
            if role in ['mid', 'bottom']:
                player_score += trend * 1.5
            else:
                player_score += trend
        
        total_score += player_score

    # Aplica multiplicador de média do time e adiciona bônus de sinergia
    final_score = (total_score / len(composition)) * avg_score_multiplier
    final_score += synergy_score

    return final_score

def find_best_team_composition(role_players: Dict[str, List[Player]], budget: float, 
                             opponent_dict: Dict[str, List[str]] = None) -> TeamComposition:
    """Returns the best possible team composition within the given budget."""
    best_composition = None
    best_score = float('-inf')
    
    # Pre-filtra jogadores com baixa performance
    filtered_players = pre_filter_players(role_players)
    
    # Get all possible combinations of players for each role
    combinations = product(
        filtered_players['top'],
        filtered_players['jungle'],
        filtered_players['mid'],
        filtered_players['bottom'],
        filtered_players['support']
    )
    
    for top, jungle, mid, bottom, support in combinations:
        comp = [top, jungle, mid, bottom, support]
        total_cost = sum(player.cost for player in comp)
        
        # Skip if combination exceeds budget
        if total_cost > budget:
            continue
        
        # Calculate team score using the enhanced scoring system
        team_score = calculate_team_score(comp, opponent_dict)
        
        # Update best composition if current one has higher score
        if best_composition is None or team_score > best_score:
            best_score = team_score
            best_composition = TeamComposition(
                top=top,
                jungle=jungle,
                mid=mid,
                bottom=bottom,
                support=support,
                total_cost=total_cost,
                total_value=team_score,
                remaining_budget=budget - total_cost
            )
    
    return best_composition