import time
import trabajos

def test_un_trabajo_se_completa(monkeypatch):
    def descarga_falsa(url, on_progress=None, on_paso=None):
        on_progress({"downloaded_bytes": 50, "total_bytes": 100})
        return "ok"

    monkeypatch.setattr(trabajos, "procesar_descarga", descarga_falsa)

    id_trabajo = trabajos.encolar("https://ejemplo", "Canción")
    for _ in range(100):                      # espera hasta 5 segundos
        if trabajos.consultar(id_trabajo)["estado"] == "ok":
            break
        time.sleep(0.05)

    trabajo = trabajos.consultar(id_trabajo)
    assert trabajo["estado"] == "ok"
    assert trabajo["progreso"] == 1.0