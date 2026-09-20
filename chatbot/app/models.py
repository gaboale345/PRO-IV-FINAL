from django.db import models

# Modelos para el ChatBot

class ChatHistory(models.Model):
    user_input = models.TextField(verbose_name="Mensaje del usuario")
    bot_response = models.TextField(verbose_name="Respuesta del asistente")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")

    class Meta:
        verbose_name = "Historial de chat"
        verbose_name_plural = "Historiales de chat"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Mensaje ({self.timestamp.strftime('%d/%m/%Y %H:%M')}): {self.user_input[:40]}..."