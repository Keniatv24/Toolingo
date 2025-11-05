# App/rentals/views.py
from datetime import timedelta

from django.db import models
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from common.enums import EstadoPago 

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from catalog.models import Articulo
from rest_framework.views import APIView

from .models import Alquiler, Calificacion, CartItem, Pago
from .serializers import (
    AlquilerSerializer,
    CalificacionPublicSerializer,
    CalificacionSerializer,
    CartItemSerializer,
    PagoSerializer,
)

# ---------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------
def daterange(d1, d2):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)

# Alquileres

class AlquilerViewSet(viewsets.ModelViewSet):
    serializer_class = AlquilerSerializer

    def get_queryset(self):
        qs = Alquiler.objects.select_related("articulo", "arrendatario", "propietario")
        u = getattr(self.request, "user", None)
        if u and u.is_authenticated:
            if u.is_staff:
                return qs
            return qs.filter(models.Q(arrendatario=u) | models.Q(propietario=u))
        return qs.none()

    def get_permissions(self):
        if getattr(self, "action", None) == "disponibilidad":
            return [permissions.AllowAny()]
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(arrendatario=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mios(self, request):
        qs = self.get_queryset().filter(arrendatario=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="disponibilidad", permission_classes=[permissions.AllowAny])
    def disponibilidad(self, request):
        art = request.query_params.get("articulo")
        s = parse_date(request.query_params.get("from") or "")
        e = parse_date(request.query_params.get("to") or "")

        if not art or not s or not e or s > e:
            return Response({"detail": "Parámetros inválidos"}, status=400)

        bloqueantes = ["SOLICITADO", "APROBADO", "EN_CURSO"]
        qs = (
            Alquiler.objects.filter(
                articulo_id=art,
                estado__in=bloqueantes,
                fecha_inicio__lte=e,
                fecha_fin__gte=s,
            )
            .order_by("fecha_inicio")
        )

        rangos = []
        dias_ocupados = set()
        for a in qs:
            rangos.append(
                {"inicio": a.fecha_inicio.isoformat(), "fin": a.fecha_fin.isoformat(), "estado": a.estado}
            )
            d0 = max(a.fecha_inicio, s)
            d1 = min(a.fecha_fin, e)
            cur = d0
            while cur <= d1:
                dias_ocupados.add(cur.isoformat())
                cur += timedelta(days=1)

        return Response(
            {
                "articulo": art,
                "from": s.isoformat(),
                "to": e.isoformat(),
                "rangos": rangos,
                "dias_ocupados": sorted(list(dias_ocupados)),
            }
        )


# Carrito

class CartItemViewSet(viewsets.ModelViewSet):
    """
    /api/carrito/            (lista, crea, elimina)
    /api/carrito/checkout/   (POST) -> crea Alquileres a partir del carrito y lo vacía
    """
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.select_related("articulo").filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        items = list(self.get_queryset())
        if not items:
            return Response({"detail": "El carrito está vacío."}, status=400)

        creados = []
        errores = []
        for it in items:
            data = {
                "articulo": it.articulo_id,
                "fecha_inicio": it.fecha_inicio,
                "fecha_fin": it.fecha_fin,
            }
            ser = AlquilerSerializer(data=data, context={"request": request})
            if ser.is_valid():
                try:
                    obj = ser.save()
                    creados.append(str(obj.id))
                except Exception as e:
                    errores.append(str(e))
            else:
                errores.append(ser.errors)

        if creados:
            CartItem.objects.filter(id__in=[i.id for i in items]).delete()

        return Response({"creados": creados, "errores": errores}, status=201 if creados else 400)


# pago
class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Pago.objects.select_related("alquiler").filter(
            models.Q(alquiler__arrendatario=u) | models.Q(alquiler__propietario=u)
        )



# Calificaciones propias (por usuario)

class CalificacionViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Calificacion.objects.filter(models.Q(autor=u) | models.Q(destinatario=u))


# Reseñas públicas por artículo
COMPLETED_STATES = ["FINALIZADO", "FINALIZADA", "COMPLETADO", "CERRADO", "TERMINADO"]
ALMOST_DONE_STATES = ["SOLICITADO", "APROBADO", "EN_CURSO"]


class ReviewsByArticuloList(APIView):
    """
    GET /api/articulos/<uuid:art_id>/reviews/?page=1&page_size=10
    Lista reseñas públicas de un artículo.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, art_id):
        qs = (
            Calificacion.objects.select_related("alquiler", "autor")
            .filter(alquiler__articulo_id=art_id)
            .order_by("-fecha")
        )

        # paginación simple
        try:
            page_size = int(request.GET.get("page_size", 10))
            page = int(request.GET.get("page", 1))
        except Exception:
            page_size, page = 10, 1

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        ser = CalificacionPublicSerializer(qs[start:end], many=True)
        return Response({"count": total, "page": page, "page_size": page_size, "results": ser.data})


class ReviewsByArticuloSummary(APIView):
    """
    GET /api/articulos/<uuid:art_id>/reviews/summary/
    Retorna promedio y conteo por estrellas.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, art_id):
        qs = Calificacion.objects.filter(alquiler__articulo_id=art_id)
        counts = {i: qs.filter(puntaje=i).count() for i in range(1, 6)}
        total = sum(counts.values()) or 0
        avg = round(sum(i * counts[i] for i in range(1, 6)) / total, 2) if total else 0.0
        return Response({"avg": avg, "total": total, "counts": counts})


