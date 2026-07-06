"""
Test diagnostico v2 per CoinMatch — campionamento completo delle celle.

Invece di leggere un pixel al centro, campiona TUTTA la cella,
filtra lo sfondo, e prende il colore dominante della moneta.
"""

import numpy as np
import time
import sys
from collections import Counter

# ── Configurazioni ─────────────────────────────────────────────────
GRID_X = 600
GRID_Y = 250
CELL_SIZE = 50
GRID_SIZE = 8
SAMPLE_MARGIN = 8  # pixel da ignorare ai bordi della cella (evita griglia)

# Colori di sfondo da ignorare (dark blue grid, white empty)
BACKGROUND_COLORS = [
    (0, 20, 60),     # dark blue grid
    (15, 20, 90),    # dark navy
    (250, 250, 255), # white empty
    (0, 5, 10),      # near-black
]


def is_background(r, g, b, tolerance=30):
    """Check if a pixel is background (grid line, empty cell)."""
    brightness = r + g + b
    if brightness < 50:  # near-black
        return True
    if brightness > 700:  # near-white (empty cell)
        return True
    for br, bg, bb in BACKGROUND_COLORS:
        if abs(r - br) + abs(g - bg) + abs(b - bb) <= tolerance:
            return True
    return False


def color_distance(c1, c2):
    return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])


