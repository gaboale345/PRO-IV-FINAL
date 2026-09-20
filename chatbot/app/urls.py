from django.urls import path
from .views import chatbot_view, chat, chat_history, export_history, clear_history

urlpatterns = [
    path("", chatbot_view, name="Chatbot"),
    path("chat/", chat, name="chat"),
    path("history/", chat_history, name="history"),
    path("export/", export_history, name="export"),
    path("clear-history/", clear_history, name="clear_history"),
]