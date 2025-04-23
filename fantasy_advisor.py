#!/usr/bin/env python3

import argparse
import tabulate
import requests
from typing import Dict, List, Tuple
from models import Player, TeamComposition
from utils import calculate_team_averages, create_player_objects, find_best_team_composition

NAME = "name"
TEAM = "team"
COST = "cost"
ROLES = ["top", "jungle", "mid", "bottom", "support"]

def fetch_market_data() -> Dict:
    """
    Fetch market data from the API and adapt to expected structure.
    Returns a dictionary with player data organized by roles and match information.
    """
    try:
        response = requests.get("https://api.ltafantasy.com/market")
        response.raise_for_status()
        api_data = response.json()
        
        # Initialize roles dictionary with empty lists
        roles = {role: [] for role in ROLES}
        matches = set()
        
        # Get the teams mapping for easier access
        teams_by_id = {team["id"]: team for team in api_data.get("data", {}).get("teams", [])}
        
        # Process player data from the response using roundPlayers instead of players
        players = api_data.get("data", {}).get("roundPlayers", [])
        if not players:
            raise ValueError("Missing required player data")
            
        for player in players:
            role = player.get("role", "").lower()
            if role in roles:
                # Get team info
                team_id = player.get("teamId")
                team_info = teams_by_id.get(team_id, {})
                team_name = team_info.get("name", "Unknown")
                
                player_data = {
                    "name": player.get("summonerName", ""),
                    "team": team_name,
                    "cost": float(player.get("price", 0))
                }
                
                roles[role].append(player_data)
                
                # Process matches from upcomingOpponents
                upcoming = player.get("upcomingOpponents", [])
                if upcoming and team_name != "Unknown":
                    for opp in upcoming:
                        opp_team = opp.get("teamName")
                        if opp_team and opp_team != team_name:
                            match = tuple(sorted([team_name, opp_team]))
                            matches.add(match)
        
        # Validate we have players for all roles
        empty_roles = [role for role in ROLES if not roles[role]]
        if empty_roles:
            raise ValueError(f"Missing data for roles: {', '.join(empty_roles)}")
        
        result = {
            "matches": [list(m) for m in matches],
            **roles  # Unpacks all roles directly into the return dictionary
        }
        
        return result
        
    except requests.RequestException as e:
        print(f"Error fetching market data: {e}")
        raise
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error processing market data: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while fetching market data: {e}")
        raise

