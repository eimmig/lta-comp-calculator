import requests
from typing import Dict, List, Set
from src.domain.exceptions import FantasyAdvisorException

ROLES = ["top", "jungle", "mid", "bottom", "support"]

class MarketAPI:
    def __init__(self, base_url: str = "https://api.ltafantasy.com"):
        self.base_url = base_url.rstrip('/')
        
    def fetch_market_data(self) -> Dict:
        """
        Fetch market data from the API and adapt to expected structure.
        Returns a dictionary with player data organized by roles and match information.
        """
        try:
            response = requests.get(f"{self.base_url}/market")
            response.raise_for_status()
            api_data = response.json()
            
            # Initialize roles dictionary with empty lists
            roles = {role: [] for role in ROLES}
            matches = set()
            
            # Get the teams mapping for easier access
            teams_by_id = {team["id"]: team for team in api_data.get("data", {}).get("teams", [])}
            
            # Process player data from the response using roundPlayers
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
            raise FantasyAdvisorException(f"Error fetching market data: {e}")
        except (ValueError, KeyError, TypeError) as e:
            raise FantasyAdvisorException(f"Error processing market data: {e}")
        except Exception as e:
            raise FantasyAdvisorException(f"Unexpected error while fetching market data: {e}")
            
    def calculate_team_averages(self, market_data: Dict) -> Dict[str, float]:
        """Calculate average cost per team from market data"""
        team_costs = {}
        
        for role in ROLES:
            for player in market_data.get(role, []):
                team = player.get("team")
                cost = player.get("cost", 0)
                if team and cost:
                    team_costs.setdefault(team, []).append(cost)

        return {
            team: sum(costs) / len(costs)
            for team, costs in team_costs.items()
        }