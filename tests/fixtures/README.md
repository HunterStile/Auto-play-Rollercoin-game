`coinfisher.png` is the game-only crop of the screenshot supplied on 2026-09-10.
It contains 28 visible coins; account details and surrounding browser UI are excluded.

`coin2048_playing.png` and `coin2048_result.png` come from the 2026-09-11
19:58:32 and 19:59:56 screenshots. The latter is cropped around the win dialog.
Tests check recognition across scales and translations, cyan gameplay rejection,
missing text/panel rejection, ambiguous dialogs, score independence, keyboard
pattern preservation, stable confirmation and a real-time deadline. All input
is mocked. Only the supplied result layout is verified, not unseen loss screens.
The detector embeds a packed mask of the button lettering derived from this
fixture, so executable builds require no extra image data files.

```powershell
python -m unittest discover -s tests -p test_coin2048.py
python test_coin2048.py --image tests/fixtures/coin2048_result.png
```

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

`coinmatch_monero.png` is the game-only screenshot supplied on 2026-09-11.
Its 64 cells, including 13 Monero coins, are independently transcribed in
`tests/test_coinmatch.py`. Replay tests check all cells and coordinates at 70%,
100% and 120% scale, valid move selection, and rejection of incomplete Monero
sprites. These checks do not verify live animation timing or wins.

`coinmatch_blue_gray.png` is the game-only screenshot supplied on 2026-09-11
at 19:45:18, with nine blue/gray coins. `BLUE_GRAY` is a visual identifier;
the currency name has not been verified. Tests independently transcribe all
64 cells, check coordinates and legal moves at 70%, 100% and 120% scale, and
reject incomplete blue/gray coins. The blue symbol and pale body must be
combined to detect geometry, with a narrow blue tolerance to preserve DASH.

`coinmatch_yellow_symbol.png` is the final-level screenshot supplied on
2026-09-11 at 22:10:18. All 64 cells are independently transcribed, including
seven bright-yellow coins (`YELLOW_SYMBOL`, a visual identifier). Tests cover
70%, 100% and 120% scale, coordinates, legal moves and missing/unknown cells.
The yellow rim can vote for XMR; small blue/gray coins also need tolerance for
their DASH-colored outline. Earlier screenshots remain regression coverage.


Coin Flip fixtures are rack-only crops of the user's screenshots from 2026-09-10;
the wallet/browser area is excluded:

- `coinflip_covered.png`: 09:37:22, twelve covered cards.
- `coinflip_pair.png`: 09:37:32, Monero exposed at (row 2, col 1) and (row 3, col 2).
- `coinflip_mixed.png`: 09:37:42, those two slots empty, RollerCoin and Binance
  exposed at (row 2, col 2) and (row 2, col 3).

`tests/test_coinflip.py` tests image replay at 70%, 100% and 120%, rejects absent,
clipped and ambiguous racks, and exercises memory and input with no real clicks.
Synthetic 16/20-card racks are also constructed from the supplied back sprites
to verify geometry.

`coinflip_4x4.png` and `coinflip_monochrome.png` are rack-only crops of the
2026-09-11 screenshots (14:02:26 and 14:05:52). They verify 14 covered cards
with two empty slots, and 15 covered cards with one black-and-white face,
respectively. Tests replay both at 70%, 100% and 120% scale, check that stable
reads authorize a covered-card click, and verify that the monochrome face is
remembered. Mouse input is mocked; live animation timing is not verified.

`coinflip_litecoin_193834.png` and `coinflip_litecoin_193844.png` are rack-only
crops of the 2026-09-11 screenshots at the named times. Both have 20 slots and
four empty cells. Litecoin at (row 4, column 2) is exposed in both; Bitcoin at
(row 3, column 5) is also exposed in the second. A regression replays both at
70%, 100% and 120%, then simulates their closing with a real back sprite. It
checks that Litecoin is remembered as a face, not marked removed, and that the
controller records the mismatch and continues to an unknown card. Previously,
the gray empty-slot rule misclassified the silver Litecoin card as empty.

```powershell
python test_coinflip.py --image tests/fixtures/coinflip_mixed.png
python -m unittest discover -s tests -v
```
