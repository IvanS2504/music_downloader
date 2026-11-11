import logging
import yt_dlp
from pathlib import Path
from correccion_automatica import editar_metadatos

BASE = Path(__file__).resolve().parent
CARPETA_DESCARGAS = BASE / "downloads"
ARCHIVO_LINKS = BASE / "links.txt"
ARCHIVO_LOG = BASE / "historial_descargas.log"
ARCHIVO_HISTORIAL = BASE / "archivo_descargas.txt"
DESCARGAS_FALLIDAS = BASE / "descargas_fallidas.txt"

# Configuracion logs
logging.basicConfig(
    filename=ARCHIVO_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def mostrar_progreso(d):
    """Hook de yt-dlp: dibuja una barra mientras se descarga."""
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            fraccion = d.get("downloaded_bytes", 0) / total
            llenos = int(fraccion * 30)
            barra = "█" * llenos + "░" * (30 - llenos)
            print(f"\r   [{barra}] {fraccion:6.1%}", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r   [{'█' * 30}] 100.0%  Descarga completa")

PASOS = {
    "ThumbnailsConvertor": "Recortando carátula a cuadrado",
    "ExtractAudio": "Extrayendo audio",
    "Metadata": "Escribiendo metadatos",
    "EmbedThumbnail": "Incrustando carátula",
    "MoveFiles": "Guardando archivo",
}

pasos_mostrados = set()

def mostrar_paso(d):
    """Hook de postprocesadores: avisa cada paso una sola vez por descarga."""
    if d["status"] != "started":
        return
    paso = d["postprocessor"]
    if paso in pasos_mostrados:
        return
    pasos_mostrados.add(paso)
    print(f"   {PASOS.get(paso, paso)}...")

#Configuracion de yt-dlp
OPCIONES = {
    "noplaylist": True,
    "format": "bestaudio/best",
    "outtmpl": str(CARPETA_DESCARGAS / "%(title)s.%(ext)s"),
    "js_runtimes": {
        "node": {}
    },
    "remote_components": ["ejs:github"],
    "writethumbnail": True,
    "postprocessors": [
    {"key": "FFmpegExtractAudio", "preferredcodec": "best"},
    {"key": "FFmpegMetadata"},
    {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
    {"key": "EmbedThumbnail"},
    ],
    "postprocessor_args": {
        "thumbnailsconvertor+ffmpeg_o": [
            "-c:v", "mjpeg",
            "-vf", "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
        ],
    },
    "download_archive": str(ARCHIVO_HISTORIAL),
    "quiet": True,
    "progress_hooks": [mostrar_progreso],
    "postprocessor_hooks": [mostrar_paso],
}

def leer_fallidas():
    if not DESCARGAS_FALLIDAS.exists():
        return []
    return DESCARGAS_FALLIDAS.read_text(encoding="utf-8").splitlines()

def registrar_fallida(url):
    """Agrega la URL a la lista de pendientes si aún no está."""
    if url not in leer_fallidas():
        with open(DESCARGAS_FALLIDAS, "a", encoding="utf-8") as f:
            f.write(url + "\n")

def quitar_fallida(url):
    """Quita la URL de la lista de pendientes (si estaba)."""
    lineas = leer_fallidas()
    if url in lineas:
        restantes = [l for l in lineas if l != url]
        texto = "\n".join(restantes) + ("\n" if restantes else "")
        DESCARGAS_FALLIDAS.write_text(texto, encoding="utf-8")

def procesar_descarga(url):
    """Procesa una URL de forma individual."""
    pasos_mostrados.clear()
    try:
        print(f"\nBuscando: {url}")
        with yt_dlp.YoutubeDL(OPCIONES) as ydl:
            info = ydl.extract_info(url, download=True)
        if info is None:
            print("Ya estaba descargada")
            logging.info(f"Omitida, ya estaba en historial: {url}")
            quitar_fallida(url)
            return "omitida"
        
        titulo = info.get('title') or "Sin título"
        print(f"-> Descargado: {titulo}")
        logging.info(f"Descarga exitosa: {titulo} ({url})")
        quitar_fallida(url)
        return "ok"

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"No se pudo descargar URL {url}: {e}")
        print(f"[❌ Error de descarga]: {url}")
        registrar_fallida(url)
        return "fallida"

    except Exception as e:
        logging.error(f"Error inesperado con '{url}': {e}")
        print("[❌ Error]: Revisa el log.")
        registrar_fallida(url)
        return "fallida"

def formatear_duracion(segundos):
    """Convierte segundos a formato H:MM:SS o M:SS."""
    if not segundos:
        return "??:??"
    horas, resto = divmod(int(segundos), 3600)
    minutos, seg = divmod(resto, 60)
    return f"{horas}:{minutos:02d}:{seg:02d}" if horas else f"{minutos}:{seg:02d}"

def cargar_historial():
    """Devuelve el conjunto de IDs de videos ya descargados."""
    if not ARCHIVO_HISTORIAL.exists():
        return set()
    with open(ARCHIVO_HISTORIAL, encoding="utf-8") as f:
        return {linea.split(maxsplit=1)[1].strip() for linea in f if " " in linea}

def buscar_videos_youtube(consulta, max_resultados=10):
    """Busca videos en YouTube y devuelve una lista de diccionarios con información."""
    try:
        opciones_busqueda = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(opciones_busqueda) as ydl:
            resultados = ydl.extract_info(
                f"ytsearch{max_resultados}:{consulta}",
                download=False
            )
        videos = []
        for resultado in resultados.get("entries") or []:
            if not resultado:
                continue
            video_id = resultado.get("id")
            url = resultado.get("webpage_url")
            if not url and video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
            if not url:
                url = resultado.get("url")
            if not url:
                continue
            videos.append({
                "title": resultado.get("title") or "Sin título",
                "channel": resultado.get("channel") or resultado.get("uploader") or "Canal desconocido",
                "duration": resultado.get("duration") or 0,
                "url": url,
                "id": video_id,
            })

        return videos
    except yt_dlp.utils.DownloadError as error:
        logging.error(f"No se pudo buscar en YouTube '{consulta}': {error}")
        print("[❌ Error de búsqueda]: No se pudieron obtener resultados de YouTube.")
    except Exception as error:
        logging.error(f"Error inesperado al buscar '{consulta}': {error}")
        print("[❌ Error]: Ocurrió un problema con la búsqueda. Revisa el log.")
    return []

def op_url_individual():
    url = input("Ingrese url: ").strip()
    if url:
        procesar_descarga(url)
    
def op_lote_links(archivo):
    """Procesa varios links desde un archivo txt"""
    if not archivo.exists():
        print(f"\n[⚠️ Atención]: No se encontró el archivo '{archivo.name}' en la carpeta del proyecto.")
        print("Crea un archivo llamado 'links.txt' y pega un enlace por línea.")
        return
    
    print(f"\nLeyendo enlaces desde '{archivo.name}'...")
    
    with open(ARCHIVO_LINKS, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    total = len(urls)
    if total == 0:
        print(f"El archivo '{archivo.name}' está vacío.")
        return
    
    print(f"Se encontraron {total} enlaces para procesar.\n")
    
    resultados = {"ok": 0, "omitida": 0, "fallida": 0}
    
    for i, url in enumerate(urls, 1):
        print(f"\n--- Procesando canción {i} de {total} ---")
        status = procesar_descarga(url)
        resultados[status] += 1
    
    print("\n=== Lote finalizado ===")
    print(f"✅ Exitosas: {resultados['ok']}")
    print(f"⏭️ Ya estaban: {resultados['omitida']}")
    print(f"❌ Fallidas: {resultados['fallida']}")
    logging.info(f"Lote finalizado. {resultados}")

def op_search_download():
    consulta = input("¿Qué canción o artista quieres buscar?: ").strip()
    if not consulta:
        print("La búsqueda no puede estar vacía.")
        return
    
    videos = buscar_videos_youtube(consulta)
    if not videos:
        print("No se encontraron resultados.")
        return
    
    print("\nResultados de YouTube:")
    historial = cargar_historial()
    for indice, video in enumerate(videos, 1):
        marca = "  ✅ Ya descargada" if video["id"] in historial else ""
        print(f"  {indice}. {video['title']} — {video['channel']} "
              f"({formatear_duracion(video['duration'])}){marca}")

    seleccion = input(
        "\nElige el número del resultado para descargar (0 para cancelar): "
    ).strip()
    if seleccion == "0":
        return
    if not seleccion.isdecimal() or not 1 <= int(seleccion) <= len(videos):
        print("Selección no válida.")
        return
    
    procesar_descarga(videos[int(seleccion) - 1]["url"])

def op_metadata_correction():
    confirmar = input(
        "Se sobrescribirán título y artista de los .opus según el nombre "
        "del archivo. ¿Continuar? (s/n): "
    ).strip().lower()
    if confirmar == "s":
        editar_metadatos(CARPETA_DESCARGAS)

def main():
    print("=== 🎵 Iniciando Descargador de Música ===")

    while True:
        print("\nOpciones:")
        print("  1. Descargar una URL individual")
        print("  2. Descargar desde archivo 'links.txt'")
        print("  3. Reintentar descargas fallidas")
        print("  4. Buscar en YouTube y descargar")
        print("  5. Corregir metadatos(titulo, artista) y nombre del archivo")
        print("  6. Salir")
        
        opcion = input("\nElige una opción (1, 2, 3, 4, 5 o 6): ").strip()
        
        if opcion == '6' or opcion.lower() in ['salir', 'q', 'exit']:
            print("¡Hasta luego! Cerrando programa...")
            break

        elif opcion == '1':
            op_url_individual()

        elif opcion == '2':
            op_lote_links(ARCHIVO_LINKS)

        elif opcion == '3':
            op_lote_links(DESCARGAS_FALLIDAS)    

        elif opcion == '4':
            op_search_download()

        elif opcion == '5':
            op_metadata_correction()
        else:
            print("Opción no válida. Por favor, elige 1, 2, 3, 4 o 5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[⚠️ Interrupción]: Aplicación cancelada por el usuario.")