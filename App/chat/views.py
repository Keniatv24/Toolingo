from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation
try:
    # Si existe el modelo Message lo importamos (nombre típico)
    from .models import Message  # type: ignore
except Exception:  # pragma: no cover
    Message = None  # para que no truene si aún no existe

# Serializers
from .serializers import ConversationListSerializer as ConversationSerializer
try:
    from .serializers import MessageSerializer  # type: ignore
except Exception:  # pragma: no cover
    MessageSerializer = None

from catalog.models import Articulo

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    API de conversaciones.
    Incluye acciones auxiliares:
      - POST /api/chats/by-article/
      - GET/POST /api/chats/{id}/messages/
      - POST /api/chats/{id}/read/
    """
    queryset = Conversation.objects.all().order_by("-creado") if hasattr(Conversation, "creado") else Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Por defecto listamos solo las conversaciones donde participa el usuario.
        """
        user = self.request.user
        return (Conversation.objects
                .filter(participantes=user)
                .distinct()
                .order_by("-creado") if hasattr(Conversation, "creado") else
                Conversation.objects.filter(participantes=user).distinct())

    
    # Crear / obtener conversación a partir de un artículo
    
    @action(detail=False, methods=['post'], url_path='by-article')
    def by_article(self, request):
        """
        Crea o retorna la conversación entre el usuario autenticado y
        el propietario del artículo recibido.
        Body esperado: {"articulo_id": "<uuid|id>"}  (también acepta ?article= o ?articulo=)
        """
        art_id = (
            request.data.get("articulo_id")
            or request.query_params.get("articulo")
            or request.query_params.get("article")
        )
        if not art_id:
            return Response({"detail": "articulo_id requerido"}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Buscar artículo
        try:
            articulo = Articulo.objects.get(pk=art_id)
        except Articulo.DoesNotExist:
            return Response({"detail": "Artículo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # 2) Hallar propietario (tolerante a diferentes nombres de campo)
        owner = (
            getattr(articulo, "propietario", None)
            or getattr(articulo, "usuario", None)
            or getattr(articulo, "dueno", None)
            or getattr(articulo, "owner", None)
        )
        if owner is None:
            return Response({"detail": "El artículo no tiene propietario asociado"}, status=status.HTTP_400_BAD_REQUEST)

        me = request.user

        # 3) Reusar conversación existente con ese par de usuarios
        if owner == me:
            # conversación de 1 participante (consigo mismo)
            conv = (
                Conversation.objects.filter(participantes=me)
                .annotate(num=Count("participantes"))
                .filter(num=1)
                .first()
            )
            if not conv:
                conv = Conversation.objects.create()
                conv.participantes.add(me)
        else:
            conv = (
                Conversation.objects.filter(participantes=me)
                .filter(participantes=owner)
                .first()
            )
            if not conv:
                conv = Conversation.objects.create()
                conv.participantes.add(me, owner)

        data = ConversationSerializer(conv, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)

   
    # Listar / crear mensajes de una conversación
    
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        GET  -> lista mensajes de la conversación
        POST -> crea un mensaje en la conversación
        """
        if Message is None or MessageSerializer is None:
            return Response({"detail": "Modelo/serializer de mensajes no disponible"}, status=501)

        # Recuperar la conversación a la que el usuario pertenece
        try:
            conv = Conversation.objects.filter(participantes=request.user).get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversación no encontrada"}, status=404)

        # Detección robusta del nombre del FK en Message (conversation vs conversacion)
        fk_name = "conversacion" if hasattr(Message, "conversacion_id") else "conversation"

        if request.method.lower() == "get":
            q = Q(**{f"{fk_name}": conv})
            qs = Message.objects.filter(q).order_by("creado") if hasattr(Message, "creado") else Message.objects.filter(q).order_by("id")
            return Response(MessageSerializer(qs, many=True, context={"request": request}).data)

        # POST
        contenido = request.data.get("contenido", "").strip()
        if not contenido:
            return Response({"detail": "contenido requerido"}, status=400)

        kwargs = {fk_name: conv, "autor": request.user, "contenido": contenido}
        msg = Message.objects.create(**kwargs)
        data = MessageSerializer(msg, context={"request": request}).data
        return Response(data, status=201)

   
    # Marcar como leído (simplificado)
 
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        Marca los mensajes como leídos para el usuario (no-op si no hay tracking).
        Se deja simple para no acoplarse a implementaciones específicas.
        """
        # Aquí podrías guardar un timestamp por usuario/conversación, etc.
        return Response(status=204)
