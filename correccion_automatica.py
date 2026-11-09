import re
from mutagen.oggopus import OggOpus

def separar_artistas(texto):
    """Divide 'A ft B', 'A feat. B' o 'A x B' en una lista de artistas."""
    artistas = re.split(
        r"\s*,\s*|\s+(?:ft\.?|feat\.?|featuring|x)\s+",
        texto,
        flags=re.IGNORECASE,
    )
    return [a.strip() for a in artistas if a.strip()]

def limpiar_titulo(titulo):
    return re.sub(
        r"\s*[\(\[][^)\]]*(official|video|audio|lyrics|letra|hd|hq)[^)\]]*[\)\]]",
        "",
        titulo,
        flags=re.IGNORECASE,
    ).strip()

def automatico(audio, archivo):
    nombre_limpio = limpiar_titulo(archivo.stem)
    if " - " not in nombre_limpio:
        return None
    artista, titulo = archivo.stem.split(" - ", 1)
    audio["artist"] = separar_artistas(artista)
    audio["title"] = [titulo.strip()]
    return nombre_limpio

def editar_metadatos(CARPETA_DESCARGAS):
    archivos = sorted(CARPETA_DESCARGAS.glob("*.opus"))
    if not archivos:
        print("No hay archivos .opus en la carpeta.")
        return

    corregidos = 0
    omitidos = []
    for archivo in archivos:
        audio = OggOpus(str(archivo))
        nombre_limpio = automatico(audio, archivo)
        if nombre_limpio is None:
            omitidos.append(archivo.name)
            continue

        audio.save()
        corregidos += 1

        nuevo = archivo.with_stem(nombre_limpio)
        if nuevo == archivo:
            continue
        if nuevo.exists():
            print(f"Ya existe un archivo con el nombre {nuevo.name}. Se omitirá la renombración.")
        else:
            archivo.rename(nuevo)

    print(f"\n✅ Corregidos: {corregidos}")
    if omitidos:
        print("⚠️ Sin formato 'Artista - Título' (no se tocaron):")
        for nombre in omitidos:
            print(f"   - {nombre}")