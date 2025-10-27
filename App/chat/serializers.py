# App/chat/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Usuario compacto para mostrar en participantes/autor."""
    class Meta:
        model = User
        fields = ("id", "email", "username")
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    autor = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "conversacion", "autor", "contenido", "creado")
        read_only_fields = ("id", "conversacion", "autor", "creado")


class ConversationListSerializer(serializers.ModelSerializer):
    participantes = UserMiniSerializer(many=True, read_only=True)
    articulo = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "participantes",
            "articulo",
            "ultimo_mensaje_en",
            "creado",
            "actualizado",
        )
        read_only_fields = fields

    def get_articulo(self, obj):
        a = getattr(obj, "articulo", None)
        if not a:
            return None
        # Campos tolerantes a distintos nombres presentes en tu modelo/serializer de catálogo
        titulo = getattr(a, "titulo", None) or getattr(a, "nombre", None) or "Artículo"
        precio = (
            getattr(a, "precio_por_dia", None)
            or getattr(a, "precio", None)
            or getattr(a, "costo", None)
        )
        # Imagen principal (portada o la primera de 'imagenes')
        portada = getattr(a, "portada", None)
        img = None
        if portada:
            img = getattr(portada, "url", None) or portada
        elif hasattr(a, "imagenes"):
            try:
                first = a.imagenes.first()
                img = getattr(first, "archivo", None) or getattr(first, "imagen", None) or first
                if hasattr(img, "url"):
                    img = img.url
            except Exception:
                img = None

        return {
            "id": str(getattr(a, "id", "")),
            "titulo": titulo,
            "precio": precio,
            "imagen": img,
        }
