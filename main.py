import logging
import yt_dlp
from pathlib import Path

BASE = Path(__file__).resolve().parent
CARPETA_DESCARGAS = BASE / "downloads"
ARCHIVO_LINKS = BASE / "links.txt"
ARCHIVO_LOG = BASE / "historial_descargas.log"
ARCHIVO_HISTORIAL = BASE / "archivo_descargas.txt"

# Configuramos los logs
logging.basicConfig(
    filename=ARCHIVO_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    """Procesa una URL de forma individual. Devuelve True si tuvo éxito."""
    try:
        print(f"\nBuscando: {url}")
        with yt_dlp.YoutubeDL(OPCIONES) as ydl:
            info = ydl.extract_info(url, download=True)
            
        titulo = info.get('title') or "Sin título"
        print(f"-> Descargado: {titulo}")
        logging.info(f"Descarga exitosa: {titulo} ({url})")
        return True

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"No se pudo descargar URL {url}: {e}")
        print(f"[❌ Error de descarga]: {url}")
        return False

    except Exception as e:
        logging.error(f"Error inesperado con '{url}': {e}")
        print("[❌ Error]: Revisa el log.")
        return False


def buscar_videos_youtube(consulta, max_resultados=10):
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
                "url": url,
            })

        return videos
    except yt_dlp.utils.DownloadError as error:
        logging.error(f"No se pudo buscar en YouTube '{consulta}': {error}")
        print("[❌ Error de búsqueda]: No se pudieron obtener resultados de YouTube.")
    except Exception as error:
        logging.error(f"Error inesperado al buscar '{consulta}': {error}")
        print("[❌ Error]: Ocurrió un problema con la búsqueda. Revisa el log.")
    return []

def main():
    print("=== 🎵 Iniciando Descargador de Música ===")

    while True:
        print("\nOpciones:")
        print("  1. Descargar una URL individual")
        print("  2. Descargar desde archivo 'links.txt'")
        print("  3. Buscar en YouTube y descargar")
        print("  4. Salir")
        
        opcion = input("\nElige una opción (1, 2, 3 o 4): ").strip()
        
        if opcion == '4' or opcion.lower() in ['salir', 'q', 'exit']:
            print("¡Hasta luego! Cerrando programa...")
            break

        elif opcion == '1':
            url = input("Ingrese url: ").strip()
            if url:
                procesar_descarga(url)

        elif opcion == '2':

            if not ARCHIVO_LINKS.exists():
                print(f"\n[⚠️ Atención]: No se encontró el archivo '{ARCHIVO_LINKS}' en la carpeta del proyecto.")
                print("Crea un archivo llamado 'links.txt' y pega un enlace por línea.")
                continue
                
            print(f"\nLeyendo enlaces desde '{ARCHIVO_LINKS}'...")
            
            with open(ARCHIVO_LINKS, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                
            total = len(urls)
            if total == 0:
                print("El archivo 'links.txt' está vacío.")
                continue
                
            print(f"Se encontraron {total} enlaces para procesar.\n")
            
            exitosas = 0
            fallidas = 0
            
            for i, url in enumerate(urls, 1):
                print(f"\n--- Procesando canción {i} de {total} ---")
                exito = procesar_descarga(url)
                if exito:
                    exitosas += 1
                else:
                    fallidas += 1
                    
            print("\n=== Lote finalizado ===")
            print(f"✅ Exitosas: {exitosas}")
            print(f"❌ Fallidas: {fallidas}")
            logging.info(f"Lote finalizado. Exitosas: {exitosas}, Fallidas: {fallidas}")

        elif opcion == '3':
            consulta = input("¿Qué canción o artista quieres buscar?: ").strip()
            if not consulta:
                print("La búsqueda no puede estar vacía.")
                continue

            videos = buscar_videos_youtube(consulta)
            if not videos:
                print("No se encontraron resultados.")
                continue

            print("\nResultados de YouTube:")
            for indice, video in enumerate(videos, 1):
                print(f"  {indice}. {video['title']} — {video['channel']}")

            seleccion = input(
                "\nElige el número del resultado para descargar (0 para cancelar): "
            ).strip()
            if seleccion == "0":
                continue
            if not seleccion.isdecimal() or not 1 <= int(seleccion) <= len(videos):
                print("Selección no válida.")
                continue

            procesar_descarga(videos[int(seleccion) - 1]["url"])

        else:
            print("Opción no válida. Por favor, elige 1, 2, 3 o 4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[⚠️ Interrupción]: Aplicación cancelada por el usuario.")