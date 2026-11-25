import re
import requests
from mutagen.oggopus import OggOpus
from musicbrainz import buscar_datos

PALABRAS_BASURA = [
    "official", "oficial", "video", "videoclip", "audio",
    "lyric", "lyrics", "letra", "hd", "hq", "4k","version","original"
]

def enriquecer(audio, nombre_limpio, duracion_s):
    """Mejora las etiquetas con MusicBrainz. Devuelve True si lo logró."""
    artista, titulo = nombre_limpio.split(" - ", 1)
    primer_artista = (separar_artistas(artista) or [artista])[0]
    try:
        datos = buscar_datos(primer_artista, titulo.strip(), duracion_s)
    except requests.RequestException as e:
        print(f"   ⚠️ MusicBrainz no respondió: {e}")
        return "error"
    if datos is None:
        print("Sin Coincidencia en MusicBrainz.")
        return "sin_coincidencia"

    if datos["artistas"]:
        audio["artist"] = datos["artistas"]
    audio["title"] = [datos["titulo"]]
    if datos["album"]:
        audio["album"] = [datos["album"]]
    if datos["anio"]:
        audio["date"] = [datos["anio"]]
    audio["musicbrainz_trackid"] = [datos["mbid"]]
    return "ok"

def limpiar_titulo(titulo):
    palabras = "|".join(PALABRAS_BASURA)
    patron = rf"\s*[\(\[][^)\]]*\b(?:{palabras})\b[^)\]]*[\)\]]"
    return re.sub(patron, "", titulo, flags=re.IGNORECASE).strip()

def separar_artistas(texto):
    """Divide 'A ft B', 'A feat. B' o 'A x B' en una lista de artistas."""
    artistas = re.split(
        r"\s*,\s*|\s+(?:ft\.?|feat\.?|featuring|x)\s+",
        texto,
        flags=re.IGNORECASE,
    )
    return [a.strip() for a in artistas if a.strip()]

def automatico(audio, archivo):
    nombre_limpio = limpiar_titulo(archivo.stem)
    if " - " not in nombre_limpio:
        return None
    artista, titulo = nombre_limpio.split(" - ", 1)
    audio["artist"] = separar_artistas(artista)
    audio["title"] = [titulo.strip()]
    return nombre_limpio

def editar_metadatos(CARPETA_DESCARGAS, usar_musicbrainz=False):
    archivos = sorted(CARPETA_DESCARGAS.glob("*.opus"))
    if not archivos:
        print("No hay archivos .opus en la carpeta.")
        return

    corregidos = con_musicbrainz = ya_listos = 0
    omitidos = []
    for archivo in archivos:
        audio = OggOpus(str(archivo))

        if "musicbrainz_trackid" in audio:
            ya_listos += 1
            continue

        nombre_limpio = automatico(audio, archivo)
        if nombre_limpio is None:
            omitidos.append(archivo.name)
            continue

        if usar_musicbrainz:
            print(f"Consultando MusicBrainz: {nombre_limpio}")
            estado = enriquecer(audio, nombre_limpio, audio.info.length)
            if estado == "ok":
                con_musicbrainz += 1
                fallos_seguidos = 0
            elif estado == "error":
                fallos_seguidos += 1
                if fallos_seguidos >= 3:
                    print("⚠️ Demasiados fallos seguidos: se continúa sin MusicBrainz.")
                    usar_musicbrainz = False

        audio.save()
        corregidos += 1

        nuevo = archivo.with_stem(nombre_limpio)
        if nuevo == archivo:
            continue
        if nuevo.exists():
            print(f"Ya existe un archivo con el nombre {nuevo.name}. Se omitirá la renombración.")
        else:
            archivo.rename(nuevo)

    print(f"\n✅ Corregidos: {corregidos}  (con MusicBrainz: {con_musicbrainz})")
    print(f"⏭️ Ya completos: {ya_listos}")
    if omitidos:
        print("⚠️ Sin formato 'Artista - Título' (no se tocaron):")
        for nombre in omitidos:
            print(f"   - {nombre}")