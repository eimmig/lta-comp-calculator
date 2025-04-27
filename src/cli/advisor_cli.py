import argparse
from typing import Dict, List, Optional
from tabulate import tabulate
from src.domain.models import Role, TeamComposition
from src.api.market_api import MarketAPI
from src.api.stats_api import StatsAPI
from src.services.player_analysis import PlayerAnalysisService
from src.services.match_analysis import MatchAnalysisService
from src.services.team_composition import TeamCompositionService
from src.utils.formatters import format_player_stats, format_team_summary

class AdvisorCLI:
    def __init__(self):
        self.market_api = MarketAPI()
        self.stats_api = StatsAPI()
        self.match_analysis = MatchAnalysisService()
        self.team_composition = TeamCompositionService(self.match_analysis)
        self.player_analysis = PlayerAnalysisService()

    def setup_argparse(self) -> argparse.ArgumentParser:
        """Configure command line argument parser"""
        parser = argparse.ArgumentParser(description='Fantasy League Team Advisor')
        parser.add_argument("-k", "--key", type=int, default=0, help="column index to sort role tables")
        parser.add_argument("-r", "--reverse", action="store_true", default=False, help="sort column in reverse order")
        parser.add_argument("-v", "--valorTotal", type=float, help="valor total disponível para escalar o time")
        return parser

    def format_role_table(self, role: str, players: List[Dict], team_avg_cost: Dict[str, float],
                         opponent_dict: Dict[str, List[str]], stats_data: Dict) -> List[List]:
        """Format player data into a table for display"""
        role_table = []
        
        role_costs = [p["cost"] for p in players]
        role_avg_cost = sum(role_costs) / len(role_costs) if role_costs else 0
        
        for player in players:
            name = player["name"]
            team = player["team"]
            cost = player["cost"]
            
            # Get player stats
            player_obj = self.player_analysis.create_player(
                name=name,
                team=team,
                cost=cost,
                role=Role(role),
                stats_data=self.stats_api.get_player_stats(name, stats_data),
                opponent_dict=opponent_dict,
                team_avg_cost=team_avg_cost
            )
            
            # Format player stats
            stats_str = format_player_stats(player_obj)
            
            # Calculate player value
            value = self.team_composition.calculate_player_score(player_obj)
            
            role_table.append([
                name,
                team,
                cost,
                "",  # Computation details placeholder
                stats_str,
                round(value, 2)
            ])
            
        return role_table

    def run(self) -> None:
        """Main entry point for the CLI application"""
        parser = self.setup_argparse()
        args = parser.parse_args()

        if args.key < 0 or args.key > 5:
            print(f"Error: invalid key '{args.key}'")
            exit(1)

        try:
            # Fetch data
            market_data = self.market_api.fetch_market_data()
            stats_data = self.stats_api.fetch_player_stats()
            
            # Process match data and display matches
            opponent_dict = {}
            if "matches" in market_data:
                opponent_dict = self.match_analysis.process_match_data(market_data["matches"])
                matches_table = [[team, ", ".join(opponents)] for team, opponents in opponent_dict.items()]
                matches_table.sort(key=lambda x: x[0])
                print(tabulate(matches_table, headers=["Team", "Opponents"]))
                print()
                
            # Calculate team averages
            team_avg_cost = self.market_api.calculate_team_averages(market_data)
            
            # Display tables for each role
            for role in Role:
                role_table = self.format_role_table(
                    role.value,
                    market_data[role.value],
                    team_avg_cost,
                    opponent_dict,
                    stats_data
                )
                
                role_table.sort(key=lambda x: x[args.key], reverse=args.reverse)
            
            # Find best team composition if budget is provided
            if args.valorTotal is not None:
                players_by_role = {}
                for role in Role:
                    players_by_role[role] = []
                    for p_data in market_data[role.value]:
                        player = self.player_analysis.create_player(
                            name=p_data["name"],
                            team=p_data["team"],
                            cost=p_data["cost"],
                            role=role,
                            stats_data=self.stats_api.get_player_stats(p_data["name"], stats_data),
                            opponent_dict=opponent_dict,
                            team_avg_cost=team_avg_cost
                        )
                        players_by_role[role].append(player)
                
                best_comp = self.team_composition.find_best_composition(
                    players_by_role,
                    args.valorTotal,
                    opponent_dict
                )
                
                print("\nBest Team Composition for Your Budget:")
                print("-" * 50)
                print(best_comp)
                print("\nDetailed Analysis:")
                print(format_team_summary(best_comp))
                
        except Exception as e:
            print(f"Error: {str(e)}")
            exit(1)