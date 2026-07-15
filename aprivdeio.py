import json
import os
import secrets
import subprocess

ESTENSIONI_VIDEO = (".mp4", ".avi", ".mkv", ".mov", ".wmv")
TAG_FILE = "video_tags.json"
VIDEO_PLAYERS = ("vlc.exe", "wmplayer.exe", "potplayer.exe", "mpc-hc64.exe", "mpc-hc.exe")
# Se True, durante lo skip chiude i player (piu lento ma piu pulito).
# Se False, lo skip e' immediato e apre direttamente il prossimo video.
CHIUDI_PLAYER_NELLO_SKIP = False


def trova_video(cartella):
    """Trova tutti i file video nella cartella e sottocartelle."""
    file_video = []
    for root, _, files in os.walk(cartella):
        for file in files:
            if file.lower().endswith(ESTENSIONI_VIDEO):
                file_video.append(os.path.join(root, file))
    return sorted(file_video)


def normalizza_tag(tag):
    return tag.strip().lower()


def parse_tag_input(raw):
    tags = []
    for elemento in raw.split(","):
        pulito = normalizza_tag(elemento)
        if pulito:
            tags.append(pulito)
    return sorted(set(tags))


def carica_tags(path_file):
    if not os.path.exists(path_file):
        return {}

    try:
        with open(path_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        print("Attenzione: file tag non valido. Inizio con archivio vuoto.")
        return {}

    if not isinstance(data, dict):
        return {}

    tags = {}
    for video, valori in data.items():
        if isinstance(video, str) and isinstance(valori, list):
            tags[video] = sorted({normalizza_tag(v) for v in valori if isinstance(v, str) and normalizza_tag(v)})
    return tags


def salva_tags(path_file, tags_db):
    with open(path_file, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)


def termina_processo_video():
    """Termina i processi più comuni dei player video usando taskkill."""
    for player in VIDEO_PLAYERS:
        subprocess.run(
            f"taskkill /F /IM {player}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def apri_video(video_path):
    subprocess.Popen(f'start "" "{video_path}"', shell=True)


def prossimo_video_casuale(tutti_video, video_riprodotti):
    """Restituisce un video casuale non ancora visto."""
    video_disponibili = list(set(tutti_video) - set(video_riprodotti))

    if not video_disponibili:
        print("Hai visto tutti i video. Resetto la cronologia.")
        video_disponibili = list(tutti_video)
        video_riprodotti.clear()

    video_casuale = secrets.choice(video_disponibili)
    video_riprodotti.append(video_casuale)
    return video_casuale


def mostra_video_con_indice(videos):
    for i, video in enumerate(videos, start=1):
        print(f"{i}. {os.path.basename(video)}")


def scegli_video(videos):
    if not videos:
        print("Nessun video disponibile.")
        return None

    mostra_video_con_indice(videos)
    scelta = input("Scegli numero video (invio per annullare): ").strip()
    if not scelta:
        return None
    if not scelta.isdigit():
        print("Scelta non valida.")
        return None

    idx = int(scelta) - 1
    if idx < 0 or idx >= len(videos):
        print("Indice fuori range.")
        return None
    return videos[idx]


def aggiungi_tag_a_video(video_path, tags_db):
    nome = os.path.basename(video_path)
    esistenti = tags_db.get(video_path, [])
    print(f"\nVideo: {nome}")
    print(f"Tag attuali: {', '.join(esistenti) if esistenti else 'nessuno'}")

    raw = input("Inserisci tag separati da virgola: ").strip()
    nuovi_tag = parse_tag_input(raw)

    if not nuovi_tag:
        print("Nessun tag valido inserito.")
        return False

    unione = sorted(set(esistenti).union(nuovi_tag))
    tags_db[video_path] = unione
    print(f"Tag salvati: {', '.join(unione)}")
    return True


def gestisci_comando_riproduzione(cmd, video_corrente, tagged_nel_turno, tags_db, tags_path):
    """Ritorna: (azione, nuovo_tagged_nel_turno)."""
    if cmd == "t":
        if aggiungi_tag_a_video(video_corrente, tags_db):
            salva_tags(tags_path, tags_db)
            return "continua", True
        return "continua", tagged_nel_turno

    if cmd == "s":
        if not tagged_nel_turno:
            print("Prima di skippare devi inserire almeno un tag per questo video.")
            return "continua", tagged_nel_turno
        if CHIUDI_PLAYER_NELLO_SKIP:
            termina_processo_video()
        return "prossimo_video", tagged_nel_turno

    if cmd == "x":
        termina_processo_video()
        return "torna_menu", tagged_nel_turno

    print("Comando non valido. Usa t, s oppure x.")
    return "continua", tagged_nel_turno


def riproduzione_con_tag_obbligatorio(tutti_video, video_riprodotti, tags_db, tags_path):
    """Riproduce video in ciclo: lo skip e' consentito solo dopo aver aggiunto almeno un tag."""
    print("\nModalita riproduzione attiva. Premi CTRL+C per tornare al menu.")

    try:
        while True:
            video_corrente = prossimo_video_casuale(tutti_video, video_riprodotti)
            tagged_nel_turno = False

            print(f"\nIn riproduzione: {os.path.basename(video_corrente)}")
            print(f"Percorso: {video_corrente}")
            print(
                "Comandi: [t] aggiungi tag, [s] skip video (solo dopo almeno un tag), [x] chiudi player e torna al menu"
            )
            apri_video(video_corrente)

            while True:
                cmd = input("Comando: ").strip().lower()
                azione, tagged_nel_turno = gestisci_comando_riproduzione(
                    cmd, video_corrente, tagged_nel_turno, tags_db, tags_path
                )
                if azione == "prossimo_video":
                    break
                if azione == "torna_menu":
                    return

    except KeyboardInterrupt:
        print("\nRitorno al menu principale.")
        termina_processo_video()


def trova_video_non_taggati(tutti_video, tags_db):
    non_taggati = []
    for video in tutti_video:
        if not tags_db.get(video):
            non_taggati.append(video)
    return non_taggati


def riproduzione_discovery(tutti_video, tags_db, tags_path):
    """Riproduce casualmente solo video senza tag finche non vengono classificati."""
    print("\nModalita Discovery attiva. Solo video senza tag. Premi CTRL+C per tornare al menu.")

    try:
        while True:
            candidati = trova_video_non_taggati(tutti_video, tags_db)
            if not candidati:
                print("Discovery completata: tutti i video hanno almeno un tag.")
                termina_processo_video()
                return

            video_corrente = secrets.choice(candidati)
            tagged_nel_turno = False

            print(f"\nIn discovery: {os.path.basename(video_corrente)}")
            print(f"Rimasti senza tag: {len(candidati)}")
            print(f"Percorso: {video_corrente}")
            print(
                "Comandi: [t] aggiungi tag, [s] skip video (solo dopo almeno un tag), [x] chiudi player e torna al menu"
            )
            apri_video(video_corrente)

            while True:
                cmd = input("Comando: ").strip().lower()
                azione, tagged_nel_turno = gestisci_comando_riproduzione(
                    cmd, video_corrente, tagged_nel_turno, tags_db, tags_path
                )
                if azione == "prossimo_video":
                    break
                if azione == "torna_menu":
                    return

    except KeyboardInterrupt:
        print("\nRitorno al menu principale.")
        termina_processo_video()


def cerca_video_per_tag(tutti_video, tags_db):
    ricerca_raw = input("Inserisci uno o piu tag (separati da virgola): ").strip()
    richiesti = parse_tag_input(ricerca_raw)

    if not richiesti:
        print("Nessun tag valido inserito.")
        return

    risultati = []
    for video in tutti_video:
        video_tags = set(tags_db.get(video, []))
        if set(richiesti).issubset(video_tags):
            risultati.append(video)

    print(f"\nRisultati per tag {', '.join(richiesti)}:")
    if not risultati:
        print("Nessun video trovato.")
        return

    mostra_video_con_indice(risultati)


def mostra_tag_per_video(tutti_video, tags_db):
    video = scegli_video(tutti_video)
    if not video:
        return

    tags = tags_db.get(video, [])
    print(f"\n{os.path.basename(video)}")
    print(f"Tag: {', '.join(tags) if tags else 'nessuno'}")


def menu_principale(cartella_video):
    tutti_video = trova_video(cartella_video)
    if not tutti_video:
        print("Nessun file video trovato nella cartella indicata.")
        return

    tags_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), TAG_FILE)
    tags_db = carica_tags(tags_path)
    video_riprodotti = []

    while True:
        print("\n=== MENU VIDEO TAG ===")
        print("1) Riproduci video casuali (tag obbligatorio prima dello skip)")
        print("2) Discovery (solo video non ancora taggati)")
        print("3) Aggiungi/modifica tag a un video")
        print("4) Cerca video per tag")
        print("5) Mostra tag di un video")
        print("6) Aggiorna scansione cartella video")
        print("0) Esci")

        scelta = input("Scelta: ").strip()

        if scelta == "1":
            riproduzione_con_tag_obbligatorio(tutti_video, video_riprodotti, tags_db, tags_path)
        elif scelta == "2":
            riproduzione_discovery(tutti_video, tags_db, tags_path)
        elif scelta == "3":
            video = scegli_video(tutti_video)
            if video and aggiungi_tag_a_video(video, tags_db):
                salva_tags(tags_path, tags_db)
        elif scelta == "4":
            cerca_video_per_tag(tutti_video, tags_db)
        elif scelta == "5":
            mostra_tag_per_video(tutti_video, tags_db)
        elif scelta == "6":
            tutti_video = trova_video(cartella_video)
            print(f"Scansione aggiornata. Trovati {len(tutti_video)} video.")
        elif scelta == "0":
            print("Uscita dal programma.")
            termina_processo_video()
            return
        else:
            print("Scelta non valida.")


def main():
    default_cartella = r"D:\temp"
    cartella_video = input(
        f"Cartella video (invio per default: {default_cartella}): "
    ).strip() or default_cartella

    if not os.path.isdir(cartella_video):
        print("La cartella indicata non esiste.")
        return

    menu_principale(cartella_video)


if __name__ == "__main__":
    main()