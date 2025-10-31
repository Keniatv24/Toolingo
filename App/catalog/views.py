from django.db.models import Prefetch
from django.shortcuts import render

from rest_framework import viewsets, permissions, status, mixins, filters
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from .models import Categoria, Articulo, Imagen
from .serializers import CategoriaSerializer, ArticuloSerializer
from .filters import ArticuloFilter

# Geocodificación y distancia
from common.services.geocoding import geocode_city, geocode_address, GeocodingError
from .utils import haversine_km


# -------------------- Categorías (solo lectura) --------------------
class CategoriaViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]


# -------------------- Permiso owner-or-readonly --------------------
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "propietario_id", None) == getattr(request.user, "id", None)


# -------------------- Artículos (CRUD + acciones) --------------------
class ArticuloViewSet(ModelViewSet):
    serializer_class = ArticuloSerializer
    filterset_class = ArticuloFilter
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descripcion", "ubicacion"]
    ordering_fields = ["creado", "precio_por_dia"]
    ordering = ["-creado"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # ---------- helpers ----------
    @staticmethod
    def _to_float_or_none(v):
        if v in (None, "", "null", "None"):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clip(s, n):
        if s is None:
            return None
        return str(s)[:n]

    @staticmethod
    def _round6(x):
        if x in (None, "", "null", "None"):
            return None
        try:
            return round(float(x), 6)
        except (TypeError, ValueError):
            return None

    def _ensure_coords(self, instance: Articulo, ubicacion_raw, lat_raw, lng_raw):
        # 1) Si llegan coords válidas, guárdalas
        lat6 = self._round6(lat_raw)
        lng6 = self._round6(lng_raw)
        if lat6 is not None and lng6 is not None:
            instance.lat = lat6
            instance.lng = lng6
            instance.save(update_fields=["lat", "lng"])
            return

        # 2) Geocodificar por dirección si hay texto
        ubic = (ubicacion_raw or instance.ubicacion or "").strip()
        if not ubic:
            return
        try:
            lat, lng, display = geocode_address(ubic, country_codes="co")
            instance.lat = round(float(lat), 6)
            instance.lng = round(float(lng), 6)
            clean_display = self._clip(display, 140) if display else None
            if clean_display and len(clean_display) > len(instance.ubicacion or ""):
                instance.ubicacion = clean_display
                instance.save(update_fields=["lat", "lng", "ubicacion"])
            else:
                instance.save(update_fields=["lat", "lng"])
        except GeocodingError:
            pass  # no interrumpe

    # ---------- acciones ----------
    @action(detail=False, methods=["get"], url_path="cerca", permission_classes=[permissions.AllowAny])
    def cerca(self, request):
        try:
            radio_km = float(request.query_params.get("radio_km", 10))
        except ValueError:
            return Response({"detail": "radio_km inválido"}, status=status.HTTP_400_BAD_REQUEST)

        ciudad = request.query_params.get("ciudad")
        lat_param = request.query_params.get("lat")
        lng_param = request.query_params.get("lng")

        if ciudad:
            try:
                base_lat, base_lng = geocode_city(ciudad)
            except GeocodingError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif lat_param and lng_param:
            try:
                base_lat, base_lng = float(lat_param), float(lng_param)
            except ValueError:
                return Response({"detail": "lat/lng inválidos"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Proporcione ?ciudad=... o ?lat=...&lng=..."}, status=status.HTTP_400_BAD_REQUEST)

        qs = (self.get_queryset()
              .exclude(lat__isnull=True)
              .exclude(lng__isnull=True))

        deg = radio_km / 111.0
        qs = qs.filter(lat__gte=base_lat - deg, lat__lte=base_lat + deg,
                       lng__gte=base_lng - deg, lng__lte=base_lng + deg)

        dentro = []
        for art in qs:
            d = haversine_km(float(art.lat), float(art.lng), base_lat, base_lng)
            if d <= radio_km:
                dentro.append((d, art))
        dentro.sort(key=lambda t: t[0])
        articulos_ordenados = [a for _, a in dentro]

        page = self.paginate_queryset(articulos_ordenados)
        serializer = self.get_serializer(page or articulos_ordenados, many=True)
        body = serializer.data
        meta = {"origen": {"lat": base_lat, "lng": base_lng, "radio_km": radio_km},
                "fuente_geocoding": "Nominatim (OpenStreetMap)",
                "atribucion": "© OpenStreetMap contributors"}
        if page is not None:
            return self.get_paginated_response({"meta": meta, "items": body})
        return Response({"meta": meta, "items": body})

    # ---------- queryset ----------
    def get_queryset(self):
        qs = (Articulo.objects
              .select_related("categoria", "propietario")
              .prefetch_related(Prefetch("imagenes", queryset=Imagen.objects.order_by("id")))
              .all())

        slug = self.request.query_params.get("slug")
        if slug:
            qs = qs.filter(slug=slug)

        cat_slug = self.request.query_params.get("categoria")
        if cat_slug:
            qs = qs.filter(categoria__slug=cat_slug)

        return qs

    # ---------- permisos ----------
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    # ---------- create/update ----------
    def perform_create(self, serializer):
        # seguridad extra: no permitir crear sin user
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            raise permissions.NotAuthenticated("Debes iniciar sesión.")
        serializer.save(propietario=user)

    def create(self, request, *args, **kwargs):
        # Bloquea si no está autenticado (evita IntegrityError)
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "No autenticado."}, status=status.HTTP_401_UNAUTHORIZED)

        files = request.FILES.getlist("imagenes")
        if len(files) == 0 and not request.FILES.get("portada"):
            return Response({"detail": "Debes adjuntar al menos una foto."},
                            status=status.HTTP_400_BAD_REQUEST)

        lat_raw = request.data.get("lat")
        lng_raw = request.data.get("lng")
        ubi_raw = request.data.get("ubicacion")

        # Fallback de ubicación si viene vacía pero tenemos coords
        lat6 = self._round6(lat_raw)
        lng6 = self._round6(lng_raw)
        ubicacion_final = (ubi_raw or "").strip()
        if not ubicacion_final and (lat6 is not None and lng6 is not None):
            ubicacion_final = f"Lat {lat6}, Lng {lng6}"

        data = {
            "titulo": request.data.get("titulo"),
            "descripcion": request.data.get("descripcion"),
            "categoria": request.data.get("categoria"),
            "estado": request.data.get("estado") or "USADO",
            "precio_por_dia": request.data.get("precio_por_dia") or 0,
            "deposito": request.data.get("deposito") or 0,
            "disponibilidad_global": request.data.get("disponibilidad_global", True) in (True, "true", "True", "1", 1, "on"),
            "ubicacion": self._clip(ubicacion_final, 140),
            "lat": lat6,
            "lng": lng6,
        }

        ser = self.get_serializer(data=data)
        if not ser.is_valid():
            # logging para depurar rápido en consola
            print("❌ Articulo serializer errors =>", ser.errors)
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(ser)
        articulo = ser.instance

        # Intentar geocodificar si aún faltan coords
        self._ensure_coords(
            articulo,
            ubicacion_raw=data.get("ubicacion"),
            lat_raw=data.get("lat"),
            lng_raw=data.get("lng"),
        )

        portada = request.FILES.get("portada")
        if portada:
            Imagen.objects.create(articulo=articulo, imagen=portada)
        for f in files:
            Imagen.objects.create(articulo=articulo, imagen=f)

        headers = self.get_success_headers(ser.data)
        return Response(self.get_serializer(articulo).data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        resp = super().update(request, *args, **kwargs)
        self._ensure_coords(instance,
                            ubicacion_raw=request.data.get("ubicacion"),
                            lat_raw=request.data.get("lat"),
                            lng_raw=request.data.get("lng"))
        return resp

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        resp = super().partial_update(request, *args, **kwargs)
        self._ensure_coords(instance,
                            ubicacion_raw=request.data.get("ubicacion"),
                            lat_raw=request.data.get("lat"),
                            lng_raw=request.data.get("lng"))
        return resp

    # --------- auxiliares ---------
    @action(detail=False, methods=["get"])
    def recent(self, request):
        limit = int(request.query_params.get("limit", 6))
        qs = self.get_queryset().order_by("-creado")[:limit]
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        qs = self.get_queryset().filter(propietario=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)


# -------------------- Vista de detalle (template) --------------------
def articulo_detalle(request, id):
    return render(request, "catalog/detalle.html", {"articulo_id": str(id)})
