"""
Test diagnostico per CoinMatch.

1. Cattura lo screen dell'area di gioco
2. Scansiona la griglia 8x8
3. Mostra i colori trovati e la griglia rilevata
4. Aiuta a calibrare posizione griglia e colori monete
"""

import pyautogui
import numpy as np
import time
import sys
from PIL import Image
from collections import Counter

# ── Configurazioni da testare ──────────────────────────────────────
GRID_X = 600       # X dell'angolo in alto a sinistra della griglia
GRID_Y = 250       # Y dell'angolo in alto a sinistra della griglia
CELL_SIZE = 50     # Dimensione cella in pixel
GRID_SIZE = 8
COLOR_TOLERANCE = 25

# Colori hardcoded (R, G, B) da provare
# ETH = blu/viola, BLUE = azzurro, YELLOW = giallo, ORANGE = arancione
COIN_COLORS_RGB = {
    'ETH':    (66, 60, 207),
    'BLUE':   (0, 120, 184),
    'YELLOW': (200, 180, 64),
    'ORANGE': (231, 120, 32),
    'GREEN':  (50, 180, 80),    # possibile colore extra
    'RED':    (220, 50, 50),     # possibile colore extra
}


def get_pixel_color(x, y):
    """Legge il colore esatto di un pixel."""
    try:
        r, g, b = pyautogui.pixel(x, y)
        return (r, g, b)
    except Exception as e:
        return None


def get_avg_color(x, y, radius=5):
    """Media del colore in un'area attorno al punto."""
    try:
        region = (x - radius, y - radius, x + radius + 1, y + radius + 1)
        pic = pyautogui.screenshot(region=region)
        arr = np.array(pic)
        avg = tuple(np.mean(arr, axis=(0, 1)).astype(int))
        return avg
    except Exception:
        return None


def guess_coin_type(rgb, tolerance=COLOR_TOLERANCE):
    """Indovina il tipo di moneta dal colore RGB."""
    r, g, b = rgb
    best = None
    best_dist = float('inf')
    for name, (tr, tg, tb) in COIN_COLORS_RGB.items():
        dist = abs(r - tr) + abs(g - tg) + abs(b - tb)
        if dist < best_dist:
            best_dist = dist
            best = name
    if best_dist <= tolerance * 3:
        return best, best_dist
    return None, best_dist


def scan_grid(grid_x, grid_y, cell_size, grid_size=8):
    """Scansiona la griglia e mostra il tipo di ogni cella."""
    print(f"\n{'='*70}")
    print(f"SCANSIONE GRIGLIA @ ({grid_x}, {grid_y}) cell={cell_size}px")
    print(f"{'='*70}")
    print(f"\n{'Colori per cella (centro esatto):':>10}")
    print(f"{'':>10}", end="")
    for col in range(grid_size):
        print(f"  Col{col:2d}  ", end="")
    print()

    grid = [[None] * grid_size for _ in range(grid_size)]
    all_colors = []

    for row in range(grid_size):
        print(f"Riga {row:2d}:", end="")
        for col in range(grid_size):
            x = grid_x + col * cell_size + cell_size // 2
            y = grid_y + row * cell_size + cell_size // 2
            color = get_pixel_color(x, y)
            all_colors.append((row, col, color))
            coin, dist = guess_coin_type(color) if color else (None, float('inf'))
            grid[row][col] = coin

            if coin:
                print(f" {coin:>6s}  ", end="")
            else:
                r, g, b = color if color else (0, 0, 0)
                print(f" ({r:3d},{g:3d},{b:3d})", end="")
        print()

    return grid, all_colors


def find_unique_colors(all_colors, tolerance=30):
    """Raggruppa i colori simili per trovare i colori unici delle monete."""
    clusters = []

    for row, col, color in all_colors:
        if color is None:
            continue
        r, g, b = color
        found = False
        for cluster_colors, positions in clusters:
            cr, cg, cb = cluster_colors[0]  # rappresentante
            if abs(r - cr) + abs(g - cg) + abs(b - cb) <= tolerance:
                cluster_colors.append(color)
                positions.append((row, col))
                found = True
                break
        if not found:
            clusters.append(([color], [(row, col)]))

    print(f"\n{'='*70}")
    print("COLORI UNICI TROVATI (cluster con tolleranza {tolerance})")
    print(f"{'='*70}")
    for i, (colors, positions) in enumerate(clusters):
        avg_r = int(np.mean([c[0] for c in colors]))
        avg_g = int(np.mean([c[1] for c in colors]))
        avg_b = int(np.mean([c[2] for c in colors]))
        print(f"\n  Cluster {i+1}: ({avg_r}, {avg_g}, {avg_b})  [{len(colors)} celle]")
        pos_str = ", ".join([f"({r},{c})" for r, c in positions[:8]])
        if len(positions) > 8:
            pos_str += f" ... +{len(positions)-8}"
        print(f"    Posizioni: {pos_str}")

    return clusters


