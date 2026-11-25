import queue
import threading
import uuid

from descargas import PASOS, fraccion_de, procesar_descarga

_trabajos = {}                  # id -> estado de cada trabajo
_cola = queue.Queue()
_candado = threading.Lock()     # protege _trabajos entre hilos
_hilo = None


def encolar(url, titulo):
    """Agrega una descarga a la cola y devuelve su identificador."""
    id_trabajo = uuid.uuid4().hex
    with _candado:
        _trabajos[id_trabajo] = {
            "titulo": titulo, "url": url,
            "estado": "en_cola", "progreso": 0.0, "paso": "",
        }
    _cola.put(id_trabajo)
    _asegurar_trabajador()          # fuera del "with": el candado no es reentrante
    return id_trabajo


def consultar(id_trabajo):
    """Devuelve una copia del estado del trabajo, o None si no existe."""
    with _candado:
        trabajo = _trabajos.get(id_trabajo)
        return dict(trabajo) if trabajo else None


def _actualizar(id_trabajo, **cambios):
    with _candado:
        _trabajos[id_trabajo].update(cambios)


def _asegurar_trabajador():
    global _hilo
    with _candado:
        if _hilo is None or not _hilo.is_alive():
            _hilo = threading.Thread(target=_trabajador, daemon=True)
            _hilo.start()


def _trabajador():
    while True:
        id_trabajo = _cola.get()
        try:
            _ejecutar(id_trabajo)
        except Exception:
            _actualizar(id_trabajo, estado="fallida")
        finally:
            _cola.task_done()


def _ejecutar(id_trabajo):
    _actualizar(id_trabajo, estado="descargando")
    url = consultar(id_trabajo)["url"]

    def al_progresar(d):
        fraccion = fraccion_de(d)
        if fraccion is not None:
            _actualizar(id_trabajo, progreso=fraccion)

    def al_paso(d):
        if d["status"] == "started":
            _actualizar(id_trabajo, paso=PASOS.get(d["postprocessor"], d["postprocessor"]))

    resultado = procesar_descarga(url, al_progresar, al_paso)
    _actualizar(id_trabajo, estado=resultado,
                progreso=1.0 if resultado != "fallida" else 0.0)

def hay_activos():
    """True si hay descargas esperando o en curso."""
    with _candado:
        return any(t["estado"] in ("en_cola", "descargando") for t in _trabajos.values())