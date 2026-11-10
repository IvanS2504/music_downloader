import logging
import yt_dlp
from pathlib import Path
from correccion_automatica import editar_metadatos

BASE = Path(__file__).resolve().parent
CARPETA_DESCARGAS = BASE / "downloads"
ARCHIVO_LINKS = BASE / "links.txt"
ARCHIVO_LOG = BASE / "historial_descargas.log"
ARCHIVO_HISTORIAL = BASE / "archivo_descargas.txt"

# Configuracion logs
logging.basicConfig(
    filename=ARCHIVO_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    {"key": "EmbedThumbnail"},
    ],
    "download_archive": str(ARCHIVO_HISTORIAL),
}

def procesar_descarga(url):
    """Procesa una URL de forma individual."""
    try:
        print(f"\nBuscando: {url}")
        with yt_dlp.YoutubeDL(OPCIONES) as ydl:
            info = ydl.extract_info(url, download=True)
        if info is None:
            print("Ya estaba descargada")
            logging.info(f"Omitida, ya estaba en historial: {url}")
            return "omitida"
        
        titulo = info.get('title') or "Sin título"
        print(f"-> Descargado: {titulo}")
        logging.info(f"Descarga exitosa: {titulo} ({url})")
        return "ok"

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"No se pudo descargar URL {url}: {e}")
        print(f"[❌ Error de descarga]: {url}")
        return "fallida"

    except Exception as e:
        logging.error(f"Error inesperado con '{url}': {e}")
        print("[❌ Error]: Revisa el log.")
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

def op_url_download():
    url = input("Ingrese url: ").strip()
    if url:
        procesar_descarga(url)

def op_lote_links():
    """Procesa varios links desde un archivo txt"""
    if not ARCHIVO_LINKS.exists():
        print(f"\n[⚠️ Atención]: No se encontró el archivo '{ARCHIVO_LINKS}' en la carpeta del proyecto.")
        print("Crea un archivo llamado 'links.txt' y pega un enlace por línea.")
        return
    
    print(f"\nLeyendo enlaces desde '{ARCHIVO_LINKS}'...")
    
    with open(ARCHIVO_LINKS, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    total = len(urls)
    if total == 0:
        print("El archivo 'links.txt' está vacío.")
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
        print("  3. Buscar en YouTube y descargar")
        print("  4. Corregir metadatos(titulo, artista) y nombre del archivo")
        print("  5. Salir")
        
        opcion = input("\nElige una opción (1, 2, 3, 4 o 5): ").strip()
        
        if opcion == '5' or opcion.lower() in ['salir', 'q', 'exit']:
            print("¡Hasta luego! Cerrando programa...")
            break

        elif opcion == '1':
            op_url_download()

        elif opcion == '2':
            op_lote_links()

        elif opcion == '3':
            op_search_download()

        elif opcion == '4':
            op_metadata_correction()
        else:
            print("Opción no válida. Por favor, elige 1, 2, 3, 4 o 5.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[⚠️ Interrupción]: Aplicación cancelada por el usuario.")