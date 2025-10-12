# App/chat/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Usuario compacto para mostrar en participantes/autor."""
    class Meta:
        model = User
        # Ajusta los campos según tu User (si no tienes email, quítalo)
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

    class Meta:
        model = Conversation
        fields = (
            "id",
            "participantes",
            "ultimo_mensaje_en",
            "creado",
            "actualizado",
        )
        read_only_fields = fields
