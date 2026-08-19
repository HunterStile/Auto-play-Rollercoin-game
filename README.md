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

Everything (GUI, all 8 game bots, automation engine) ships inside the single
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
| 2 | 🃏 **CoinFlip** (Memory) | Memory | Card color memorization, 3 difficulty levels | ✅ |
| 3 | 🔢 **2048 Coins** | Puzzle | Arrow-key tile merging pattern | ✅ |
| 4 | 🐹 **Hamster Climber** | Reaction | Green-bar detection + spacebar jumps | ✅ |
| 5 | 🪝 **Coin Fisher** | Aiming | Coin clustering, shoots densest group | ✅ |
| 6 | 🎮 **CoinMatch** | Match-3 | 8x8 grid scan + AI move evaluation | 🚧 In lavorazione |
| 7 | 🚀 **Flappy Rocket** | Flappy | Rocket tracking + obstacle gap detection | 🚧 In lavorazione |
| 8 | 💥 **Token Blaster** | Shooter | Auto-fire + red enemy targeting | 🚧 In lavorazione |

All games are registered at startup by `game_engine/games/__init__.py` and
appear automatically in the GUI — no hardcoded game lists.

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
| CoinFlip (Memory) | 838, 1004 | 992, 500 | 1–3 |
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