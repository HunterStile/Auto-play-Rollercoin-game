"""
Routine.py - Main entry point for RollerCoin automation.

Uses the new game_engine.orchestrator for modular game execution.
Backward-compatible with existing Routine_config.py.
"""

from game_engine.orchestrator import GameOrchestrator
from Routine_config import GameRoutineConfig

if __name__ == "__main__":
    orchestrator = GameOrchestrator(GameRoutineConfig)
    orchestrator.run()
