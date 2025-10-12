from django.conf import settings
from django.db import models


class Conversation(models.Model):
    # Dejamos el M2M pero ahora *a través* del modelo intermedio explícito
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        through='ConversationParticipante',   # <— clave
        blank=True,
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    ultimo_mensaje_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-ultimo_mensaje_en', '-creado']


class ConversationParticipante(models.Model):
    """
    Tabla intermedia explícita para Conversation.participantes.
    Importante: usamos db_table='chat_conversation_participantes' para
    que coincida EXACTO con lo que espera tu código/consultas.
    """
    conversacion = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='miembros'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membresias_chat'
    )
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('conversacion', 'usuario'),)
        db_table = 'chat_conversation_participantes'  # <— nombre exacto


class Message(models.Model):
    conversacion = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='mensajes'
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensajes_chat'
    )
    contenido = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado']
