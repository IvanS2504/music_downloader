from pathlib import Path
import pytest
from metadatos import limpiar_titulo, separar_artistas, automatico

@pytest.mark.parametrize("entrada, esperado", [
    ("Artist - Song (Official Video)", "Artist - Song"),
    ("Artist - Song [HD]", "Artist - Song"),
    ("Artist - Song (Lyric Video)", "Artist - Song"),
    ("Artist - Song (Video Oficial)", "Artist - Song"),
    ("Artist - Song (Audiophile Mix)", "Artist - Song (Audiophile Mix)"),
])
def test_limpiar_titulo(entrada, esperado):
    assert limpiar_titulo(entrada) == esperado

def test_separa_varios_artistas():
    assert separar_artistas("A ft B x C, D") == ["A", "B", "C", "D"]

def test_artista_unico():
    assert separar_artistas("Cher") == ["Cher"]

def test_automatico_rellena_etiquetas():
    audio = {}   # un diccionario basta como sustituto del archivo de audio
    archivo = Path("Artist A x Artist B - Song (Official Video).opus")
    nombre = automatico(audio, archivo)
    assert nombre == "Artist A x Artist B - Song"
    assert audio["artist"] == ["Artist A", "Artist B"]
    assert audio["title"] == ["Song"]

def test_automatico_sin_formato():
    assert automatico({}, Path("Solo un titulo.opus")) is None