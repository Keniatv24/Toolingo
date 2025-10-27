from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation
try:
    from .models import Message  # type: ignore
except Exception:
    Message = None

from .serializers import ConversationListSerializer as ConversationSerializer
try:
    from .serializers import MessageSerializer  # type: ignore
except Exception:
    MessageSerializer = None

from catalog.models import Articulo

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    API de conversaciones.
      - POST /api/chats/by-article/
      - GET/POST /api/chats/{id}/messages/
      - POST /api/chats/{id}/read/
    """
    queryset = Conversation.objects.all().order_by("-creado") if hasattr(Conversation, "creado") else Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base = Conversation.objects.filter(participantes=user).distinct()
        return base.order_by("-creado") if hasattr(Conversation, "creado") else base

    # ======================================================
    # === Conversación por artículo ========================
    # ======================================================
    @action(detail=False, methods=["post"], url_path="by-article")
    def by_article(self, request, *args, **kwargs):
        """
        Devuelve o crea la conversación ligada a un artículo entre el usuario actual
        y el propietario. Si el usuario ES el propietario, retorna la última conversación
        existente para ese artículo (si la hay).
        Acepta: body {"articulo_id": "..."} o query ?articulo= / ?article=
        """
        art_id = (
            request.data.get("articulo_id")
            or request.query_params.get("articulo")
            or request.query_params.get("article")
        )
        if not art_id:
            return Response({"detail": "articulo_id requerido"}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Artículo
        try:
            articulo = Articulo.objects.get(pk=art_id)
        except Articulo.DoesNotExist:
            return Response({"detail": "Artículo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # 2) Dueño (ajusta si tu campo se llama distinto)
        owner = (
            getattr(articulo, "propietario", None)
            or getattr(articulo, "usuario", None)
            or getattr(articulo, "dueno", None)
            or getattr(articulo, "owner", None)
        )
        if owner is None:
            return Response({"detail": "El artículo no tiene propietario asociado"}, status=status.HTTP_400_BAD_REQUEST)

        me = request.user

        # 👉 Si el que llama es el dueño, devolver la conversación más reciente del artículo
        if owner == me:
            conv = (
                Conversation.objects
                .filter(articulo=articulo, participantes=me)
                .order_by("-ultimo_mensaje_en", "-creado")
                .first()
            )
            if not conv:
                return Response({"detail": "Aún no hay conversaciones para este artículo"}, status=status.HTTP_404_NOT_FOUND)
            data = self.get_serializer(conv, context={"request": request}).data
            data["created"] = False
            return Response(data, status=status.HTTP_200_OK)

        # 3) Reusar conversación exacta (mismo artículo y ambos usuarios)
        conv = (
            Conversation.objects
            .filter(articulo=articulo)
            .filter(participantes=me)
            .filter(participantes=owner)
            .first()
        )
        created = False
        if not conv:
            # Migrar una conversación vieja sin artículo (si existe)
            conv = (
                Conversation.objects
                .filter(articulo__isnull=True)
                .filter(participantes=me)
                .filter(participantes=owner)
                .first()
            )
            if conv:
                conv.articulo = articulo
                conv.save(update_fields=["articulo"])
            else:
                conv = Conversation.objects.create(articulo=articulo)
                conv.participantes.add(me, owner)
                created = True

        data = self.get_serializer(conv, context={"request": request}).data
        data["created"] = created
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # ======================================================
    # === Mensajes =========================================
    # ======================================================
    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        """
        GET  -> lista mensajes de la conversación (si el usuario pertenece)
        POST -> crea un mensaje en la conversación
        """
        if Message is None or MessageSerializer is None:
            return Response({"detail": "Modelo/serializer de mensajes no disponible"}, status=501)

        try:
            conv = Conversation.objects.filter(participantes=request.user).get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversación no encontrada"}, status=404)

        fk_name = "conversacion" if hasattr(Message, "conversacion_id") else "conversation"

        if request.method.lower() == "get":
            qs = Message.objects.filter(**{fk_name: conv}).order_by("creado") if hasattr(Message, "creado") \
                 else Message.objects.filter(**{fk_name: conv}).order_by("id")
            return Response(MessageSerializer(qs, many=True, context={"request": request}).data)

        # POST
        contenido = (request.data.get("contenido") or "").strip()
        if not contenido:
            return Response({"detail": "contenido requerido"}, status=400)

        kwargs = {fk_name: conv, "autor": request.user, "contenido": contenido}
        msg = Message.objects.create(**kwargs)
        data = MessageSerializer(msg, context={"request": request}).data
        return Response(data, status=201)

    
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        """Marca mensajes como leídos (placeholder)."""
        return Response(status=204)
