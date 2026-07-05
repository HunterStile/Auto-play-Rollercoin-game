"""
Game modules - each file registers itself with the GameRegistry on import.

Import this package to auto-register all available games:
    import game_engine.games  # triggers all registrations
"""

# Import each game module to trigger @register_game decorators
from game_engine.games import coinclick
from game_engine.games import coinflip
from game_engine.games import coin2048
from game_engine.games import hamsterclimber
from game_engine.games import coinmatch
from game_engine.games import tokenblaster
from game_engine.games import coinfisher
from game_engine.games import flappyrocket
