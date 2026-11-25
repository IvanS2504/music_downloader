import re
from mutagen.oggopus import OggOpus

PALABRAS_BASURA = [
    "official", "oficial", "video", "videoclip", "audio",
    "lyric", "lyrics", "letra", "hd", "hq", "4k","version","original"
]

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

def normalizar_guiones(texto):
    """Convierte guiones largos (– —) entre espacios en un guion normal."""
    return re.sub(r"\s+[\u2012-\u2015\u2212]\s+", " - ", texto)

def automatico(audio, archivo):
    nombre_limpio = normalizar_guiones(limpiar_titulo(archivo.stem))
    if " - " not in nombre_limpio:
        return None
    artista, titulo = nombre_limpio.split(" - ", 1)
    audio["artist"] = separar_artistas(artista)
    audio["title"] = [titulo.strip()]
    return nombre_limpio

def editar_metadatos(carpeta):
    """Corrige etiquetas y nombres de los .opus. Devuelve un resumen."""
    resumen = {"corregidos": 0, "renombrados": 0, "omitidos": [], "conflictos": []}

    for archivo in sorted(carpeta.glob("*.opus")):
        audio = OggOpus(str(archivo))
        nombre_limpio = automatico(audio, archivo)
        if nombre_limpio is None:
            resumen["omitidos"].append(archivo.name)
            continue

        audio.save()
        resumen["corregidos"] += 1

        nuevo = archivo.with_stem(nombre_limpio)
        if nuevo == archivo:
            continue
        if nuevo.exists():
            resumen["conflictos"].append(f"{archivo.name} → ya existe {nuevo.name}")
        else:
            archivo.rename(nuevo)
            resumen["renombrados"] += 1

    return resumen