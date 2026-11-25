from musicbrainz import elegir_mejor, normalizar

ORIGINAL = {
    "id": "1", "title": "Song", "score": 100, "length": 215000,
    "artist-credit": [{"name": "A", "artist": {"name": "Artist A"}}],
    "first-release-date": "2001-05-12",
    "releases": [
        {"title": "Compilation", "status": "Official", "date": "2010"},
        {"title": "Original Album", "status": "Official", "date": "2001-05-12"},
        {"title": "Promo", "status": "Promotion", "date": "2000"},
    ],
}
EN_VIVO = {"id": "2", "title": "Song (Live)", "score": 100, "length": 340000,
           "artist-credit": [], "releases": []}
POCO_RELEVANTE = {**ORIGINAL, "id": "3", "score": 70}

def test_elige_por_duracion():
    assert elegir_mejor([EN_VIVO, ORIGINAL], 214)["id"] == "1"

def test_descarta_score_bajo():
    assert elegir_mejor([POCO_RELEVANTE], 215) is None

def test_none_si_la_duracion_no_coincide():
    assert elegir_mejor([EN_VIVO, ORIGINAL], 600) is None

def test_normalizar():
    datos = normalizar(ORIGINAL)
    assert datos["album"] == "Original Album"
    assert datos["anio"] == "2001"
    assert datos["artistas"] == ["Artist A"]