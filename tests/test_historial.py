from historial import registrar_fallida, quitar_fallida, leer_fallidas, cargar_historial

def test_registrar_no_duplica(tmp_path):
    archivo = tmp_path / "fallidas.txt"
    registrar_fallida("https://x/1", archivo)
    registrar_fallida("https://x/1", archivo)
    assert leer_fallidas(archivo) == ["https://x/1"]

def test_quitar_fallida(tmp_path):
    archivo = tmp_path / "fallidas.txt"
    registrar_fallida("a", archivo)
    registrar_fallida("b", archivo)
    quitar_fallida("a", archivo)
    assert leer_fallidas(archivo) == ["b"]

def test_cargar_historial(tmp_path):
    archivo = tmp_path / "historial.txt"
    archivo.write_text("youtube abc123\nyoutube def456\n", encoding="utf-8")
    assert cargar_historial(archivo) == {"abc123", "def456"}