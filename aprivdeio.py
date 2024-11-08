import os
import random
import subprocess

# Specifica il percorso della cartella principale
cartella_video = "D:\\temp"

# Crea una lista per raccogliere tutti i file video
file_video = []

# Usa os.walk per scorrere la cartella e le sue sottocartelle
for root, dirs, files in os.walk(cartella_video):
    for file in files:
        if file.endswith(('.mp4', '.avi', '.mkv')):
            # Aggiungi il percorso completo del file video
            file_video.append(os.path.join(root, file))

# Scegli un video casuale
if file_video:  # Verifica se ci sono video
    video_casuale = random.choice(file_video)

    # Apri il video con il lettore predefinito
    subprocess.run(["start", video_casuale], shell=True)
else:
    print("Nessun file video trovato.")
