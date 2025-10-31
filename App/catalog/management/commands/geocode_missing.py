# App/catalog/management/commands/geocode_missing.py
from django.core.management.base import BaseCommand
from catalog.models import Articulo
from common.services.geocoding import geocode_address, GeocodingError

class Command(BaseCommand):
    help = "Geocodifica artículos sin lat/lng usando Nominatim."

    def add_arguments(self, parser):
        parser.add_argument("--country", default="co", help="Filtro de país (country codes). Ej: co")

    def handle(self, *args, **opts):
        cc = opts["country"]
        qs = Articulo.objects.filter(lat__isnull=True, lng__isnull=True).exclude(ubicacion__isnull=True).exclude(ubicacion="")
        total = qs.count()
        ok, fail = 0, 0
        for art in qs.iterator():
            try:
                lat, lng, display = geocode_address(art.ubicacion, country_codes=cc)
                art.lat = lat
                art.lng = lng
                if display and len(display) > len(art.ubicacion or ""):
                    art.ubicacion = display
                art.save(update_fields=["lat", "lng", "ubicacion"])
                ok += 1
            except GeocodingError:
                fail += 1
        self.stdout.write(self.style.SUCCESS(f"Listo. Total: {total}, geocodificados: {ok}, fallidos: {fail}"))
