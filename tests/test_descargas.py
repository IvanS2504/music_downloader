import pytest
from descargas import formatear_duracion

@pytest.mark.parametrize("segundos, esperado", [
    (0, "??:??"), (None, "??:??"), (65, "1:05"), (215.0, "3:35"), (3725, "1:02:05"),
])
def test_formatear_duracion(segundos, esperado):
    assert formatear_duracion(segundos) == esperado