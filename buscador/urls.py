from django.urls import path

from . import views

urlpatterns = [
    path("", views.buscar, name="buscar"),
    path("descargar/", views.descargar, name="descargar"),
    path("estado/<str:id_trabajo>/", views.estado, name="estado"),
    path("metadatos/", views.metadatos, name="metadatos"),
]