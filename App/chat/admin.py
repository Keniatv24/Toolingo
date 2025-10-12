# App/chat/admin.py
from django.contrib import admin
from .models import Conversation, ConversationParticipante, Message


class ConversationParticipanteInline(admin.TabularInline):
    model = ConversationParticipante
    extra = 1
    autocomplete_fields = ("usuario",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "ultimo_mensaje_en", "creado")
    search_fields = ("id",)
    inlines = [ConversationParticipanteInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversacion", "autor", "creado")
    list_select_related = ("conversacion", "autor")
    search_fields = ("contenido",)
    autocomplete_fields = ("conversacion", "autor")
