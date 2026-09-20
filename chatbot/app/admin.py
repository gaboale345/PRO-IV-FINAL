from django.contrib import admin
from .models import ChatHistory

# Registro de modelos para administración

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_input_preview', 'bot_response_preview', 'timestamp')
    search_fields = ('user_input', 'bot_response')
    list_filter = ('timestamp',)

    def user_input_preview(self, obj):
        return obj.user_input[:50] + ("..." if len(obj.user_input) > 50 else "")
    user_input_preview.short_description = "Mensaje del usuario"

    def bot_response_preview(self, obj):
        return obj.bot_response[:50] + ("..." if len(obj.bot_response) > 50 else "")
    bot_response_preview.short_description = "Respuesta del bot"
