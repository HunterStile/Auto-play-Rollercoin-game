#!/usr/bin/env python3
"""
Test standalone: Flappy Rocket scanner debug.

1. Screenshot della regione di gioco
2. Scansione colonna di ostacoli con debug pixel-per-pixel
3. Output: mappa ASCII della colonna + immagine annotata
"""

import pyautogui
import time
import sys
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont

# ── Config (stessa del bot originale) ──────────────────────────────────
DEFAULT_REGION = (400, 100, 800, 700)

OBSTACLE_COLORS = [
    (50, 180, 50),    # green
    (30, 150, 30),    # dark green
    (80, 80, 80),     # grey
    (40, 40, 40),     # dark grey
]

BACKGROUND_COLOR = (20, 20, 40)
END_SCREEN_COLOR = (3, 225, 228)
COLOR_TOLERANCE = 30

SCAN_AHEAD_X = 120
SCAN_WIDTH = 10


# ── Utility ────────────────────────────────────────────────────────────
def color_match(target: Tuple[int, int, int], actual: Tuple[int, int, int],
                tolerance: int = COLOR_TOLERANCE) -> bool:
    return all(abs(t - a) <= tolerance for t, a in zip(target, actual))


def classify_pixel(r: int, g: int, b: int) -> str:
    """Classifica un pixel: ostacolo, sfondo, brillante, o sconosciuto."""
    brightness = r + g + b

    # Sfondo scuro
    if color_match(BACKGROUND_COLOR, (r, g, b), tolerance=40):
        return "BG"

    # Molto brillante (monete/items, non ostacoli)
    if r > 200 and g > 200 and b > 200:
        return "BRI"

    # Colori ostacolo noti
    for color in OBSTACLE_COLORS:
        if color_match(color, (r, g, b)):
            return "OBS"

    # Pixel non-sfondo, non-brillante → probabile ostacolo
    if brightness > 100 and brightness < 520:
        return "OBS?"

    return "???"


def scan_column(pic: Image.Image, height: int, step: int = 3) -> List[dict]:
    """
    Scansiona la colonna di pixel (larghezza SCAN_WIDTH).
    Ritorna lista di {y, obs_count, total, classification}.
    """
    results = []
    for y in range(0, height, step):
        obs_count = 0
        total = 0
        classifications = []
        for x in range(0, SCAN_WIDTH, 2):
            try:
                r, g, b = pic.getpixel((x, y))
                label = classify_pixel(r, g, b)
                classifications.append(label)
                total += 1
                if label.startswith("OBS"):
                    obs_count += 1
            except Exception:
                pass
        results.append({
            'y': y,
            'obs_count': obs_count,
            'total': total,
            'is_obstacle': obs_count >= 3,
            'labels': classifications,
        })
    return results


def find_gaps(scan_results: List[dict], height: int, step: int) -> List[dict]:
    """
    Trova i gap (transizioni ostacolo → non-ostacolo).
    Ritorna lista di {gap_top_y}.
    """
    gaps = []
    in_obstacle = False
    for i, row in enumerate(scan_results):
        is_obs = row['is_obstacle']
        if is_obs and not in_obstacle:
            in_obstacle = True
        elif not is_obs and in_obstacle:
            gap_y = row['y']
            gaps.append({'gap_top_y': gap_y, 'row_index': i})
            in_obstacle = False
    return gaps


