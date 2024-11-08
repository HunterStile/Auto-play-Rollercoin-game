import os
import random
import subprocess

# Specifica il percorso della cartella con i video
cartella_video = "D:\\temp"

# Ottieni una lista di file nella cartella
file_video = [f for f in os.listdir(cartella_video) if f.endswith(('.mp4', '.avi', '.mkv'))]

# Scegli un video casuale
video_casuale = random.choice(file_video)

# Costruisci il percorso completo al file video
percorso_completo = os.path.join(cartella_video, video_casuale)

# Apri il video con il lettore predefinito
subprocess.run(["start", percorso_completo], shell=True)