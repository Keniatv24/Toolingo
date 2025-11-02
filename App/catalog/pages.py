# App/catalog/pages.py
from django.conf import settings
from django.shortcuts import render
import requests

def articulo_detalle(request, id):
    """
    Renderiza la plantilla de detalle del artículo.
    'id' puede ser UUID o int; lo pasamos como string al template.
    """
    return render(request, "catalog/detalle.html", {"articulo_id": str(id)})


def productos_aliados(request):
    """
    Consume el servicio JSON del equipo anterior y muestra productos aliados
    con un look & feel de Toolingo (tarjetas con imagen, precio, estado, etc.).
    Soporta claves flexibles del aliado (titulo/title/name, precio/price/precio_por_dia, etc.).
    """
    url = getattr(settings, "EXTERNAL_ALLY_PRODUCTS_URL", "")
    items, error = [], None

    def _money(v):
        try:
            return f"${float(v):,.0f}".replace(",", ".")
        except Exception:
            return None

    try:
        if not url:
            raise ValueError("No se configuró EXTERNAL_ALLY_PRODUCTS_URL en settings.py")

        r = requests.get(url, timeout=6)
        r.raise_for_status()
        data = r.json()

        # Normalizamos y enriquecemos cada item
        for it in data:
            # Título flexible
            titulo = it.get("titulo") or it.get("title") or it.get("name") or "Artículo aliado"

            # Precio (si el aliado lo provee con algún nombre conocido)
            precio_raw = it.get("precio_por_dia") or it.get("precio") or it.get("price") or it.get("valor_dia")
            precio_fmt = _money(precio_raw) if precio_raw not in (None, "", False) else None

            # Estado / disponibilidad (si lo envían)
            estado = it.get("estado") or it.get("condition") or it.get("status")
            disponible = it.get("disponible") or it.get("available")

            # Ubicación/ciudad si existe
            ubicacion = it.get("ubicacion") or it.get("ciudad") or it.get("city")

            # Enlaces
            detail_api = it.get("detail_api") or it.get("detail_url") or ""
            detail_web = it.get("detail_web") or ""

            # Imagen: si el aliado no envía, usamos un placeholder estable por ID/título
            seed = str(it.get("id") or titulo).replace(" ", "-")
            img = it.get("imagen") or it.get("image") or f"https://picsum.photos/seed/{seed}/600/360"

            items.append({
                "id": it.get("id"),
                "titulo": titulo,
                "precio_fmt": precio_fmt,    # e.g. $120.000
                "estado": estado,            # e.g. NUEVO / USADO
                "disponible": disponible,    # True/False/None
                "ubicacion": ubicacion,      # e.g. Medellín
                "detail_api": detail_api,
                "detail_web": detail_web,
                "img": img,
            })
    except Exception as ex:
        error = str(ex)

    return render(request, "catalog/productos_aliados.html", {
        "items": items,
        "error": error,
        "source_url": url,
    })