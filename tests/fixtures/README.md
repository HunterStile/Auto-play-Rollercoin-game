`coinfisher.png` is the game-only crop of the screenshot supplied on 2026-09-10.
It contains 28 visible coins; account details and surrounding browser UI are excluded.

Run the offline regression checks from the repository root:

```powershell
python -m unittest discover -s tests -p test_coinfisher_vision.py
```

The tests replay the board at different positions and scales, and mock all mouse
input. They verify detection and click bounds, not live projectile physics or wins.

For a manual round, start Coin Fisher and run `python test_coinfisher.py`, then
focus the game during the four-second countdown. Keep the entire game visible.
The bot detects the water automatically; an optional `scan_region` is now only
a search hint in `(left, top, width, height)` screen coordinates. A missing,
clipped or ambiguous board suppresses shots. Screenshot/mouse scale mismatches
stop the run. Move the mouse to the top-left corner to trigger PyAutoGUI failsafe.
The end-panel color check is heuristic; it does not certify a win or level 10.


`coinmatch_level1.png` is the game-only screenshot supplied on 2026-09-10.
Its 64 cells are transcribed independently in `tests/test_coinmatch.py`.
Tests cover 70%, 100%, 120% scale, translations, missing/unknown/moving coins,
ambiguous boards, legal swaps, unique match counting and mocked input feedback.

```powershell
python -m unittest discover -s tests -v
python test_coinmatch.py --image tests/fixtures/coinmatch_level1.png
```

The second command only prints the detected board and suggested swap; no clicks.


Coin Flip fixtures are rack-only crops of the user's screenshots from 2026-09-10;
the wallet/browser area is excluded:

- `coinflip_covered.png`: 09:37:22, twelve covered cards.
- `coinflip_pair.png`: 09:37:32, Monero exposed at (row 2, col 1) and (row 3, col 2).
- `coinflip_mixed.png`: 09:37:42, those two slots empty, RollerCoin and Binance
  exposed at (row 2, col 2) and (row 2, col 3).

`tests/test_coinflip.py` tests image replay at 70%, 100% and 120%, rejects absent,
clipped and ambiguous racks, and exercises memory and input with no real clicks.
Larger 16/20-card racks are constructed from the supplied back sprites: these
verify geometry only and are not evidence of the real higher-level appearance.

```powershell
python test_coinflip.py --image tests/fixtures/coinflip_mixed.png
python -m unittest discover -s tests -v
```
