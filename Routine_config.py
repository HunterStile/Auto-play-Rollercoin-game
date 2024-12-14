# routine_config.py

class GameRoutineConfig:
    # Posizioni dei giochi
    COINCLICK_POSITION = (1300, 244)
    MEMORY_POSITION = (600, 817)
    GIOCO2048_POSITION = (1300, 655)
    HAMSTERCLIMBER_POSITION = (600,970)
    
    scroll_down = -390
    # Flag per il banner dell'evento
    BANNER_EVENT = True
    
    # Livello per il gioco Memory
    LEVEL_MEMORY = 1

    GAME_ORDER = [
        'hamsterclimber',
        'coinclick',
        '2048',
        'memory'
    ]