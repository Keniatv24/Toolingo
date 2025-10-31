from django.contrib import admin
from .models import Categoria, Articulo, Imagen
from common.services.geocoding import geocode_address, GeocodingError

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "parent", "slug")
    search_fields = ("nombre", "slug")

@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "ubicacion", "lat", "lng", "creado", "propietario")
    list_filter  = ("categoria", "creado")
    search_fields = ("titulo", "descripcion", "ubicacion")
    actions = ["geocodificar_seleccionados"]

    def geocodificar_seleccionados(self, request, queryset):
        ok, fail = 0, 0
        for art in queryset:
            direccion = (art.ubicacion or "").strip()
            if not direccion:
                fail += 1
                continue
            try:
                lat, lng, display = geocode_address(direccion, country_codes="co")
                art.lat = lat
                art.lng = lng
                if display and len(display) > len(art.ubicacion or ""):
                    art.ubicacion = display
                art.save(update_fields=["lat", "lng", "ubicacion"])
                ok += 1
            except GeocodingError:
                fail += 1
        self.message_user(request, f"Geocodificados: {ok}. Fallidos: {fail}.")

    geocodificar_seleccionados.short_description = "Geocodificar (Nominatim) los artículos seleccionados"

@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ("id", "articulo", "descripcion")
