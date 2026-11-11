from pathlib import Path

BASE = Path(__file__).resolve().parent
CARPETA_DESCARGAS = BASE / "downloads"
ARCHIVO_LINKS = BASE / "links.txt"
ARCHIVO_LOG = BASE / "historial_descargas.log"
ARCHIVO_HISTORIAL = BASE / "archivo_descargas.txt"
DESCARGAS_FALLIDAS = BASE / "descargas_fallidas.txt"