def check_grid_alignment(grid_x, grid_y, cell_size, grid_size=8):
    """Verifica se la griglia è allineata correttamente controllando i bordi."""
    print(f"\n{'='*70}")
    print("VERIFICA ALLINEAMENTO GRIGLIA")
    print(f"{'='*70}")

    # Controlla i pixel tra le celle (dovrebbero essere sfondo scuro)
    issues = 0
    for row in range(grid_size):
        for col in range(grid_size - 1):
            # Punto tra cella col e col+1
            x = grid_x + (col + 1) * cell_size
            y = grid_y + row * cell_size + cell_size // 2
            color = get_pixel_color(x, y)
            if color:
                brightness = sum(color)
                if brightness > 150:  # troppo chiaro = probabilmente dentro una cella
                    issues += 1

    if issues > 5:
        print(f"  ⚠️  {issues} punti tra le celle sono chiari - la griglia potrebbe essere disallineata!")
        print(f"  Suggerimento: regola GRID_X, GRID_Y o CELL_SIZE")
    else:
        print(f"  ✅ Solo {issues} punti sospetti - griglia probabilmente allineata")


def main():
    print("=" * 70)
    print("  TEST DIAGNOSTICO CoinMatch")
    print("=" * 70)
    print()
    print("Assicurati che il gioco CoinMatch sia visibile sullo schermo!")
    print("Hai 3 secondi per prepararti...")
    time.sleep(3)

    # 1. Scansiona la griglia
    grid, all_colors = scan_grid(GRID_X, GRID_Y, CELL_SIZE, GRID_SIZE)

    # 2. Trova colori unici
    clusters = find_unique_colors(all_colors)

    # 3. Verifica allineamento
    check_grid_alignment(GRID_X, GRID_Y, CELL_SIZE, GRID_SIZE)

    # 4. Suggerimenti
    print(f"\n{'='*70}")
    print("SUGGERIMENTI")
    print(f"{'='*70}")
    print()

    non_null = sum(1 for row in grid for cell in row if cell is not None)
    total = GRID_SIZE * GRID_SIZE
    print(f"  Celle riconosciute: {non_null}/{total} ({non_null*100/total:.0f}%)")

    if non_null < total * 0.5:
        print("  ⚠️  Meno del 50% delle celle riconosciute!")
        print("  Possibili cause:")
        print("    1. GRID_X/GRID_Y sbagliati (la griglia è spostata)")
        print("    2. CELL_SIZE sbagliato (le celle sono più grandi/piccole)")
        print("    3. I colori hardcoded non corrispondono a quelli reali")
        print()
        print("  Per risolvere:")
        print("    - Aggiungi GRID_X e GRID_Y come parametri: python test_coinmatch.py <X> <Y>")
        print("    - Modifica COIN_COLORS_RGB nel file con i colori reali del gioco")

    # Mostra colori per la calibrazione
    print()
    print("  Colori reali rilevati (da copiare in COIN_COLORS_RGB):")
    for i, (colors, positions) in enumerate(clusters[:6]):
        avg_r = int(np.mean([c[0] for c in colors]))
        avg_g = int(np.mean([c[1] for c in colors]))
        avg_b = int(np.mean([c[2] for c in colors]))
        count = len(colors)
        # Suggerisci un nome
        if avg_r > 200 and avg_g > 150:
            name = "YELLOW"
        elif avg_r > 200 and avg_g < 100:
            name = "ORANGE"
        elif avg_b > 180:
            name = "BLUE"
        elif avg_r < 100 and avg_b > 150:
            name = "ETH"
        else:
            name = f"COIN_{i+1}"
        print(f"    '{name}': ({avg_r}, {avg_g}, {avg_b}),  # {count} celle")


if __name__ == "__main__":
    # Supporta parametri da CLI: python test_coinmatch.py <GRID_X> <GRID_Y> [CELL_SIZE]
    if len(sys.argv) >= 3:
        GRID_X = int(sys.argv[1])
        GRID_Y = int(sys.argv[2])
    if len(sys.argv) >= 4:
        CELL_SIZE = int(sys.argv[3])

    main()