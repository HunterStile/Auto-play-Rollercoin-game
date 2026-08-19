"""
Game Orchestrator - runs mini-games in configured order.

Replaces the monolithic Routine.py with a modular,
registry-driven game runner.
"""

import pyautogui
from time import sleep
from typing import List, Optional, Dict, Any

from game_engine.registry import GameRegistry
from game_engine.utils import wait_game_ready, click
from game_engine.base import BaseGame

# Import all games to ensure they're registered
import game_engine.games  # noqa: F401


class GameOrchestrator:
    """
    Manages the game automation loop.

    Loads config, discovers available games via the registry,
    and runs them in the configured order.
    """

    def __init__(self, config):
        """
        Args:
            config: GameRoutineConfig module or dict with configuration.
        """
        self.config = config
        self._extract_config()

    def _extract_config(self):
        """Extract values from config (supports both module and dict)."""
        cfg = self.config

        def get(key, default=None):
            if hasattr(cfg, key):
                return getattr(cfg, key)
            return cfg.get(key, default) if isinstance(cfg, dict) else default

        # General settings
        self.gain_power_position = get('GAIN_POWER_POSITION', (967, 645))
        self.scroll_down = get('scroll_down', -390)
        self.banner_event = get('BANNER_EVENT', True)

        # Game order
        self.game_order = get('GAME_ORDER', [])

        # Elections
        self.elezioni_enabled = get('ELEZIONI_ENABLED', False)
        self.elezioni_base_minutes = get('ELEZIONI_INTERVAL_MINUTES', 60)

    def _get_game_config(self, game_id: str) -> dict:
        """Extract config values for a specific game using its declared config_keys."""
        cfg = self.config
        game_cls = GameRegistry.get(game_id)

        def get(key, default=None):
            if hasattr(cfg, key):
                return getattr(cfg, key)
            return cfg.get(key, default) if isinstance(cfg, dict) else default

        # Get config key names from the game class
        if game_cls:
            key_map = game_cls.get_required_config_keys()
        else:
            gid_upper = game_id.upper()
            key_map = {
                'position': f'{gid_upper}_POSITION',
                'start_position': f'{gid_upper}_START',
            }

        return {
            'position': get(key_map.get('position', '')),
            'start_position': get(key_map.get('start_position', '')),
            'gain_power_position': self.gain_power_position,
            'difficulty': get('LEVEL_MEMORY', 2) if game_id == 'coinflip' else 1,
        }

    def _run_single_game(self, game_id: str) -> bool:
        """Run one game round. Returns True if successful."""
        print(f"\n{'='*50}")
        print(f"Running game: {game_id}")
        print(f"{'='*50}")

        game_cls = GameRegistry.get(game_id)
        if not game_cls:
            print(f"!! Game '{game_id}' not found in registry!")
            return False

        config = self._get_game_config(game_id)
        game = game_cls(config)

        # Step 1: Click game icon and wait for it to load
        position = config.get('position')
        if not position:
            print(f"!! No position configured for {game_id}")
            return False

        if not wait_game_ready(position):
            print(f"X Game {game_id} failed to load")
            return False

        # Step 2: Click start button
        start_pos = config.get('start_position')
        if start_pos:
            sleep(1)
            click(*start_pos)
            sleep(3)

        # Step 3: Play the game
        success = game.play()
        sleep(2)

        # Step 4: Collect power
        gp = self.gain_power_position
        if gp:
            sleep(2)
            click(*gp)
            sleep(2)

        # Step 5: Refresh page
        pyautogui.press('f5')
        sleep(15)
        pyautogui.scroll(500)
        if self.banner_event:
            pyautogui.scroll(self.scroll_down)

        return success

    def run_elections(self):
        """Run elections mode (infinite loop)."""
        from Elezioni import ElezioniBot

        cfg = self.config

        def get(key, default=None):
            if hasattr(cfg, key):
                return getattr(cfg, key)
            return cfg.get(key, default) if isinstance(cfg, dict) else default

        elezioni_bot = ElezioniBot(
            voto1_position=get('ELEZIONI_VOTO1_POSITION', (446, 724)),
            voto2_position=get('ELEZIONI_VOTO2_POSITION', (1358, 720)),
            scroll_value=get('ELEZIONI_SCROLL', 500),
            wait_time=get('ELEZIONI_WAIT_TIME', 5),
        )

        iteration = 0
        while True:
            iteration += 1
            print(f"\n=== Elections iteration {iteration} ===")

            pyautogui.press('f5')
            sleep(5)

            elezioni_bot.run_election_cycle()

            wait_minutes = self.elezioni_base_minutes + (iteration * 2)
            wait_seconds = wait_minutes * 60
            print(f"Next elections in {wait_minutes} minutes")
            sleep(wait_seconds)

    def run_games(self):
        """Run games in configured order (infinite loop)."""
        print(f"Game order: {self.game_order}")
        print(f"Available games: {GameRegistry.list_game_ids()}")

        # Validate game order
        valid_order = [g for g in self.game_order if GameRegistry.get(g)]
        if not valid_order:
            print("!! No valid games configured!")
            return

        print(f"Running games: {valid_order}")

        while True:
            played_any = False
            for game_id in valid_order:
                if self._run_single_game(game_id):
                    played_any = True
                else:
                    print(f"! {game_id} not available, skipping to next game...")
            if not played_any:
                print("No games available. Waiting and retrying...")
                sleep(30)

    def run(self):
        """Main entry point: runs elections or games based on config."""
        print("=" * 60)
        print("  RollerCoin Auto-Play Bot - Game Orchestrator")
        print("=" * 60)

        # Initial click to focus page
        click(800, 150)
        sleep(1)

        if self.elezioni_enabled:
            print("Mode: ELECTIONS (no games)")
            self.run_elections()
        else:
            print("Mode: GAMES")
            pyautogui.scroll(500)
            if self.banner_event:
                pyautogui.scroll(self.scroll_down)
            self.run_games()


# -- Entry point ------------------------------------------------------------

if __name__ == "__main__":
    from Routine_config import GameRoutineConfig
    orchestrator = GameOrchestrator(GameRoutineConfig)
    orchestrator.run()
