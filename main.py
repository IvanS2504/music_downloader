import logging

from config import ARCHIVO_LINKS, ARCHIVO_LOG, CARPETA_DESCARGAS, DESCARGAS_FALLIDAS
from descargas import buscar_videos_youtube, formatear_duracion, procesar_descarga
from historial import cargar_historial
from metadatos import editar_metadatos

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
    logging.basicConfig(
        filename=ARCHIVO_LOG,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
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