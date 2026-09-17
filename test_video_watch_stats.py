import json
import time

from aprivdeio import aggiungi_tempo_guardato, classifica_video_per_tempo, riprendi_tempo_da_sessione_attiva


def test_aggiorna_tempo_guardato_somma_secondi():
    db = {}

    aggiungi_tempo_guardato(db, "video_a.mp4", 10)
    aggiungi_tempo_guardato(db, "video_a.mp4", 25)

    assert db["video_a.mp4"] == 35


def test_classifica_video_per_tempo_ordina_descrescente():
    db = {
        "video_b.mp4": 120,
        "video_a.mp4": 60,
        "video_c.mp4": 200,
    }

    classifica = classifica_video_per_tempo(db)

    assert [video for video, _ in classifica] == ["video_c.mp4", "video_b.mp4", "video_a.mp4"]


def test_riprendi_tempo_da_sessione_attiva_aggiunge_secondi_salvati(tmp_path):
    db = {}
    session_path = tmp_path / "watch_session.json"
    stats_path = tmp_path / "watch_stats.json"

    with open(session_path, "w", encoding="utf-8") as f:
        json.dump({"video_path": "video_a.mp4", "started_at": time.time() - 30}, f)

    riprendi_tempo_da_sessione_attiva(db, str(session_path), str(stats_path))

    assert db["video_a.mp4"] >= 25
    assert not session_path.exists()
