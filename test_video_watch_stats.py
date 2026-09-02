from aprivdeio import aggiungi_tempo_guardato, classifica_video_per_tempo


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
