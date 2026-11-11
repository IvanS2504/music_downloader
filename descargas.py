import logging
import yt_dlp

from config import CARPETA_DESCARGAS, ARCHIVO_HISTORIAL
from historial import registrar_fallida, quitar_fallida

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