def cluster_colors(pixels, tolerance=40):
    """Group similar colors, return sorted by frequency."""
    if not pixels:
        return []
    clusters = []  # [(representative_color, count)]
    for px in pixels:
        found = False
        for i, (rep, count) in enumerate(clusters):
            if color_distance(px, rep) <= tolerance:
                clusters[i] = (tuple((np.array(rep) * count + np.array(px)) // (count + 1)), count + 1)
                found = True
                break
        if not found:
            clusters.append((px, 1))
    clusters.sort(key=lambda x: -x[1])
    return clusters


def get_cell_dominant_color(screenshot, col, row):
    """
    Extract all non-background pixels from a cell and return the dominant color.
    screenshot: numpy array (H, W, 3) of the game area.
    Returns (r, g, b) or None.
    """
    h, w = screenshot.shape[:2]
    x1 = col * CELL_SIZE + SAMPLE_MARGIN
    y1 = row * CELL_SIZE + SAMPLE_MARGIN
    x2 = min((col + 1) * CELL_SIZE - SAMPLE_MARGIN, w)
    y2 = min((row + 1) * CELL_SIZE - SAMPLE_MARGIN, h)

    if x2 <= x1 or y2 <= y1:
        return None

    cell = screenshot[y1:y2, x1:x2]
    pixels = []
    for py in range(cell.shape[0]):
        for px in range(cell.shape[1]):
            r, g, b = cell[py, px]
            if not is_background(int(r), int(g), int(b)):
                pixels.append((int(r), int(g), int(b)))

    if not pixels:
        return None

    # Get the most common non-background color
    clusters = cluster_colors(pixels)
    return clusters[0][0] if clusters else None


def scan_grid_full():
    """Scan the grid using full-cell sampling."""
    import pyautogui

    print(f"Scansione griglia @ ({GRID_X}, {GRID_Y}) cell={CELL_SIZE}px")
    print(f"Campionamento: margine={SAMPLE_MARGIN}px, ogni cella analizzata completamente")
    print()

    # Screenshot di tutta l'area della griglia
    region = (GRID_X, GRID_Y, CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE)
    print(f"Screenshot area: {region}")

    try:
        pic = pyautogui.screenshot(region=region)
    except Exception as e:
        print(f" ERRORE screenshot: {e}")
        return None, None

    arr = np.array(pic)
    print(f"Dimensione screenshot: {arr.shape}")

    grid_colors = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
    all_dominant = []

    print(f"\n{'Griglia rilevata (colore dominante per cella):':>15}")
    print(f"{'':>12}", end="")
    for col in range(GRID_SIZE):
        print(f"  Col{col}  ", end="")
    print()

    for row in range(GRID_SIZE):
        print(f"Riga {row:2d}:", end=" ")
        for col in range(GRID_SIZE):
            color = get_cell_dominant_color(arr, col, row)
            grid_colors[row][col] = color
            if color:
                r, g, b = color
                print(f"({r:3d},{g:3d},{b:3d})", end=" ")
                all_dominant.append((row, col, color))
            else:
                print(f"  [vuoto]  ", end=" ")
        print()

    return grid_colors, all_dominant


def find_unique_coin_colors(all_dominant):
    """Cluster all dominant colors found to identify unique coin types."""
    if not all_dominant:
        return []

    pixels = [color for _, _, color in all_dominant]
    clusters = cluster_colors(pixels, tolerance=50)

    print(f"\n{'='*60}")
    print("COLORI MONETE RILEVATI (cluster dei colori dominanti)")
    print(f"{'='*60}")

    for i, (color, count) in enumerate(clusters):
        r, g, b = color
        # Trova le posizioni di questo cluster
        positions = []
        for row, col, c in all_dominant:
            if color_distance(c, color) <= 50:
                positions.append((row, col))

        # Suggerisci nome
        if r > 200 and g > 150 and b < 120:
            name = "YELLOW/GOLD"
        elif r > 200 and g > 100 and g < 160:
            name = "ORANGE"
        elif b > 150 and r < 120:
            name = "BLUE"
        elif r < 80 and g < 80 and b > 100:
            name = "PURPLE/ETH"
        elif g > 150 and r < 100 and b < 100:
            name = "GREEN"
        else:
            name = f"COIN_{i+1}"

        print(f"\n  {name}: RGB({r}, {g}, {b})  [{count} celle]")
        pos_str = ", ".join([f"({r},{c})" for r, c in positions[:10]])
        if len(positions) > 10:
            pos_str += f" ... +{len(positions)-10}"
        print(f"    Posizioni: {pos_str}")

    return clusters


def main():
    print("=" * 60)
    print("  TEST DIAGNOSTICO CoinMatch v2 - Full Cell Sampling")
    print("=" * 60)
    print()
    print("Assicurati che CoinMatch sia visibile. Hai 3 secondi...")
    time.sleep(3)

    grid_colors, all_dominant = scan_grid_full()

    if all_dominant is None:
        print("\n❌ Impossibile fare lo screenshot. Il gioco è visibile?")
        return

    if all_dominant:
        clusters = find_unique_coin_colors(all_dominant)
        recognized = len(all_dominant)
        total = GRID_SIZE * GRID_SIZE
        print(f"\n✅ Celle riconosciute: {recognized}/{total} ({recognized*100/total:.0f}%)")
        print(f"   Colori unici trovati: {len(clusters)}")
    else:
        print("\n❌ Nessuna cella riconosciuta!")
        print("   Controlla: GRID_X={}, GRID_Y={}, CELL_SIZE={}".format(GRID_X, GRID_Y, CELL_SIZE))

    print(f"\n{'='*60}")
    print("SUGGERIMENTI PER LA CONFIGURAZIONE")
    print(f"{'='*60}")

    empty_count = sum(1 for row in grid_colors for c in row if c is None) if grid_colors else 0
    if empty_count > 30:
        print(f"\n  ⚠️  {empty_count} celle VUOTE - griglia probabilmente disallineata")
        print(f"  Prova: python3 test_coinmatch.py <X> <Y> <CELL_SIZE>")
        print(f"  Esempio: python3 test_coinmatch.py 580 240 48")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        GRID_X = int(sys.argv[1])
        GRID_Y = int(sys.argv[2])
    if len(sys.argv) >= 4:
        CELL_SIZE = int(sys.argv[3])
    if len(sys.argv) >= 5:
        SAMPLE_MARGIN = int(sys.argv[4])

    main()