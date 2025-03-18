# Automation-Bots - PATCH 1.4.0

## Descrizione
Automation-Bots è un progetto che include bot per automatizzare le attività sui giochi "CoinClick" e "2048". Questi bot sono progettati per eseguire azioni specifiche nel gioco in modo automatizzato.

## Funzionalità
- **CoinClick Bot**: Automatizza il clic sui pulsanti e gestisce le risorse nel gioco CoinClick.
- **2048 Bot**: Automatizza le mosse nel gioco 2048 per cercare di ottenere il punteggio più alto possibile.
- **Coin-Flip Bot**: Automatizza il gioco di memoria Coin-Flip, supportando 3 livelli di difficoltà (1-3) con griglie di dimensioni diverse.
- **Hamster Climber Bot**: Automatizza il gioco del criceto che salta, gestendo i tempi e i movimenti per massimizzare il punteggio.

## Requisiti di Sistema
- Python 3.7 o versione successiva
- Modulo Selenium per l'automazione del browser (per CoinClick)
- Modulo PyAutoGUI per l'automazione del mouse e della tastiera (per 2048)
- Connessione Internet stabile (per CoinClick)


## Installazione
1. Clona il repository da GitHub:
   ```bash
   git clone https://github.com/tuonome/Automation-Bots.git
=======
# Auto-play Rollercoin Game Bot

A bot to automate Rollercoin mining through mini-games.

## Supported Games

The bot supports the following Rollercoin mini-games:

1. **CoinClick**
   - A simple clicking game
   - Requires precision and speed

2. **Coin-Flip**
   - Card memory game
   - Supports 3 difficulty levels (1-3)
   - Level 1: 3x4 grid
   - Level 2: 4x4 grid
   - Level 3: 5x4 grid

3. **2048 Coins**
   - Classic 2048 game
   - Uses arrow keys to combine numbers

4. **Hamster Climber**
   - Hamster jumping game
   - Requires precise timing

## Requirements

- Python 3.x
- PyAutoGUI
- Tkinter (included with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Auto-play-Rollercoin-game.git
cd Auto-play-Rollercoin-game
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Launch the main program:
```bash
python main.py
```

2. In the GUI, configure:
   - Game positions (where to click to find games)
   - Start button positions (where to click to start each game)
   - Gain Power button position
   - Game execution order
   - Coin-Flip difficulty level
   - Scroll value (default: -390)
   - Banner event option

3. To find correct positions:
   - Click "Find" next to each position field
   - Move mouse to desired position
   - Press OK in the dialog window
   - Confirm if you want to use those coordinates

4. Save configuration by clicking "Save Configuration"

## Usage

1. Make sure the Rollercoin browser window is open and visible
2. Start the bot by clicking "Start Bot"
3. The bot will execute games in the specified order
4. To stop the bot, click "Stop Bot"

## Important Notes

- Do not move the mouse during bot execution
- Keep the browser window visible and not minimized
- Scroll value may vary based on screen resolution
- If you have the event banner active, make sure to set the correct scroll value

## Troubleshooting

1. **Incorrect Positions**
   - Use the "Find" button to get exact positions
   - Ensure the browser is in the same position each time

2. **Bot Not Clicking Correctly**
   - Verify the browser window is active
   - Check that positions are correct
   - Make sure the scroll value is appropriate

3. **Permission Errors**
   - The bot will automatically save configuration to the home directory if it doesn't have permissions in the current directory

## Contributing

Contributions and suggestions are welcome! To contribute:

1. Fork the repository
2. Create a branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.