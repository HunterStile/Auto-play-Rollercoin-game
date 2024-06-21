import pyautogui
import time
import keyboard

# Funzione per controllare se i valori RGB rientrano in un determinato range
def is_green_color(r, g, b):
    r_range = range(75, 77)    # Range per il rosso (R) R=76, G=194, B=86
    g_range = range(193, 195) # Range per il verde (G)
    b_range = range(85,87)    # Range per il blu (B)
    return (r in r_range) and (g in g_range) and (b in b_range)

def mouse_click(x, y, wait=0.2):
    pyautogui.click(x, y)
    time.sleep(wait)

def coinclick(a):
    print("START GAME")
    while a == 1:
        # Definisci la regione centrale approssimata (modifica i valori se necessario)
        pic = pyautogui.screenshot(region=(530, 430, 828, 417))
        width, height = pic.size
        for x in range(0, width, 5):
            for y in range(0, height, 5):
                r, g, b = pic.getpixel((x, y))

                # Fine del gioco (se necessario)
                if b == 228 and r == 3 and g == 225:
                    a = 0
                    break

                # Rileva il rettangolo verde R=55, G=173, B=67
                if is_green_color(r, g, b):
                    mouse_click(x + 240, y + 150, wait=0)
                    print(f"Green detected at ({x}, {y}): R={r}, G={g}, B={b}")
                    time.sleep(1)
                    break

    print("END GAME")
    start()

def start():
    print("Premi Enter per iniziare, naciścialo solo quando è in corso il conto alla rovescia")
    keyboard.wait("enter")
    a = 1
    coinclick(a)

start()