`cryptohex.png` is the user's game-only screenshot from 2026-09-19 22:57:15.
It contains 19 hex cells: blue x1 at column 2/row 4, red x4 at column 3/row 4
(one-based columns/rows), and tray piles green x3, red x3, green x5 below blue x5.
Tests replay at 70%, 100%, 120% scale and translated positions, reject unknown
colors, missing cells, clipped/ambiguous boards and other games. Strategy and
mouse control are tested offline, including input cleanup, acknowledgement,
timeouts and a mocked result panel. These checks do not establish live wins.
`test_cryptohex_refill.py` also moves the actual tray artwork onto the board in
synthetic frames. A ten-chip stack used to invalidate the hidden hex above it
and stop the whole reader. Tests now require continuing around that hex, retaining
validated coordinates through empty tray slots, reading changed refill colors,
and making six controller moves across two batches. This is not a live recording.

`cryptohex_live_024.png`, `_026.png`, `_029.png`, `_046.png` are game-only frames
from an authorized live run on September 19. After three placements a blue x8
pile covered a grid-validation pixel with its gray antialiased outline; its cap
also looked like a false blue x1 on the hex above. `_five_stack.png` captures
a second run where a mixed five-chip pile slightly overlapped the upper empty
hex. `cryptohex_live_win.png` is the third run's actual YOU WIN / 12,750-point
dialog. These regressions read new tray colors after each placement, continue
past the third move, and confirm the brighter reward dialog at different scales.

`cryptohex_tall_stacks.png` is the user's screenshot from 2026-09-20 00:19:19.
It has blue x9 at cell 5, green x6 at cell 14, and tray piles red x2, red x5,
blue x2. The blue cap's thin reddish outline was counted as another color run,
invalidating the entire board. At 70% zoom, the green cap's blended edge also
invalidated the empty cell above it. Replay at 70%, 100%, 120% and translated
positions verifies the counts, blocks the obscured cell 4, and confirms that
a pending merge from seven to nine chips permits the next move. Input is mocked;
this regression does not establish a live win.

`cryptohex_main_stall.png` is the game-only crop of `debug/cryptohex/last_frame.png`
saved by the main routine on 2026-09-20 at 00:28:26. Green x8 occupies cell 5,
blue x9 cell 14, and blue x1 under red x2 cell 15. The blue pile's base touches
the mixed pile's cap, so the central stripe used to join two separate sprites
and reject both. Tests require cap-shoulder validation to split the piles,
correct counts at three scales and offsets, and a placement through the same
orchestrator/play loop used by main. All mouse and keyboard input is mocked.

`cryptohex_crowded_stall.png` is the user's game-only screenshot from
2026-09-20 04:12:21. It has blue x5 at cells 4 and 10, red x9 at cell 8,
green x8 at cell 14, and blue x2 / green x1 / green x4 in the tray.
The blue cap shoulder obscured a grid-validation point; the small neighborhood
contained too little table and rejected the whole layout. At 70% zoom the red
pile's bottom sample landed on its blended rim, also rejecting the board.
Replay at 70%, 100%, 120% and offsets requires accurate counts, blocked hidden
cells 7 and 13, a legal next move and continued play through the main
orchestrator. All input is mocked; this is not evidence of a live win.

`flappyrocket.png` is the game-only crop of the screenshot supplied on
2026-09-19 at 22:16:10. It contains a blue-cabin rocket near (160, 582), smoke,
HUD text, and one red/green pipe pair around x=592..695. The dark rods extend
the pipe ends; tests check a conservative gap around y=95..497. Replay covers
70%, 100%, 120% scale and translation, smoke/HUD rejection, missing sprites,
incomplete pipes and ambiguous boards. Mocked control checks velocity, cooldown,
active-pipe selection, unknown frames, stop/timeout and synthetic end panels.
These tests do not establish live wins or calibrated jump physics.
Run `python -m unittest discover -s tests -p test_flappyrocket.py -v`.

`tokenblaster_level1.png` is the game-only crop supplied on 2026-09-11 at
22:24:28. It contains 27 enemies (7 green, 20 orange), one yellow projectile
and the player ship. Offline tests cover zoom/translation, target selection,
nearby-threat avoidance and suppression of input for unknown frames.
Run `python -m unittest discover -s tests -p test_tokenblaster_vision.py -v`.
These checks do not establish live wins or validate later levels.

`tokenblaster_video_09.png`, `_30.png`, `_36.png` and `_destroyed.png` are
game-only frames from the supplied 2026-09-11 22:33:10 recording at 9, 30, 36
and 37.5 seconds. The first three contain 28, 13 and 5 enemies; the last has
no player ship. They cover muted recording colors, exhaust animation, explosion
rejection and loss of the ship. Control tests reproduce the previous 45 ms
movement pulses and abandonment of nearby columns, and check target retention,
firing alignment and release of input on unknown frames.

