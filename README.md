# 🎵 Music Downloader

![Tests](https://github.com/IvanS2504/music_downloader/actions/workflows/test.yml/badge.svg)

Descargador de música personal basado en [yt-dlp](https://github.com/yt-dlp/yt-dlp),
con una interfaz web local (Django) y una interfaz de consola.
Proyecto de aprendizaje: lo desarrollé paso a paso, con pruebas automáticas y control de versiones desde el principio.

![Buscador](docs/captura-buscador.png)

## Funciones

**Búsqueda y descarga**
- Búsqueda en YouTube con duración y marca de «ya descargada».
- Descargas en cola con barra de progreso (interfaz web).
- Audio en su formato original, sin recodificar (normalmente Opus), con la
  carátula recortada a cuadrado e incrustada.

**Metadatos**
- Corrige artista(s) y título a partir del nombre del archivo y lo renombra.
- Limpia sufijos como «(Official Video)» o «[HD]» sin tocar títulos legítimos.
- Reconoce varios artistas (`ft`, `feat`, `x`, coma) y distintos tipos de guion.

**Robustez**
- Historial para no repetir descargas.
- Lista de URLs fallidas, con opción de reintento desde la consola.
- Errores registrados en un archivo de log.

## Requisitos

- Python 3.x (desarrollado con 3.14)
- [ffmpeg](https://ffmpeg.org/) y [Node.js](https://nodejs.org/) instalados y en el PATH
  (yt-dlp usa Node para resolver los desafíos de YouTube)

## Instalación (Windows, PowerShell)

```powershell
git clone https://github.com/TU_USUARIO/music_downloader.git
cd music_downloader
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
```

## Uso

Con doble clic:

| Archivo | Qué hace |
|---|---|
| `iniciar_web.bat` | Arranca el servidor local y abre http://127.0.0.1:8000 |
| `iniciar_consola.bat` | Abre el menú de consola |
| `actualizar.bat` | Actualiza el código, las dependencias y yt-dlp |

O desde PowerShell:

```powershell
.venv\Scripts\python.exe manage.py runserver   # interfaz web
.venv\Scripts\python.exe main.py               # interfaz de consola
```

La interfaz web tiene dos páginas: **Buscar** (con descarga y progreso) y
**Corregir metadatos**. La consola ofrece además descarga por URL, por lote
desde `links.txt` y reintento de fallidas. Las canciones se guardan en `downloads/`.

> YouTube cambia su reproductor con frecuencia y yt-dlp se rompe cada tanto.
> Si las descargas empiezan a fallar, ejecuta `actualizar.bat`.

## Pruebas y calidad

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
```

Las pruebas no necesitan internet y se ejecutan automáticamente en cada push
con GitHub Actions.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `main.py` | Menú de consola |
| `descargas.py` | Opciones de yt-dlp, descarga y búsqueda |
| `trabajos.py` | Cola de descargas en segundo plano |
| `historial.py` | Historial de descargas y URLs fallidas |
| `metadatos.py` | Limpieza de nombres y etiquetas |
| `config.py` | Rutas del proyecto |
| `sitio/`, `buscador/` | Proyecto y app de Django (interfaz web) |
| `tests/` | Pruebas con pytest |
| `.github/workflows/` | Integración continua |

## Decisiones de diseño

- **Lógica separada de la presentación.** Las funciones devuelven datos y no
  imprimen; la consola y la web las muestran cada una a su manera.
- **Funciones puras y pruebas sin red.** La limpieza de títulos, la separación
  de artistas y el manejo de archivos se prueban con pytest, usando carpetas
  temporales y datos de ejemplo.
- **Cola con un solo trabajador.** La web no se bloquea durante una descarga y
  se descarga una canción a la vez, lo que evita problemas de concurrencia y es
  más amable con YouTube. La página consulta el estado cada segundo.
- **Entrada validada.** El navegador solo envía el ID del video; el servidor
  construye la URL.
- **Casos reales que mejoraron el código:** títulos con guiones largos
  (`–`) en lugar de guion normal, y un cambio del reproductor de YouTube que
  rompió el solucionador de desafíos de yt-dlp hasta actualizar la herramienta.
- **Spotify descartado.** Evalué su API para los metadatos, pero en 2026
  exige una cuenta Premium para desarrolladores y limita campos y usuarios.

## Limitaciones

- La calidad del audio depende de lo que YouTube ofrezca.
- La corrección de metadatos espera nombres con el formato «Artista - Título».
- La interfaz web está pensada para usarse **solo en tu propia computadora**
  (`127.0.0.1`); no la expongas a internet.
- Tu historial, enlaces, descargas y claves no se suben al repositorio
  (están en `.gitignore`).

## Pendiente

- Metadatos desde MusicBrainz (álbum, año, nombres oficiales): hay una rama
  `musicbrainz` con pruebas que pasan, pero falta ajustar las coincidencias con
  canciones reales.
- Vista de biblioteca y edición de metadatos desde la web.
- Cola persistente que sobreviva a recargar la página.

## Aviso

Proyecto para uso personal y de aprendizaje. Cada persona es responsable de
respetar los términos de servicio de YouTube y las leyes de derechos de autor
de su país.

