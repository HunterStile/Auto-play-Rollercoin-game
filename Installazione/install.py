import subprocess
import sys

def install_requirements():
    try:
        # Esegui il comando pip per installare i pacchetti da requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dipendenze installate correttamente!")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'installazione delle dipendenze: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()