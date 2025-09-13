# App/catalog/pages.py
from django.shortcuts import render

def articulo_detalle(request, id):
    """
    Renderiza la plantilla de detalle del artículo.
    'id' puede ser UUID o int; lo pasamos como string al template.
    """
    return render(request, "catalog/detalle.html", {"articulo_id": str(id)})
