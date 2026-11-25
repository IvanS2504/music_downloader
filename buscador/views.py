import re

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

import trabajos

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

@require_POST
def descargar(request):
    id_video = request.POST.get("id", "")
    titulo = request.POST.get("titulo", "").strip()
    if not re.fullmatch(r"[\w-]{11}", id_video):
        return JsonResponse({"error": "ID de video no válido"}, status=400)

    url = f"https://www.youtube.com/watch?v={id_video}"
    return JsonResponse({"trabajo": trabajos.encolar(url, titulo)})


@require_GET
def estado(request, id_trabajo):
    trabajo = trabajos.consultar(id_trabajo)
    if trabajo is None:
        return JsonResponse({"error": "No existe"}, status=404)
    return JsonResponse(trabajo)