def fetch_player_stats() -> Dict:
    """Fetch player statistics from the API."""
    try:
        response = requests.get("https://api.ltafantasy.com/player-stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return {"data": {"players": []}}

def process_match_data(matches: List[List[str]]) -> Tuple[Dict[str, List[str]], List[List[str]]]:
    """Process match data and return opponent dictionary and table."""
    opponent_dict = {}
    
    # Create opponent dictionary
    for match in matches:
        team1, team2 = match
        opponent_dict.setdefault(team1, []).append(team2)
        opponent_dict.setdefault(team2, []).append(team1)
    
    # Create table for display
    opponent_table = [[team, opponents] for team, opponents in opponent_dict.items()]
    opponent_table.sort(key=lambda x: x[0])
    
    return opponent_dict, opponent_table

def calculate_opponent_strength(team: str, opponent_dict: Dict[str, List[str]], 
                              team_avg_cost: Dict[str, float], role_avg_cost: float) -> float:
    """Calculate the relative strength of a team's opponents."""
    if team not in opponent_dict:
        return 1.0
        
    opponent_strengths = []
    for opponent in opponent_dict[team]:
        if opponent in team_avg_cost:
            # Normalize team strength relative to role average
            opponent_strengths.append(team_avg_cost[opponent] / role_avg_cost)
    
    return sum(opponent_strengths) / len(opponent_strengths) if opponent_strengths else 1.0

def process_role_data(role: str, data: Dict, opponent_dict: Dict[str, List[str]], 
                     team_avg_cost: Dict[str, float], player_stats_data: Dict) -> Tuple[List[List], List[float]]:
    """Process data for a specific role and return role table and values."""
    # Calculate role average cost for normalization
    role_costs = [player_dict[COST] for player_dict in data[role]]
    role_avg_cost = sum(role_costs) / len(role_costs) if role_costs else 0
    
    role_table = []
    role_values = []
    
    for player_dict in data[role]:
        team = player_dict[TEAM]
        name = player_dict[NAME]
        player_cost = player_dict[COST] or 0
        
        # Find player stats
        player_stats = next(
            (p for p in player_stats_data.get("data", {}).get("players", []) 
             if p["playerName"].strip().lower() == name.strip().lower()),
            None
        )
        
        # Calculate opponent strength
        opponent_strength = calculate_opponent_strength(
            team, opponent_dict, team_avg_cost, role_avg_cost
        ) if role_avg_cost > 0 else 1.0
        
        # Calculate base matchup cost
        opponents = opponent_dict.get(team, [])
        cost_against = sum(next((p[COST] for p in data[role] if p[TEAM] == opp), 0) for opp in opponents)
        cost_against_str = str(player_cost)
        for opp in opponents:
            opp_cost = next((p[COST] for p in data[role] if p[TEAM] == opp), 0)
            cost_against_str += f" - {opp_cost}"
        
        # Calculate performance metrics
        if player_stats:
            avg_score = float(player_stats.get("averageRoundScore") or 0)
            last_score = float(player_stats.get("lastRoundScore") or 0)
            max_score = float(player_stats.get("maxRoundScore") or 0)
            
            # Normalize scores by opponent strength
            performance_ratio = avg_score / player_cost if player_cost > 0 else 0
            
            # Calculate trend and consistency
            trend = last_score - avg_score
            consistency = 1 - min(1, (max_score - avg_score) / avg_score) if avg_score > 0 else 0
            
            # Penalize high scores against weak opponents
            score_spike = max(0, (last_score - avg_score) / avg_score if avg_score > 0 else 0)
            weakness_penalty = score_spike * (1 - opponent_strength) * -0.2
            
            # Calculate final value components
            base_value = player_cost - cost_against
            efficiency_bonus = performance_ratio * 0.3
            consistency_bonus = consistency * 0.15
            trend_factor = (trend * opponent_strength * 0.2)
            
            # Combine all factors
            adjusted_value = (base_value + 
                            efficiency_bonus + 
                            consistency_bonus + 
                            trend_factor + 
                            weakness_penalty)
            
            stats_str = (f"avg:{avg_score:.1f} last:{last_score:.1f} "
                        f"opp_str:{opponent_strength:.2f} trend:{trend:+.1f}")
        else:
            adjusted_value = player_cost - cost_against
            stats_str = "no stats"
        
        cost_against_str += " ="
        role_values.append(adjusted_value)
        
        role_table.append([
            name,
            team,
            player_cost,
            cost_against_str,
            stats_str,
            round(adjusted_value, 2)
        ])

    return role_table, role_values

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--key", default=0, type=int, help="column index to sort role tables")
    parser.add_argument("-r", "--reverse", action="store_true", default=False, help="sort column in reverse order")
    parser.add_argument("-v", "--valorTotal", type=float, help="valor total disponível para escalar o time")

    args = parser.parse_args()

    if args.key < 0 or args.key > 5:
        print(f"Error: invalid key '{args.key}'")
        exit(1)

    try:
        # Fetch data from API
        market_data = fetch_market_data()
        player_stats_data = fetch_player_stats()

        # Process match data
        opponent_dict, opponent_table = process_match_data(market_data["matches"])
        print(tabulate.tabulate(opponent_table, headers=[TEAM, "opponents"]))
        print()

        # Calculate average cost per team
        team_avg_cost = calculate_team_averages(market_data)
        role_values = {role: [] for role in ROLES}

        # Process each role
        for role in ROLES:
            role_table, values = process_role_data(role, market_data, opponent_dict, team_avg_cost, player_stats_data)
            role_values[role] = values
            
            role_table.sort(key=lambda x: x[args.key], reverse=args.reverse)
            print(tabulate.tabulate(role_table, headers=[NAME, TEAM, COST, "computation", "stats", "value"]))
            print()

        # If budget is provided, find and display the best team composition
        if args.valorTotal is not None:
            role_players = create_player_objects(market_data, role_values, player_stats_data)
            best_composition = find_best_team_composition(
                role_players, 
                args.valorTotal,
                opponent_dict
            )
            
            if best_composition is not None:
                print("\nBest Team Composition for Your Budget:")
                print("-" * 50)
                print(best_composition)
                
                print("\nDetailed Analysis:")
                print("-" * 50)
                total_opp_strength = 0
                total_trend = 0
                total_consistency = 0
                total_efficiency = 0
                
                for role, player in [("Top", best_composition.top), 
                                   ("Jungle", best_composition.jungle),
                                   ("Mid", best_composition.mid),
                                   ("Bottom", best_composition.bottom),
                                   ("Support", best_composition.support)]:
                    
                    player_stats = next(
                        (p for p in player_stats_data["data"]["players"] 
                         if p["playerName"].strip().lower() == player.name.strip().lower()),
                        None
                    )
                    
                    if player_stats:
                        avg_score = float(player_stats.get("averageRoundScore") or 0)
                        last_score = float(player_stats.get("lastRoundScore") or 0)
                        max_score = float(player_stats.get("maxRoundScore") or 0)
                        min_score = float(player_stats.get("minRoundScore") or 0)
                        trend = last_score - avg_score
                        
                        # Calculate metrics
                        efficiency = (avg_score/player.cost if player.cost > 0 else 0)
                        consistency = 1 - min(1, (max_score - min_score) / avg_score) if avg_score > 0 else 0
                        opp_str = calculate_opponent_strength(
                            player.team, 
                            opponent_dict, 
                            team_avg_cost, 
                            sum(p.cost for p in role_players[role.lower()]) / len(role_players[role.lower()])
                        )
                        
                        # Accumulate team metrics
                        total_opp_strength += opp_str
                        total_trend += trend
                        total_consistency += consistency
                        total_efficiency += efficiency
                        
                        print(f"{role}: {player.name}")
                        print(f"  Avg Score: {avg_score:.2f}")
                        print(f"  Last Score: {last_score:.2f}")
                        print(f"  Score Trend: {trend:+.2f}")
                        print(f"  Cost Efficiency: {efficiency:.2f} points/cost")
                        print(f"  Consistency: {consistency:.2%}")
                        print(f"  Opponent Strength: {opp_str:.2f}")
                        print()
                    else:
                        print(f"{role}: {player.name} - No stats available\n")
                
                print("Team Summary:")
                print(f"Average Opponent Strength: {total_opp_strength/5:.2f}")
                print(f"Overall Score Trend: {total_trend/5:+.2f}")
                print(f"Team Consistency: {total_consistency/5:.2%}")
                print(f"Average Cost Efficiency: {total_efficiency/5:.2f}")
                
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
