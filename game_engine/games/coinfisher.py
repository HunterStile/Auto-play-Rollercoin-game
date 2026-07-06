"""
Coin Fisher Game Bot v2.

Scans for coins using validated color ranges, groups them into clusters,
and shoots at the center of the densest cluster.

Strategy:
1. Scan all pixels for coins (collect all positions)
2. Group nearby coins into clusters (DBSCAN-like)
3. Pick the cluster with the MOST coins
4. Click at the cluster centroid
"""

import pyautogui
import time
import math
from typing import Tuple, List, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

# ── Coin color definitions (validated by user) ────────────────────────
# Each entry: (name, condition_fn) where condition_fn(r, g, b) -> bool

def _is_btc(r, g, b):
    return r > 240 and 130 < g < 170 and b < 50

def _is_doge(r, g, b):
    return r > 220 and g > 190 and 80 < b < 120

def _is_eth(r, g, b):
    return 110 < r < 150 and 130 < g < 180 and b > 240

def _is_ltc(r, g, b):
    return r > 210 and g > 210 and b > 210 and abs(r - b) < 5

def _is_dash(r, g, b):
    return r < 50 and 100 < g < 150 and 190 < b < 230

COIN_CHECKS = [_is_btc, _is_doge, _is_eth, _is_ltc, _is_dash]

# End-screen detection
END_SCREEN_COLOR = (3, 225, 228)

# Default game region (user-validated)
DEFAULT_REGION = (64, 117, 1475, 896)

# Cluster distance: coins within this many pixels are grouped together
CLUSTER_DISTANCE = 80


@register_game
class CoinFisherBot(BaseGame):
    game_id = 'coinfisher'
    display_name = 'Coin Fisher'
    description = 'Fishing game: cluster detection, shoots densest coin groups'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = 65  # seconds
        self.click_cooldown = 1.0  # seconds between harpoon shots
        self.scan_step = 6  # pixel step for scanning
        self.region = config.get('scan_region', DEFAULT_REGION) if config else DEFAULT_REGION

    # ── Coin detection ────────────────────────────────────────────────

    @staticmethod
    def _is_coin(r: int, g: int, b: int) -> bool:
        """Check if a pixel is any coin type."""
        return any(check(r, g, b) for check in COIN_CHECKS)

    def _scan_all_coins(self) -> List[Tuple[int, int]]:
        """
        Scan the entire game region for all coins.
        Returns list of (x, y) absolute screen positions.
        """
        rx, ry, rw, rh = self.region
        coins = []

        try:
            pic = pyautogui.screenshot(region=self.region)
            w, h = pic.size

            for x in range(0, w, self.scan_step):
                for y in range(0, h, self.scan_step):
                    try:
                        r, g, b = pic.getpixel((x, y))
                        if self._is_coin(r, g, b):
                            coins.append((rx + x, ry + y))
                    except Exception:
                        pass
        except Exception as e:
            print(f"  Scan error: {e}")

        return coins

    # ── Clustering ────────────────────────────────────────────────────

    def _cluster_coins(self, coins: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        """
        Group nearby coins into clusters using distance-based approach.
        Returns list of clusters, each cluster is a list of (x, y) positions.
        """
        if not coins:
            return []

        # Simple distance-based clustering
        clusters = []
        remaining = coins.copy()

        while remaining:
            # Start a new cluster with the first remaining coin
            cluster = [remaining.pop(0)]
            changed = True

            # Expand: add any coin within CLUSTER_DISTANCE of any cluster member
            while changed:
                changed = False
                i = 0
                while i < len(remaining):
                    coin = remaining[i]
                    # Check if this coin is close to any coin in the cluster
                    if any(self._distance(coin, c) <= CLUSTER_DISTANCE for c in cluster):
                        cluster.append(remaining.pop(i))
                        changed = True
                    else:
                        i += 1

            clusters.append(cluster)

        return clusters

    @staticmethod
    def _distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    @staticmethod
    def _cluster_centroid(cluster: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Calculate the center point of a cluster."""
        avg_x = sum(c[0] for c in cluster) / len(cluster)
        avg_y = sum(c[1] for c in cluster) / len(cluster)
        return (int(avg_x), int(avg_y))

    # ── Best shot selection ───────────────────────────────────────────

    def _find_best_shot(self) -> Optional[Tuple[int, int]]:
        """
        Find the best position to click:
        1. Scan all coins
        2. Group into clusters
        3. Pick the biggest cluster
        4. Return its centroid
        """
        coins = self._scan_all_coins()

        if not coins:
            # No coins visible - aim at center of game area
            rx, ry, rw, rh = self.region
            return (rx + rw // 2, ry + rh // 3)

        total_coins = len(coins)
        print(f"  Found {total_coins} coin pixels")

        # Cluster coins
        clusters = self._cluster_coins(coins)
        print(f"  Grouped into {len(clusters)} clusters")

        # Pick the biggest cluster
        best_cluster = max(clusters, key=len)
        centroid = self._cluster_centroid(best_cluster)

        # Show cluster stats
        sizes = sorted([len(c) for c in clusters], reverse=True)
        print(f"  Cluster sizes: {sizes[:5]}{'...' if len(sizes) > 5 else ''}")
        print(f"  → Shooting biggest cluster ({len(best_cluster)} coins) at {centroid}")

        return centroid

    # ── End screen detection ──────────────────────────────────────────

    def _is_end_screen(self) -> bool:
        """Check if the game has ended (cyan end screen)."""
        rx, ry, rw, rh = self.region
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 80),
        ]
        for px, py in check_points:
            try:
                r, g, b = pyautogui.pixel(px, py)
                if (abs(r - END_SCREEN_COLOR[0]) <= 5 and
                    abs(g - END_SCREEN_COLOR[1]) <= 5 and
                    abs(b - END_SCREEN_COLOR[2]) <= 5):
                    return True
            except Exception:
                pass
        return False

    # ── Main play loop ────────────────────────────────────────────────

    def play(self) -> bool:
        """Play one round of Coin Fisher."""
        print("START Coin Fisher v2 (Cluster Mode)")
        start_time = time.time()
        last_click = 0

        try:
            while time.time() - start_time < self.game_duration:
                if self._is_end_screen():
                    print("  End screen detected - game complete!")
                    break

                now = time.time()
                if now - last_click > self.click_cooldown:
                    target = self._find_best_shot()
                    if target:
                        pyautogui.click(target[0], target[1])
                        last_click = now

                time.sleep(0.25)

            print("END Coin Fisher v2")
            return True

        except Exception as e:
            print(f"  Error in Coin Fisher: {e}")
            return False