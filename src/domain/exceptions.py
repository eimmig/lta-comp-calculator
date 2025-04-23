class FantasyAdvisorException(Exception):
    """Base exception for Fantasy Advisor errors"""
    pass

class InvalidBudgetError(FantasyAdvisorException):
    """Raised when budget is invalid"""
    pass

class InvalidTeamCompositionError(FantasyAdvisorException):
    """Raised when team composition is invalid"""
    pass

class OpponentConflictError(FantasyAdvisorException):
    """Raised when there are players from opposing teams in the composition"""
    pass

class PlayerNotFoundError(FantasyAdvisorException):
    """Raised when a player is not found"""
    pass

class InvalidPlayerStatsError(FantasyAdvisorException):
    """Raised when player stats are invalid or missing"""
    pass