# ── Main ───────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("FLAPPY ROCKET - Scanner Debug Test")
    print("=" * 70)

    # Usa regione da linea di comando o default
    if len(sys.argv) >= 5:
        region = (int(sys.argv[1]), int(sys.argv[2]),
                  int(sys.argv[3]), int(sys.argv[4]))
    else:
        region = DEFAULT_REGION

    rx, ry, rw, rh = region
    print(f"Regione: x={rx} y={ry} w={rw} h={rh}")

    # Posizione della colonna di scan
    scan_x = rx + rw // 2 + SCAN_AHEAD_X
    if scan_x >= rx + rw - 10:
        scan_x = rx + rw - 30

    scan_y_start = ry + 20
    scan_y_end = ry + rh - 20
    scan_height = scan_y_end - scan_y_start

    print(f"Colonna scan: x={scan_x} y={scan_y_start}-{scan_y_end} (altezza={scan_height})")
    print(f"Offset avanti: {SCAN_AHEAD_X}px")
    print()

    # Fai screenshot della colonna
    print("📸 Catturo screenshot della colonna di scan...")
    screenshot_region = (scan_x - SCAN_WIDTH // 2, scan_y_start,
                         SCAN_WIDTH, scan_height)
    try:
        pic = pyautogui.screenshot(region=screenshot_region)
        print(f"   Screenshot catturato: {pic.size[0]}x{pic.size[1]}px")
    except Exception as e:
        print(f"   ❌ ERRORE screenshot: {e}")
        return False

    # Salva screenshot raw
    pic.save("/tmp/flappy_scan_column.png")
    print(f"   Salvato: /tmp/flappy_scan_column.png")

    # Scansiona
    STEP = 3
    print(f"\n🔍 Scansione pixel (step={STEP}px)...")
    results = scan_column(pic, scan_height, STEP)

    # Statistiche
    total_rows = len(results)
    obs_rows = sum(1 for r in results if r['is_obstacle'])
    bg_rows = total_rows - obs_rows
    print(f"   Righe scansionate: {total_rows}")
    print(f"   Righe con ostacolo: {obs_rows} ({obs_rows*100//max(1,total_rows)}%)")
    print(f"   Righe libere:       {bg_rows} ({bg_rows*100//max(1,total_rows)}%)")

    # Trova gap
    gaps = find_gaps(results, scan_height, STEP)
    print(f"\n🎯 Gap trovati: {len(gaps)}")
    for g in gaps:
        actual_y = scan_y_start + g['gap_top_y']
        print(f"   Gap a y={actual_y} (relativo +{g['gap_top_y']}px)")

    if len(gaps) == 0:
        print("\n   ⚠️  NESSUN GAP RILEVATO!")
        print("   Il bot NON salterà mai perché non vede ostacoli → gap.")

    # ── Mappa ASCII ──────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("MAPPA ASCII DELLA COLONNA DI SCAN (█=ostacolo, ·=libero)")
    print("─" * 70)
    for row in results:
        y_actual = scan_y_start + row['y']
        bar = "█" if row['is_obstacle'] else "·"
        labels = " ".join(row['labels'][:5])
        marker = ""
        for g in gaps:
            if g['gap_top_y'] == row['y']:
                marker = " ← GAP!"
                break
        print(f"  y={y_actual:4d} [{bar}] {labels:20s}{marker}")
    print("─" * 70)

    # ── Mappa a colori (ANSI) ────────────────────────────────────────
    print("\nMAPPA A COLORI (🟢=ostacolo, ⬛=sfondo, ⭐=brillante, ❓=altro)")
    print("─" * 70)
    for row in results:
        y_actual = scan_y_start + row['y']
        if row['is_obstacle']:
            symbol = "\033[31m█\033[0m"  # rosso
        else:
            # Controlla il primo label
            first = row['labels'][0] if row['labels'] else "???"
            if first == "BG":
                symbol = "\033[34m·\033[0m"  # blu
            elif first == "BRI":
                symbol = "\033[33m★\033[0m"  # giallo
            else:
                symbol = "\033[32m·\033[0m"  # verde
        print(f"  y={y_actual:4d} {symbol}", end="")
        for g in gaps:
            if g['gap_top_y'] == row['y']:
                print(" \033[1;33m← GAP!\033[0m", end="")
        print()
    print("─" * 70)

    # ── Crea immagine annotata ───────────────────────────────────────
    print("\n🖼️  Creo immagine annotata...")
    try:
        # Cattura area di gioco intera per contesto
        full_pic = pyautogui.screenshot(region=region)
    except Exception:
        full_pic = None

    if full_pic:
        draw = ImageDraw.Draw(full_pic)

        # Disegna la zona di scan
        draw.rectangle(
            [scan_x - SCAN_WIDTH // 2 - rx, scan_y_start - ry,
             scan_x + SCAN_WIDTH // 2 - rx, scan_y_end - ry],
            outline="yellow", width=2
        )

        # Disegna i gap
        for g in gaps:
            gap_abs_y = scan_y_start + g['gap_top_y']
            draw.line(
                [(scan_x - SCAN_WIDTH // 2 - rx, gap_abs_y - ry),
                 (scan_x + SCAN_WIDTH // 2 - rx, gap_abs_y - ry)],
                fill="lime", width=2
            )
            draw.text(
                (scan_x + SCAN_WIDTH // 2 + 5 - rx, gap_abs_y - ry - 8),
                f"GAP {gap_abs_y}", fill="lime"
            )

        # Info overlay
        draw.text((10, 10), f"Gaps: {len(gaps)} | Obs: {obs_rows}/{total_rows}",
                  fill="yellow")

        full_pic.save("/tmp/flappy_full_annotated.png")
        print(f"   Salvato: /tmp/flappy_full_annotated.png")

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("DIAGNOSI FINALE")
    print("=" * 70)

    if len(gaps) == 0:
        if obs_rows == 0:
            print("❌ PROBLEMA: Nessun pixel rilevato come ostacolo.")
            print("   Possibili cause:")
            print("   1. La regione di scan è sbagliata (non copre il gioco)")
            print("   2. I colori degli ostacoli non corrispondono a quelli nel codice")
            print("   3. La tolleranza colore (30) è troppo restrittiva")
            print("   4. Il gioco non è nella schermata attiva")
            print()
            print("   💡 Suggerimento: guarda /tmp/flappy_scan_column.png")
            print("      e verifica che la colonna catturata sia dentro l'area di gioco.")
        elif obs_rows == total_rows:
            print("❌ PROBLEMA: TUTTI i pixel sono rilevati come ostacolo.")
            print("   Lo sfondo è troppo chiaro? La regione è su una pagina bianca?")
        else:
            print("❌ PROBLEMA: Ci sono ostacoli ma nessun gap rilevato.")
            print("   Significa che la scansione vede solo ostacoli continui senza interruzioni.")
            print("   Possibile: gli ostacoli sono troppo vicini, o la tolleranza è troppo ampia.")
    else:
        print(f"✅ OK: {len(gaps)} gap rilevati. Il bot dovrebbe saltare.")
        print()
        for g in gaps:
            gap_abs_y = scan_y_start + g['gap_top_y']
            print(f"   Salto triggerato a y={gap_abs_y}")

    print()
    print("File generati:")
    print("  /tmp/flappy_scan_column.png   → colonna di scan raw")
    print("  /tmp/flappy_full_annotated.png → area gioco con annotazioni")
    print()
    return len(gaps) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