`tokenblaster_video_372.png` and `_373.png` are game-only crops at 37.2 and
37.3 seconds from that same recording. The ship has exploded. Tests replay
both crops and their original screen placement to catch explosion fragments
misidentified as the player. Synthetic trajectories exercise diagonal incoming
shots, divers arriving from below, multiple threats, receding shots and stale
tracking. These validate steering decisions, not physical collision-free wins.

`tokenblaster_short_exhaust.png` is the game-only crop of the diagnostic image
supplied on 2026-09-11 at about 23:17. The live ship is at the right edge with
a short blue exhaust. The cockpit splits the gray nose and body into separate
components; regression coverage requires them to form one detected ship at
the original screen position while preserving explosion rejection.
It also verifies that the bright nose is excluded from projectile detection;
the frame contains one actual yellow projectile.

`tokenblaster_bonus_double.png`, `_triple.png` and `_wave.png` are the original
63x63 weapon pickup sprites retrieved on 2026-09-20 from RollerCoin's public
`https://rollercoin.com/static/img/game_sprites/game2/{double,triple,wave}_shot.png?v=2.0.0`.
Tests composite these icons onto the supplied game frame at two heights, three
scales and translated screen positions. They require separate bonus detections,
unchanged enemy/projectile counts, and continued ship recognition for the blue
wave pickup near the hull. These are synthetic scenes with real sprites, not
recordings of successful collections. Trajectory/controller tests cover pickup
reachability, missed/collected pickups, dangerous routes, concurrent firing and
dodging, and choosing enemy columns over continuing an unproductive escape.
The screenshot-to-steering test also checks that a pickup changes the decision.
Existing real frames must produce no false pickups. Live timing, collection
rates and completion before the in-game timer expires remain unverified.

`coinfisher.png` is the game-only crop of the screenshot supplied on 2026-09-10.
It contains 28 visible coins; account details and surrounding browser UI are excluded.
The rod foot sits on the beach below the water; its loaded gray net is above it.
The control regressions added on 2026-09-20 remove, translate and rotate that
net to simulate departure, return, a thin cable and a net still extended near
the dock. These modified frames are synthetic, not a live recording.

`coin2048_playing.png` and `coin2048_result.png` come from the 2026-09-11
19:58:32 and 19:59:56 screenshots. The latter is cropped around the win dialog.
Tests check recognition across scales and translations, cyan gameplay rejection,
missing text/panel rejection, ambiguous dialogs, score independence, keyboard
pattern preservation, stable confirmation and a real-time deadline. All input
is mocked. Only the supplied result layout is verified, not unseen loss screens.
The detector embeds a packed mask of the button lettering derived from this
fixture, so executable builds require no extra image data files.

`drhamster.png` is a game-only crop of the user's 2026-09-19 22:35:57
screenshot; wallet and browser information are excluded. The dotted board has
8 columns and 10 rows, 14 colored blocks (including the active green pair at
row 2, columns 4-5) and two face blocks at row 8/column 8 and row 10/column 7.
`tests/test_drhamster.py` replays it at 70%, 100% and 120% scale with offsets,
rejects unknown/clipped/ambiguous boards, and tests planning and mocked control.
Live keyboard timing and wins are not covered by this fixture.
Mocked play-loop tests also verify continuous DOWN across screenshots while
aligned, release in the final two rows, and release on a new/unknown pair,
repositioning, Q, deadlines, exceptions, failsafe and a result-panel candidate.

```powershell
python -m unittest discover -s tests -p test_coin2048.py
python test_coin2048.py --image tests/fixtures/coin2048_result.png
```

Run the offline regression checks from the repository root:

```powershell
python -m unittest discover -s tests -p "test_coinfisher*.py" -v
```

The tests replay the board at different positions and scales, and mock all mouse
input. They verify all 28 coins, the docked net at different angles, suppression
of clicks during travel and before departure is observed, immediate replanning
on the first ready frame, and the time limit after a slow capture. Geometry
tests score the full outward/return line from the rod foot, counting each coin
once; directions between coin centres can catch multiple rows. They do not
establish live projectile physics, exact collision radii, moving-coin interception
or wins. The net reach and conservative hit radius are calibrated from the
available still image, not from a recorded round.

For a manual round, start Coin Fisher and run `python test_coinfisher.py`, then
focus the game during the four-second countdown. Keep the entire game visible.
The bot detects the water automatically; an optional `scan_region` is now only
a search hint in `(left, top, width, height)` screen coordinates. A missing,
clipped or ambiguous board suppresses shots. Screenshot/mouse scale mismatches
stop the run. Move the mouse to the top-left corner to trigger PyAutoGUI failsafe.
The end-panel color check is heuristic; it does not certify a win or level 10.
The controller no longer uses a fixed one-second click cooldown. It observes
departure and docking before sending another click, scans again for a fresh aim,
and logs each shot with the predicted number of coins on its path. That number
is a geometric estimate, not a verified score. A launch that never visibly
starts stops with `launch not observed`, rather than repeatedly clicking.


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
