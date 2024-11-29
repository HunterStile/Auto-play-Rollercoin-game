import os
import random
import subprocess
import time

def trova_video(cartella):
    """Trova tutti i file video nella cartella e sottocartelle"""
    file_video = []
    for root, dirs, files in os.walk(cartella):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mkv')):
                file_video.append(os.path.join(root, file))
    return file_video

def termina_processo_video():
    """Termina i processi del video player usando taskkill"""
    try:
        # Termina i processi più comuni dei player video
        subprocess.run('taskkill /F /IM vlc.exe', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('taskkill /F /IM wmplayer.exe', shell=True, stderr=subprocess.DEVNULL)
    except:
        pass

def riproduci_video_casuale(tutti_video, video_riprodotti):
    """Riproduce un video casuale non ancora visto"""
    video_disponibili = list(set(tutti_video) - set(video_riprodotti))
    
    if not video_disponibili:
        print("Hai visto tutti i video! Resetto la cronologia.")
        video_disponibili = tutti_video
        video_riprodotti.clear()
    
    video_casuale = random.choice(video_disponibili)
    video_riprodotti.append(video_casuale)
    
    print(f"\nRiproduco: {os.path.basename(video_casuale)}")
    print("Premi INVIO per passare al prossimo video...")
    
    subprocess.Popen(["start", video_casuale], shell=True)
    return video_casuale

def main():
    cartella_video = "D:\\temp"
    tutti_video = trova_video(cartella_video)
    
    if not tutti_video:
        print("Nessun file video trovato.")
        return
    
    video_riprodotti = []
    
    print("Premi CTRL+C per uscire dal programma")
    
    try:
        while True:
            video_corrente = riproduci_video_casuale(tutti_video, video_riprodotti)
            input()  # Aspetta che l'utente prema INVIO
            termina_processo_video()
            time.sleep(1)  # Piccola pausa per assicurarsi che il processo sia terminato
            
    except KeyboardInterrupt:
        print("\nUscita dal programma...")
        termina_processo_video()

if __name__ == "__main__":
    main()