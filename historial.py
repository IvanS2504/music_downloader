from config import ARCHIVO_HISTORIAL, DESCARGAS_FALLIDAS

def leer_fallidas(archivo=DESCARGAS_FALLIDAS):
    if not archivo.exists():
        return []
    return archivo.read_text(encoding="utf-8").splitlines()

def registrar_fallida(url, archivo=DESCARGAS_FALLIDAS):
    """Agrega la URL a la lista de pendientes si aún no está."""
    if url not in leer_fallidas(archivo):
        with open(archivo, "a", encoding="utf-8") as f:
            f.write(url + "\n")

def quitar_fallida(url, archivo=DESCARGAS_FALLIDAS):
    """Quita la URL de la lista de pendientes (si estaba)."""
    lineas = leer_fallidas(archivo)
    if url in lineas:
        restantes = [l for l in lineas if l != url]
        texto = "\n".join(restantes) + ("\n" if restantes else "")
        archivo.write_text(texto, encoding="utf-8")

def cargar_historial(archivo=ARCHIVO_HISTORIAL):
    """Devuelve el conjunto de IDs de videos ya descargados."""
    if not archivo.exists():
        return set()
    with open(archivo, encoding="utf-8") as f:
        return {linea.split(maxsplit=1)[1].strip() for linea in f if " " in linea}
