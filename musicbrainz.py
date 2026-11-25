import time
import requests


USER_AGENT = "MusicDownloader/0.1 (https://github.com/IvanS2504/music_downloader)"
URL_BUSQUEDA = "https://musicbrainz.org/ws/2/recording"
SCORE_MINIMO = 90 
TOLERANCIA_S = 5 

_ultima_llamada = 0.0


def _esperar_turno():
    """MusicBrainz permite como máximo una petición por segundo."""
    global _ultima_llamada
    espera = 1.1 - (time.monotonic() - _ultima_llamada)
    if espera > 0:
        time.sleep(espera)
    _ultima_llamada = time.monotonic()


def _escapar(texto):
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def buscar_grabaciones(artista, titulo):
    """Consulta MusicBrainz y devuelve la lista cruda de grabaciones."""
    _esperar_turno()
    consulta = f'recording:"{_escapar(titulo)}" AND artist:"{_escapar(artista)}"'
    intentos = 3
    for intento in range(1, intentos + 1):
        _esperar_turno()
        respuesta = requests.get(
            URL_BUSQUEDA,
            params={"query": consulta, "fmt": "json", "limit": 10},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if respuesta.status_code == 503 and intento < intentos:
            time.sleep(5 * intento)          # espera 5 s, luego 10 s...
            continue
        respuesta.raise_for_status()
        return respuesta.json().get("recordings", [])


def elegir_mejor(grabaciones, duracion_s=None):
    """Elige la grabación más convincente, o None si ninguna lo es."""
    candidatas = [g for g in grabaciones if g.get("score", 0) >= SCORE_MINIMO]
    if duracion_s:
        candidatas = [
            g for g in candidatas
            if g.get("length") and abs(g["length"] / 1000 - duracion_s) <= TOLERANCIA_S
        ]
    if not candidatas:
        return None
    if duracion_s:
        return min(candidatas, key=lambda g: abs(g["length"] / 1000 - duracion_s))
    return candidatas[0]


def _elegir_album(releases):
    """Álbum = la edición oficial más antigua."""
    oficiales = [r for r in releases if r.get("status") == "Official" and r.get("date")]
    if not oficiales:
        return None
    return min(oficiales, key=lambda r: r["date"])["title"]


def normalizar(grabacion):
    """Convierte la respuesta de MusicBrainz en un diccionario simple."""
    artistas = [
        c["artist"]["name"]
        for c in grabacion.get("artist-credit", [])
        if "artist" in c
    ]
    fecha = grabacion.get("first-release-date") or ""
    return {
        "mbid": grabacion["id"],
        "titulo": grabacion["title"],
        "artistas": artistas,
        "anio": fecha[:4] or None,
        "album": _elegir_album(grabacion.get("releases", [])),
    }


def buscar_datos(artista, titulo, duracion_s=None):
    """Devuelve datos normalizados, o None si no hay coincidencia convincente."""
    grabacion = elegir_mejor(buscar_grabaciones(artista, titulo), duracion_s)
    return normalizar(grabacion) if grabacion else None