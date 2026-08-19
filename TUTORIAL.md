# 🎮 RollerCoin Auto-Play Bot — Step-by-Step Tutorial

> **"How do I run this script?"** — the exact answer, from zero to a running bot.
> Written in plain English, no programming experience required (the
> README [quick start](README.md) is the short version).

---

## 🚀 EASIEST WAY: use the .exe (no Python, nothing to install)

Forget installs, terminals, `pip`, venvs — none of it. The project ships a
**single Windows executable**:

1. Go to the **[Releases](https://github.com/HunterStile/Auto-play-Rollercoin-game/releases)**
   page and download **`RollerCoin-bot.exe`**.
2. Put it in any folder (ex. `C:\RollercoinBot`) and **double-click** it.
3. The configuration window opens directly — your settings will be saved
   automatically next to the .exe.
4. Follow steps **[6 (browser)](#6-prepare-rollercoin-in-your-browser)**,
   **[7 (GUI)](#7-run-the-configuration-gui)**, **[8 (calibrate)](#8-calibrate-positions-very-important)**,
   **[9 (games)](#9-choose-your-games-and-order)** and
   **[10 (start)](#10-start-the-bot)** below — that's all you need.

> 🛡️ If Windows SmartScreen says *"Protected your PC"*: click **More info** →
> **Run anyway**. It's the well-known false positive for unsigned executables
> built with PyInstaller, not a real threat.

The rest of this tutorial documents the **source-code way** (for developers
and contributors). The .exe speedrun is:

```
download .exe  →  double-click  →  [Find] positions  →  Save  →  Start Bot
```

---

## 📌 Table of contents

1. [What this bot does](#1-what-this-bot-does)
2. [What you need before starting](#2-what-you-need-before-starting)
3. [Install Python](#3-install-python)
4. [Download the project](#4-download-the-project)
5. [Install the dependencies](#5-install-the-dependencies)
6. [Prepare RollerCoin in your browser](#6-prepare-rollercoin-in-your-browser)
7. [Run the configuration GUI](#7-run-the-configuration-gui)
8. [Calibrate positions (very important)](#8-calibrate-positions-very-important)
9. [Choose your games and order](#9-choose-your-games-and-order)
10. [Start the bot](#10-start-the-bot)
11. [Frequently asked questions](#11-frequently-asked-questions)

> ⚠️ This is for **educational purposes only**. Check RollerCoin's
> Terms of Service before using it. You are responsible for your own usage.

---

## 1. What this bot does

The bot plays **RollerCoin mini-games for you** while you're away. It
recognizes the games on your screen (via color detection), clicks by itself,
and collects the hash power you earn. It currently supports **8 games**:

CoinClick · CoinFlip (Memory) · 2048 Coins · Hamster Climber · CoinMatch ·
Flappy Rocket · Coin Fisher · Token Blaster

To work, the bot needs **to see** your screen. This is why *pyautogui* only
works on real Windows/macOS with a visible screen — no anger, no virtual-only
machines without a display.

---

## 2. What you need before starting

| Requirement | Notes |
|-------------|-------|
| **Windows PC** | The bot controls your mouse pointer — it needs a real screen |
| **Internet** | To install Python and the dependencies, then to play |
| **A RollerCoin account** | Already registered and logged in |
| **1920×1080 screen** | Not mandatory, but everything is tuned for it. 1366×768 works with extra calibration |
| **Browser at 100% zoom** | Critical! If the zoom isn't 100%, the bot clicks in the wrong place |

**Do NOT touch the mouse or keyboard** while the bot is running — it uses
them! (The failsafe: slam the mouse to a corner of the screen to abort.)

---

## 3. Install Python

1. Go to <https://www.python.org/downloads/> and download Python **3.12**
   (any 3.8+ version is fine).
2. Run the installer.
3. ⭐ **IMPORTANT**: tick the box **"Add Python to PATH"** at the bottom of the
   first screen, then click **Install Now**.

Verify the install. Open a terminal (press `Win + R`, type `cmd`, press Enter)
and run:

```
python --version
```

You should see something like `Python 3.12.x`. If you instead get a
`'python' is not recognized` error, Python is not in PATH — reinstall and tick
*Add to PATH* this time.

---

## 4. Download the project

**Option A — via Git (recommended if you want updates):**

```
git clone https://github.com/HunterStile/Auto-play-Rollercoin-game.git
cd Auto-play-Rollercoin-game
```

**Option B — as a ZIP (no Git needed):**

1. Open <https://github.com/HunterStile/Auto-play-Rollercoin-game>
2. Click the green **Code** button → **Download ZIP**.
3. Extract it to any folder (e.g. `C:\Rollercoin`).
4. Open a terminal in the extracted folder (in File Explorer: `Shift + right
   click` inside the folder → "Open a command window here").

---

## 5. Install the dependencies

The project needs a few Python libraries. It's best to install everything in a
**virtual environment** (`venv`) so we don't touch your global Python.

Open a terminal in the project folder and run these commands one by one:

```
python -m venv venv
```

> Wait a few seconds; this creates a folder `venv/`.

```
venv\Scripts\activate
```

> Your prompt should now start with `(venv)` — this means Python uses the
> virtual environment. ⭐ You must **reactivate** it every time you open a new
> terminal before running the bot.

Now install the list of dependencies from `requirements.txt`:

```
pip install -r requirements.txt
```

On success you should see "Successfully installed ..." with `pyautogui`,
`keyboard`, `Pillow` and `pynput`.

> **Alternatively** there's a folder named `Installazione` with a
> `requirements.txt` and an `install.py`. You can run it manually:
> ```
> cd Installazione
> python install.py
> cd ..
> ```
> It only installs `pyautogui numpy pillow keyboard` — it does NOT create or
> activate a venv for you. Prefer the `venv` flow above.

**Verify the install worked:**

```python
python -c "import pyautogui, keyboard, PIL, pynput; print('OK - all imports fine!')"
```

You should see `OK - all imports fine!`. If you see a
`ModuleNotFoundError`, you are not in the venv: run `venv\Scripts\activate`
first and install again.

---

## 6. Prepare RollerCoin in your browser

1. Login to <https://rollercoin.com>.
2. Set the browser zoom to **exactly 100%** (`Ctrl + 0`).
3. Make the window **1920×1080 or maximize** it.
4. Open the **Choose Game** page (`https://rollercoin.com/game/choose_game`)
   so that all the game tiles are visible on the page.
5. Keep this tab open and in the foreground during the whole run. Don't
   minimize the window and don't switch tabs.

---

## 7. Run the configuration GUI

With your venv active, in the project folder:

```
python main.py
```

A window titled **"RollerCoin Auto-Play Bot - Configuration"** opens with all
the games listed. From here you:

- set game positions,
- set start-button positions,
- set gain-power position,
- enable games / order,
- and start/stop the bot.

> 🔎 Reminder: if you get a `ModuleNotFoundError` right now, you forgot to
> activate the venv (`venv\Scripts\activate`).

---

## 8. Calibrate positions (very important)

The bot needs the screen coordinates where each game lives. **Every
user/hardware has different numbers**, so don't copy them manually — measure
them with the built-in **Find** button.

The concept is simple: you point the mouse where the target is, click **Find**
in the GUI, and it copies those numbers into the field.

1. Make sure RollerCoin's **Choose Game** page is visible on screen.
2. Next to the *CoinClick position* field, in the GUI, click **Find**.
3. A small window says *"Move your mouse to the desired position and press
   OK. You have 3 seconds to position the mouse."*
4. Quickly hover the mouse over the **CoinClick game tile** on the website,
   wait a moment (the app auto-scrolls to match your page).
5. Press **OK**; a message shows the coordinates found:
   `Position found: (842, 289) Do you want to use these coordinates?` → **Yes**.
6. Repeat for each game position you'll play, and for the **Start** button of
   each game (the blue *PLAY* button in the middle of the tile).
7. Also set **Gain Power** to the click button that collects hash-power after
   a round.

> 🗌 Screens at 1920×1080 have similar defaults as in the README — but always
> measure your own. And after RollerCoin changes its layout, calibrate again.

> ⬇️ **Why the bot scrolls while you "Find"?** The **Scroll Down Value** is
> the **first** setting in the GUI and it's used in **two places**. When you
> press **Find**, the bot first scrolls the page by that amount — so the grid
> is aligned exactly like it will be during play. The bot applies the **same
> scroll again** after every round (F5 refresh) to realign the tiles. This is
> why a **fixed scroll** is needed: it keeps your saved coordinates valid.
> If a promotional banner is on the page, keep **Scroll Event Enabled** ticked
> so the scroll is applied; no banner → untick it and the bot won't scroll.

---

## 9. Choose your games and order

In the **Game Order** section:

1. Tick the checkbox next to each game you want to automate.
2. Set the order number (1 = first) next to the Spinbox.
3. If you use CoinFlip, the **Other Settings** section has the **Difficulty**
   level (1, 2 or 3 — grid size).
4. In **Other Settings** you'll also find **Gain Power Position**.
5. Games marked *(in lavorazione)* are still under development and are disabled
   in the GUI until they're ready.

Then press **Save Configuration** — this writes `game_config.json` and
generates `Routine_config.py`.

---

## 10. Start the bot

In the GUI press **Start Bot**. The bot launches in the background and the
button turns into **Stop**. The demo label at the bottom of the window shows
the status.

Quickly switch to the RollerCoin tab (the bot already clicked on the page to
get focus — but you may need to switch focus manually if the value is a
standalone engine).

You can watch the console of `main.py` — the orchestrator prints what it's
doing (`Running game: coinclick`, `Pair found!` …).

To get hash power edition, **switch to RollerCoin tab** and leave it running.
The bot loops games in your chosen order, refreshes the page between plays
and claims "Gain Power".

When done, go back to the GUI and press **Stop Bot**. Closing the GUI while
bot is running prompts you to stop it.

> **Alternative:** after you saved the config once, you can run the bot
> directly without the GUI:
> ```
> python Routine.py
> ```

---

## 11. Frequently asked questions

### 11.1 `ModuleNotFoundError: No module named 'pyautogui'`
You are not using the venv or dependencies are missing.
Run `venv\Scripts\activate`, then `pip install -r requirements.txt`.

### 11.2 The bot clicks but nothing happens on screen
- Browser zoom must be **100%** (`Ctrl+0`).
- The RollerCoin window must be **visible** (not minimized).
- Positions were measured at a different layout/resolution — redo **Find**.

### 11.3 "Game not detected / wait_game_ready fails"
The game page was still loading, or there's a promotional banner pushing the
grid up. Wait for the page to be fully loaded, adjust `scroll_down`, or press
F5 to refresh.

### 11.4 My keyboard key does nothing while bot runs
Some games need the arrow keys, some need space, some the mouse. If the bot
gets stuck on a game, it likely needs position recalibration.

### 11.5 Can I run in a VM / over Remote Desktop / without mouse?
Only if a display is actually available. Remote Desktop, headless servers,
and Windows sandboxes often don't show the games correctly. Run on your
physical desktop screen for reliable results.

### 11.6 Will I get banned?
This project is **educational**. It's fully automated screen-use of the real
site — RollerCoin's ToS may forbid it. Use it on your own accounts, your own
responsibility, at your own risk, and preferably spend it in moderation for
learning. The author provides zero guarantees about account status or terms.

### 11.7 I want to add my own game
Read [Architecture](README.md#%F0%9F%8F%97%EF%B8%8F-architecture) in the
README. Create `game_engine/games/<name>.py` overriding `BaseGame` and
`@register_game`, save, restart the GUI — it appears automatically.

### 11.8 Where can I report a bug?
Open an issue at
<https://github.com/HunterStile/Auto-play-Rollercoin-game/issues> with:
Windows version, Python version, console output while the demo runs, and a
screenshot of the problem.

### 11.9 I downloaded the .exe — do I still need the whole guide?
No. The .exe replaces sections 2–5 and 7 of this guide for you. Read only
sections 6, 8, 9 and 10. All settings live next to the .exe.

### 11.10 Windows says the .exe is "protected / dangerous"
This happens because the .exe is **unsigned** (no paid code-signing
certificate — out of reach for a hobby project). It's a false positive of
SmartScreen and antivirus suites on any PyInstaller build. Click
**More info → Run anyway**. Alternatively, run the bot from source to build
it yourself with `python build_exe.py`.

---

<div align="center">

> ⭐ If this project helped you, leave a star on
[GitHub](https://github.com/HunterStile/Auto-play-Rollercoin-game) — it helps
more people find it. Happy mining!

</div>