class ReviewsByArticuloEligibility(APIView):
    """
    GET /api/articulos/<uuid:art_id>/reviews/eligibility/
    Permitimos reseñas a todo usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, art_id):
        u = request.user
        a = (
            Alquiler.objects
            .filter(articulo_id=art_id, arrendatario=u)
            .order_by("-fecha_fin", "-creado")
            .first()
        )
        payload = {"eligible": True}
        if a:
            payload["alquiler_id"] = a.id
        return Response(payload)


class ReviewsByArticuloCreate(APIView):
    """
    POST /api/articulos/<uuid:art_id>/reviews/create/
    Body: { "puntaje": 1..5, "comentario": "..." }

    Si el usuario no tiene alquiler del artículo, creamos un "alquiler virtual"
    (hoy→hoy) en estado FINALIZADO para poder colgar la reseña.
    Evitamos duplicados: 1 reseña por usuario y por artículo.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, art_id):
        # --- validar entrada
        try:
            puntaje = int(request.data.get("puntaje"))
        except Exception:
            return Response({"detail": "Puntaje inválido."}, status=400)
        comentario = (request.data.get("comentario") or "").strip()
        if puntaje < 1 or puntaje > 5:
            return Response({"detail": "Puntaje debe estar entre 1 y 5."}, status=400)

        u = request.user

        # --- evitar duplicado por usuario/artículo
        if Calificacion.objects.filter(autor=u, alquiler__articulo_id=art_id).exists():
            return Response({"detail": "Ya dejaste una reseña para este artículo."}, status=400)

        # --- buscar alquiler existente del usuario para el artículo (si lo hay)
        alquiler = (
            Alquiler.objects
            .filter(articulo_id=art_id, arrendatario=u)
            .order_by("-fecha_fin", "-creado")
            .first()
        )

        # --- crear alquiler virtual FINALIZADO si no existe
        if not alquiler:
            try:
                articulo = Articulo.objects.get(id=art_id)
            except Articulo.DoesNotExist:
                return Response({"detail": "Artículo no encontrado."}, status=404)
            today = now().date()
            alquiler = Alquiler.objects.create(
                articulo=articulo,
                arrendatario=u,
                propietario=articulo.propietario,
                fecha_inicio=today,
                fecha_fin=today,
                estado="FINALIZADO",
            )

        # --- crear calificación
        cal = Calificacion.objects.create(
            alquiler=alquiler,
            autor=u,
            destinatario=alquiler.propietario,
            puntaje=puntaje,
            comentario=comentario,
            fecha=now(),
        )
        return Response(CalificacionPublicSerializer(cal).data, status=201)