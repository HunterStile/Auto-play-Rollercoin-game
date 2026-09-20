# 🎮 RollerCoin Auto-Play Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![Gaming](https://img.shields.io/badge/Gaming-Automation-red.svg)](https://rollercoin.com)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d6.svg)](https://www.microsoft.com/windows)

> **Advanced automation system for RollerCoin mini-games with AI-powered strategies and a configurable dark-theme GUI**

> ⚠️ This bot is for **educational purposes only**. Review RollerCoin's
Terms of Service before use. Use it at your own risk.

## 💾 Don't want to install Python? Download the .exe

> ✅ **Non-programmers recommended path — no Python, no terminal, no deps.**

Grab the latest **`RollerCoin-bot.exe`** from the
**[Releases](https://github.com/HunterStile/Auto-play-Rollercoin-game/releases)** page,
put it in any folder, double-click it, and the configuration GUI opens
directly. Configure → **Save** → **Start Bot**. That's it.

> 👉 **Want the step-by-step setup for the .exe?** Jump straight to the
> **[TUTORIAL](TUTORIAL.md)** — it walks you through configuring the buttons
> and positions from scratch (including the Scroll Down Value explained below).

Everything (GUI, all 10 game bots, automation engine) ships inside the single
`.exe`:

- Config files (`game_config.json`, `Routine_config.py`) are created **next to
  the .exe** automatically.
- "Start Bot" runs the automation engine as a child of the same .exe — no
  Python needed on the target PC.
- If SmartScreen/antivirus warns: it's the well-known false positive for
  unsigned PyInstaller executables — choose "More info → Run anyway".

Build it yourself from source: `pip install -r dev-requirements.txt && python build_exe.py`
(output: `dist/RollerCoin-bot.exe`).

## 🌟 Overview

RollerCoin Auto-Play Bot is a Python automation system that plays RollerCoin
mini-games automatically, maximizing your hash power earnings while you sleep.
It is built on a modular **game engine** (`game_engine/`) that auto-discovers
game bots, so adding a new mini-game is as easy as dropping a new module in the
`games/` folder.

## 🎯 Mini-Games

| # | Game | Type | Strategy | Status |
|---|------|------|----------|--------|
| 1 | 🪙 **CoinClick** | Clicking | Pixel color detection & rapid clicks | ✅ |
| 2 | 🃏 **CoinFlip** (Memory) | Memory | Automatic grid detection, visual memory and verified pair removal | ✅ |
| 3 | 🔢 **2048 Coins** | Puzzle | Arrow-key pattern and verified reward-dialog detection | ✅ |
| 4 | 🐹 **Hamster Climber** | Reaction | Green-bar detection + spacebar jumps | ✅ |
| 5 | 🪝 **Coin Fisher** | Aiming | Visual net-return detection and full-path aiming through coin groups | ✅ |
| 6 | 🎮 **CoinMatch** | Match-3 | Adaptive 8x8 detection, seven coin types and scored swaps | ✅ |
| 7 | 🚀 **Flappy Rocket** | Flappy | Blue cockpit tracking, pipe gaps and vertical-speed control | 🧪 MVP disponibile |
| 8 | 💥 **Token Blaster** | Shooter | Ship tracking, targeting and predicted collision avoidance | 🧪 Beta disponibile |
| 9 | 🧩 **Dr. Hamster** | Match-4 | Adaptive 8x10 board, pair placement and verified arrow inputs | 🧪 MVP disponibile |
| 10 | **Crypto Hex** | Hex stack puzzle | Adaptive 19-cell board, colored stack reading and verified placement | 🧪 MVP disponibile |

All games are registered at startup by `game_engine/games/__init__.py` and
appear automatically in the GUI — no hardcoded game lists.

Crypto Hex is selectable as **MVP**. It locates the three tray rims and the
19-cell hex board, reads red/blue/green stacks from bottom to top, and favors
placement beside matching exposed colors. Mixed stacks retain their underlying
colors in the reading. The heuristic prioritizes a combined top run of at least
ten, following the [firsthand player guide](https://ecency.com/@coderad/rollercoin-minigame-guide-win-conditions-strategies-and-ratings);
merge direction, cascades and scoring are handled by rereading the observed
board after each placement rather than a complete game simulation.

```powershell
python test_cryptohex.py --image tests/fixtures/cryptohex.png --output debug/cryptohex/detection.png
python test_cryptohex.py --play
python -m unittest discover -s tests -p test_cryptohex.py -v
```

Inspection sends no input. `--play` waits four seconds to focus an already
started round, then drags a tray stack to an empty hex. If the game's controls
require two clicks, use `--play --input-mode click` in the standalone launcher.
The GUI routine uses drag by default. Configure Crypto Hex's icon and Start
positions before enabling it: the fallback coordinates are not calibrated.
Two consistent reads authorize a move; further input waits for a stable local
board change (or consumption of a full top run that clears immediately).
It keeps the verified board geometry, reads replacement piles after every
placement and chooses new moves using their exposed top colors. A tall mixed pile
can hide another hex: only that obscured hex is blocked, while the bot keeps
playing on readable cells. An unconfirmed placement stops without repeating it. Q or the
mouse top-left failsafe stops play, and held mouse buttons are released even
on input errors. A four-second lack of progress or 65-second deadline returns
an unverified result. A recognized empty tray waits for refill until the round
deadline instead of triggering the four-second detection timeout.
A stable shared reward dialog indicates completion, not
a verified win. The routine handles reward collection.

The supplied screenshot is replayed at 70%, 100% and 120% scale with offsets.
It has a one-chip blue pile and four-chip red pile on the board; the tray has
three green, three red, and five green under five blue chips. Only this artwork
and three colors are covered. Severe overlap, tall stacks hiding other stacks,
additional colors or unfamiliar layouts can stop detection. A live level-one
win (12,750 points) was observed and confirmed by the user on September 19.
The real replay covers five placements, replacement trays, merges and the
brighter CLAIM REWARD dialog. Later levels remain unverified. Standalone play,
the main GUI routine and the Windows executable save the last frame and stop reason under `debug/cryptohex/`
(next to the executable for frozen builds). No new dependencies;
rebuild existing executables to include the game.

Dr. Hamster is selectable as **MVP**. It reads the dotted 8x10 grid and the
orange, blue and green blocks. The supplied September 19 screenshot is tested
at 70%, 100% and 120% scale and different positions: 14 blocks, including the
active green pair and two face blocks. It scores reachable pair placements for
horizontal/vertical runs of at least four, favors clearing face blocks and
prepares reachable two/three-block lines using colors already on the map.
Buried gaps do not count as future matches; height and covered holes are penalized.
It verifies rotations and sideways movement from subsequent images, then holds
DOWN continuously across readings while the aligned pair is more than two rows
from its planned landing. Within the final two rows it releases the hold and
uses one short press per reading to limit carryover into the next pair.
It releases DOWN on unknown readings, repositioning, a result panel, Q, the
round deadline or any error. Live held-key speed still needs calibration.
Older pair links and post-clear
cascades are not simulated; each new pair uses a fresh board reading.

This is an offline-tested first version; live wins, keyboard timing, other
artwork and result dialogs in Dr. Hamster still need validation. It acquires a
pair only while isolated near the top, requires two consistent reads, and
suppresses input on unknown/ambiguous images. Start it early in a round with
the entire grid visible and the game focused. Q or the mouse top-left failsafe
stops it. Missing control observations stop it after four seconds; an ignored
rotation/movement is retried once. Timeout is not success. The shared reward
detector must see a stable dialog before reporting round completion, which is
not a verified win. No new dependencies are required.

```powershell
python test_drhamster.py --image tests/fixtures/drhamster.png
python test_drhamster.py --play
python -m unittest discover -s tests -p test_drhamster.py -v
```

`--play` waits four seconds to focus an already started round. Inspection sends
no keys; `--output debug/drhamster_detection.png` optionally annotates a saved
image (create the parent directory first). Standalone play saves its last frame
and reason under `debug/drhamster/`. To use the main routine, configure the
Dr. Hamster game-icon and Start coordinates in the GUI before enabling it;
their fallback coordinates have not been calibrated. Existing executables
must be rebuilt to include the new game.

Flappy Rocket is selectable as **MVP** in the GUI. It locates the gray board,
recognizes the blue cockpit with nearby orange/gray hull, and pairs red/green
pipes. Spacebar pulses aim at the next gap, accounting for rocket size and
vertical velocity; without pipes it maintains mid-board altitude. The supplied
screenshot is tested at 70%, 100% and 120% scale and different screen positions.
The user reported a live win without errors on September 19, 2026. This first
version assumes the supplied artwork and approximate rocket size; additional
rotations and later levels still need validation and may need timing calibration.
Keep the game visible and focused. Unknown readings suppress input and stop
after three seconds. Q or the mouse top-left failsafe stops the standalone run.
A stable cyan panel indicates round end, not a verified win; its detection is
tested synthetically. Timeout returns an unverified result. Reward collection
remains with the routine's configured click. Rebuild existing executables to
include this MVP.

```powershell
python test_flappyrocket.py --image tests/fixtures/flappyrocket.png
python test_flappyrocket.py --play
python -m unittest discover -s tests -p test_flappyrocket.py -v
```

`--play` waits four seconds to focus an already started game. Without `--play`,
the launcher only inspects a screenshot; `--output detection.png` saves boxes
and the gap target. `test_flappy_scanner.py` uses the same inspector and options.
On an unverified stop, the standalone run saves its last frame and reason to
`debug/flappyrocket/last_failure.png` and `last_failure.txt` (Git-ignored).

Token Blaster recognizes the board, animated ship, green/orange enemies and
yellow and pale projectile candidates, including the muted colors of the supplied video.
It retains a nearby target until it disappears and fires while an enemy is in
the shot lane. Movement stays held between valid readings instead of stopping
during every capture/analysis. Detection runs on a reduced image. Short-lived
motion tracks estimate projectile and enemy velocities; steering compares the
left, stationary and right routes over about 0.7 seconds, including ship size,
board edges and uncertainty in movement speed. A predicted collision overrides
targeting and pauses fire. Orange divers remain visible to the detector near
the ship; hull shape and blue cockpit reject explosion fragments. These linear
forecasts still need live calibration, especially curved dives, crowded scenes
and unfamiliar projectiles. Later levels and result dialogs remain unverified.
In the supplied video, ship recognition still drops briefly at 31.7–32.0 seconds;
input pauses during those unknown readings. Offline replay does not prove wins.
A missing board/ship releases keys and
stops after three seconds; timeout and loss of detection return an unverified
result. Token Blaster is selectable in the main GUI as beta: configure its icon
and Start positions, enable it in Game Order, save and use Start Bot. A live win
has been reported by the user; later levels and automatic result verification
remain under development. The existing routine handles reward clicking and the
transition to the next game. Existing executables must be rebuilt to include it.

Inspect without input: `python test_tokenblaster.py --image tests/fixtures/tokenblaster_level1.png`.
For an already started round: `python test_tokenblaster.py --play`, then focus
the game during the four-second countdown. Press Q to stop.
The standalone launcher prints the stop reason. On an unverified stop (except Q)
it saves the last full screenshot and reason locally to
`debug/tokenblaster/last_failure.png` and `last_failure.txt`; these are Git-ignored.
Offline regressions: `python -m unittest discover -s tests -p "test_tokenblaster*.py" -v`.


2048 Coins keeps its `down, left, down, right, down` pattern. It checks for the
cyan reward button, its CLAIM REWARD lettering, and the surrounding gray dialog
before each arrow; the cyan progress bar and tiles alone do not end a round.
Arrows pause on the first candidate and the same dialog must persist across
readings at least 0.25 seconds apart. `game_duration` now means real elapsed
seconds (default 120, allowing longer higher-level rounds), not pattern repetitions. A timeout returns an unverified
result. Reward collection remains with the existing routine and configured
coordinates. The supplied win dialog is tested offline; unseen result layouts
and live timing still need verification.

Use `python test_coin2048.py --image path/to/screenshot.png` for an offline
check, or `python test_coin2048.py --play` for an already started round after a
four-second countdown. Move the mouse to the top-left corner to stop.

Coin Flip now detects its card grid automatically; its manual difficulty selector
has been removed. Old `LEVEL_MEMORY` settings are ignored by the bot. Start with
the entire rack visible and preferably all cards covered. The detector supports
4 rows with 3, 4 or 5 columns. The supplied real screenshots validate 12-, 16-
and 20-card racks, including empty slots, black-and-white faces and silver
Litecoin cards. Face matching compares spatial color and symbol images,
without requiring a predefined list of currency names.

Run `python test_coinflip.py` to inspect the screen without clicking, or
`python test_coinflip.py --play` to play an already started round after a
four-second countdown. The bot opens unknown cards, prioritizes remembered pairs,
waits for mismatches to close and confirms pairs by their disappearance. A moved
rack clears stale coordinates and memory. Unknown readings suppress clicks;
three failed opening attempts exclude a card. Eight seconds without progress or
a 75-second time limit stops the round with an unverified result. All cards
observed removed counts as completion. The shared cyan end-panel color
(RGB 3, 225, 228) also ends the round after two consecutive readings covering
most of the last rack's central area, including after a transition frame. This
color check detects a finished round; it does not distinguish victory from defeat.
The panel check is tested with synthetic frames and needs live confirmation.
Move the mouse to the top-left corner to stop. Live animation timing and unseen
card artwork still need testing. Rebuild existing `.exe` files to include this update.

Coin Match supports all seven coin types in the supplied final-level screenshots. It recognizes
BTC, DOGE, ETH, DASH, Monero (XMR), the blue/gray higher-level coin
(`BLUE_GRAY`) and the final-level bright-yellow coin (`YELLOW_SYMBOL`). The
last two names are visual identifiers, not verified currency names. It locates
the grid automatically. Keep all 64 coins
visible. The old `grid_x`, `grid_y` and `cell_size` settings are no longer used.
An optional `scan_region=(left, top, width, height)` passed to `CoinMatchBot`
selects a board by its center if multiple boards are visible.

To inspect the visible board without clicking, run `python test_coinmatch.py`.
To play one already started round, run `python test_coinmatch.py --play` and
focus the game during the four-second countdown. Move the mouse to the top-left
corner to stop through PyAutoGUI failsafe. The bot waits for stable readings and
avoids repeating an unconfirmed swap on the same board. It stops after eight
seconds without a playable board or after 75 seconds. Two consecutive cyan
end-panel readings return control to the routine for its configured Claim reward
click; they do not certify a win. Other coin types and levels need more samples.
Validation covers screenshot replays and mocked input; live drag behavior still
needs verification. Source changes require rebuilding any existing `.exe`.


## ✨ Key Features

- 🎨 **Dark-themed configuration GUI** — discover games dynamically, set
  positions, difficulty and order, all from one clean interface.
- 🎯 **Position Finder** — a "Find" button in front of every coordinate field:
  move the mouse, confirm, done.
- 🔄 **Smart rotation** — run games in the order you choose, looping forever.
- 💾 **Persistent config** — saves `game_config.json` and generates
  `Routine_config.py` automatically.
- 🛡️ **Resilient** — automatic error recovery and game-ready detection.
- 🎥 **Bonus tools**: a video tagger/player (`aprivdeio.py`) and an
  autoclicker (`autoclick.py`).

## 📦 Installation

> 👉 **Already have the .exe? You're done — skip this whole section.** Just
> run `RollerCoin-bot.exe`. Everything below is for running from source.

### 1. Prerequisites

- **Python 3.8+** (tested with 3.12) → download from
  [python.org](https://www.python.org/downloads/) and tick
  *"Add Python to PATH"* during setup.
- **Windows** (PyAutoGUI screen control).
- **RollerCoin account**, logged in.
- Screen resolution **1920×1080** with browser zoom at **100%** (recommended).

### 2. Clone the repo

```bash
git clone https://github.com/HunterStile/Auto-play-Rollercoin-game.git
cd Auto-play-Rollercoin-game
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install dependencies

From the project root:

```bash
pip install -r requirements.txt
```

or use the included installer:

```bash
cd Installazione
python install.py
cd ..
```

Requirements (`requirements.txt`):

```txt
pyautogui==0.9.54   # screen automation (mouse + keyboard)
keyboard==0.13.5    # global key input handling
Pillow==10.2.0      # image processing
pynput==1.7.6       # low-level mouse/keyboard listeners
```

> 💡 **Troubleshooting import errors?** Missing dependencies are the #1 cause of
> "module not found". Uninstall all of the above and reinstall:
> `pip uninstall -y pyautogui keyboard Pillow pynput` then
> `pip install -r requirements.txt`.

## 🚀 Quick Start

The correct daily workflow is **configure → save → start**:

```bash
python main.py
```

1. In the GUI, every field already has sensible defaults.
2. Check the **Scroll Down Value** (first setting) matches your page.
3. Use **Find** on any coordinate field to capture your real mouse position.
4. Tick the games you want to play and set their **order**.
5. Click **Save Configuration**.
6. Click **Start Bot** — the bot launches `Routine.py` in the background.
7. Switch to the RollerCoin browser tab and enjoy. Use **Stop Bot** to halt.

After saving once, you can also start the bot directly:

```bash
python Routine.py
```

### Supported standalone scripts

| Script | What it does |
|--------|--------------|
| `main.py` | Configuration GUI (recommended entry point) |
| `Routine.py` | Runs the selected games using the saved config |
| `aprivdeio.py` | Video tagger / playback for videos |
| `autoclick.py` | Configurable autoclicker (mouse, keyboard, sequences) |
| `cerca_posizione.py` | Standalone position finder |

## 🧭 Configuring positions (the "Find" workflow)

1. Open RollerCoin in your browser at 100% zoom and login.
2. Open the **Choose Game** page so all game tiles are visible.
3. In the GUI click **Find** next to a game field, hover exactly over the game
   tile, confirm. Repeat for the **Start** button of that game.
4. Also set **Gain Power** to the "Claim power" button that appears after a
   match.
5. **Save Configuration**.

Typical defaults for 1920×1080 (from the saved `game_config.json`):

| Game | Game position | Start button | Difficulty |
|------|--------------|-------------|-----------|
| CoinClick | 842, 289 | 907, 427 | — |
| CoinFlip (Memory) | 838, 1004 | 992, 500 | Automatic |
| 2048 | 1185, 857 | 915, 497 | — |
| Hamster Climber | 854, 710 | 859, 481 | — |
| Coin Fisher | 483, 696 | 904, 480 | — |
| CoinMatch | 475, 554 | 990, 450 | — |
| Flappy Rocket | 1174, 700 | 990, 450 | — |
| Token Blaster | 1180, 506 | 990, 450 | — |

> 📌 **Scroll Down Value** (`scroll_down`) is the **first** setting in the GUI
> because it's used in **two places**:
>
> 1. **The Find button** — before capturing a position, the bot scrolls the
>    page by this amount, so the grid is aligned the same way it will be
>    during play.
> 2. **The bot itself** — after every round (refresh + `F5`) it re-applies the
>    same scroll to realign the game tiles.
>
> A **fixed scroll** is needed so that the coordinates stay valid. If a
> promotional banner is present, leave **Scroll Event Enabled** (`BANNER_EVENT`)
> ticked so the scroll is applied; if there's no banner, untick it and the bot
> won't scroll.

## 🏗️ Architecture

```
Auto-play-Rollercoin-game/
├── main.py                     # Configuration GUI (dark theme, dynamic) + --routine mode
├── Routine.py                  # Entry point → runs the orchestrator (source mode)
├── build_exe.py                # Builds the Windows .exe (PyInstaller)
├── game_engine/
│   ├── base.py                 # BaseGame abstract class for all bots
│   ├── registry.py             # Auto-discovery of game modules
│   ├── orchestrator.py         # Rotation logic for selected games
│   ├── utils.py                # Click, screenshot, game-ready helpers
│   └── games/                  # One module per mini-game
├── functions.py                # Backward-compat re-exports (legacy)
├── Installazione/              # Alternative pip installer (setup helper)
├── requirements.txt            # Runtime Python dependencies
├── dev-requirements.txt        # Build-only deps (pyinstaller)
├── game_config.json*           # Saved settings (generated, git-ignored)
├── Routine_config.py*          # Generated Python config (git-ignored)
├── aprivdeio.py                # Video tagger / player (bonus)
├── autoclick.py                # Autoclicker (bonus)
├── PATCH_NOTES.md              # Changelog
├── TUTORIAL.md                 # Step-by-step install & usage guide
└── README.md                   # This file
```

`*` generated by the GUI (next to the .exe in packaged builds), git-ignored,
safe to delete anytime.

## 📖 Install & usage tutorial

New to the project? Read the step-by-step **[TUTORIAL](TUTORIAL.md)** — in 5
minutes the bot runs. The tutorial covers both **.exe users** (no Python,
double-click and go) and **source users** (install Python, create a venv,
*how do I run this script?*).

## 🏭 Building your own .exe

1. `pip install -r dev-requirements.txt`
2. `python build_exe.py`
3. Grab `dist/RollerCoin-bot.exe` and distribute it — add it to a GitHub
   [Release](https://github.com/HunterStile/Auto-play-Rollercoin-game/releases), for example.

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'pyautogui'` | `pip install -r requirements.txt` inside the **venv** you activate before every run |
| Bot clicks but nothing happens | Browser zoom must be exactly **100%**, window **1920×1080**, game page visible |
| `Bot Non Cliche` / wrong spots | Re-run **Find** for each position. RollerCoin layout changes can shift the grid |
| Bot doesn't find a game | Check browser page loaded fully, adjust `scroll_down` value |
| `pyautogui` fails with no display | PyAutoGUI is Windows/mac-only — the bot needs a physical screen |
| GUI says **no valid games configured** | Enable at least one game in the "Game Order" section and save |

## 🔧 Advanced

- **Add a new game** — create `game_engine/games/<name>.py` with a
  `@register_game` class extending `BaseGame`, then restart the GUI. It shows
  up automatically.

## ⚖️ Legal & disclaimers

Use this project **only for educational purposes**. It engages in real screen
automation, respect RollerCoin's Terms of Service, don't break their fair-use
rules, and remember: any use is at your own full responsibility.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/xxx`)
3. Make your changes
4. Submit a Pull Request — describe the game / change.

Issues: [https://github.com/HunterStile/Auto-play-Rollercoin-game/issues](https://github.com/HunterStile/Auto-play-Rollercoin-game/issues)

## 📄 License

MIT © HunterStile — see [LICENSE](LICENSE).

---

<div align="center">

**⚡ Maximize your RollerCoin earnings with intelligent automation ⚡**

[Tutorial](TUTORIAL.md) • [Issues](https://github.com/HunterStile/Auto-play-Rollercoin-game/issues) • [Releases](https://github.com/HunterStile/Auto-play-Rollercoin-game/releases)

</div>
