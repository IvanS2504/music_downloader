from django.shortcuts import render

from descargas import buscar_videos_youtube, formatear_duracion
from historial import cargar_historial


def buscar(request):
    consulta = request.GET.get("q", "").strip()
    resultados = []
    if consulta:
        historial = cargar_historial()
        for video in buscar_videos_youtube(consulta):
            resultados.append({
                **video,
                "duracion": formatear_duracion(video["duration"]),
                "descargada": video["id"] in historial,
            })
    return render(request, "buscador/buscar.html",
                  {"consulta": consulta, "resultados": resultados})