import requests
from typing import Dict, Optional
from src.domain.exceptions import FantasyAdvisorException

class StatsAPI:
    def __init__(self, base_url: str = "https://api.ltafantasy.com"):
        self.base_url = base_url.rstrip('/')

    def fetch_player_stats(self) -> Dict:
        """Fetch player statistics from the API"""
        try:
            response = requests.get(f"{self.base_url}/player-stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FantasyAdvisorException(f"Error fetching player stats: {str(e)}")

    def get_player_stats(self, player_name: str, stats_data: Dict) -> Optional[Dict]:
        """Get stats for a specific player from stats data"""
        if not stats_data or "data" not in stats_data or "players" not in stats_data["data"]:
            return None
            
        return next(
            (player for player in stats_data["data"]["players"]
             if player["playerName"].strip().lower() == player_name.strip().lower()),
            None
        )