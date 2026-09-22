from django.urls import path
from .views import (
    chatbot_view,
    api_productos,
    api_crear_producto,
    api_obtener_producto,
    api_editar_producto,
    api_eliminar_producto,
    api_cambiar_estado,
    api_ajustar_stock,
    api_reportes,
    api_estadisticas,
    chat,
    chat_stream,
    chat_history,
    export_history,
    clear_history
)

urlpatterns = [
    # Vista Principal
    path("", chatbot_view, name="Chatbot"),

    # CRUD de Productos (RF-01, RF-02, RF-03, RF-04)
    path("api/productos/", api_productos, name="api_productos"),
    path("api/productos/crear/", api_crear_producto, name="api_crear_producto"),
    path("api/productos/<int:pk>/", api_obtener_producto, name="api_obtener_producto"),
    path("api/productos/<int:pk>/editar/", api_editar_producto, name="api_editar_producto"),
    path("api/productos/<int:pk>/eliminar/", api_eliminar_producto, name="api_eliminar_producto"),
    path("api/productos/<int:pk>/cambiar-estado/", api_cambiar_estado, name="api_cambiar_estado"),

    # Control de Existencias (RF-05)
    path("api/productos/<int:pk>/ajustar-stock/", api_ajustar_stock, name="api_ajustar_stock"),

    # Menú de Reportes Predefinidos (RF-06)
    path("api/reportes/<str:tipo>/", api_reportes, name="api_reportes"),
    path("api/estadisticas/", api_estadisticas, name="api_estadisticas"),

    # Chat e Integración con Ollama (RF-07, RF-08, RF-09)
    path("chat/", chat, name="chat"),
    path("chat/stream/", chat_stream, name="chat_stream"),

    # Historial y Exportación (RF-10)
    path("history/", chat_history, name="history"),
    path("export/", export_history, name="export"),
    path("clear-history/", clear_history, name="clear_history"),
]