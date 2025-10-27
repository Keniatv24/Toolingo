from django.conf import settings
from django.db import models
from catalog.models import Articulo  # ⬅️ vínculo al artículo


class Conversation(models.Model):
    # Conversación ligada a un artículo específico
    articulo = models.ForeignKey(
        Articulo,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="conversaciones",
    )

    # Participantes vía tabla intermedia explícita
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
        through="ConversationParticipante",
        blank=True,
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    ultimo_mensaje_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-ultimo_mensaje_en", "-creado"]


class ConversationParticipante(models.Model):
    """
    Tabla intermedia para Conversation.participantes.
    """
    conversacion = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="miembros"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membresias_chat"
    )
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("conversacion", "usuario"),)
        db_table = "chat_conversation_participantes"  # nombre estable


class Message(models.Model):
    conversacion = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="mensajes"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mensajes_chat"
    )
    contenido = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]

    def save(self, *args, **kwargs):
        # al guardar un mensaje, actualiza el "ultimo_mensaje_en"
        super().save(*args, **kwargs)
        type(self).objects.filter(pk=self.pk).update()  # no-op para asegurar pk
        Conversation.objects.filter(pk=self.conversacion_id).update(ultimo_mensaje_en=self.creado)
