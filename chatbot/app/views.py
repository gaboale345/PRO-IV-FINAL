import os
import json
import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import ChatHistory
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Catálogo de plantillas de prompts según el rol seleccionado (Funcionalidad Adicional)
PLANTILLAS_ROLES = {
    "general": """Eres un asistente virtual conciso, útil y amable.
Responde siempre en español de forma directa, breve y clara (máximo 2 a 3 oraciones).

Historial:
{context}

Pregunta: {question}
Respuesta:""",

    "programador": """Eres un desarrollador senior y experto en Python, Linux y buenas prácticas de ingeniería de software.
Responde siempre en español. Si el usuario te hace una pregunta técnica o de código, proporciona explicaciones concisas y ejemplos con código limpio, comentado y moderno.

Historial:
{context}

Pregunta: {question}
Respuesta:""",

    "tutor": """Eres un tutor universitario de la materia Programación IV, paciente, didáctico y claro.
Responde siempre en español. Explica los conceptos técnicos paso a paso, utilizando analogías didácticas y ejemplos sencillos de entender.

Historial:
{context}

Pregunta: {question}
Respuesta:""",

    "creativo": """Eres un redactor y comunicador creativo.
Responde siempre en español con un tono elocuente, expresivo y enriquecedor, manteniendo precisión y coherencia en cada respuesta.

Historial:
{context}

Pregunta: {question}
Respuesta:"""
}

ROLES_METADATA = [
    {"id": "general", "nombre": "🤖 Asistente General", "descripcion": "Respuestas rápidas, concisas y directas"},
    {"id": "programador", "nombre": "💻 Programador Python", "descripcion": "Código limpio, depuración y Linux"},
    {"id": "tutor", "nombre": "🎓 Tutor Académico", "descripcion": "Conceptos didácticos paso a paso"},
    {"id": "creativo", "nombre": "✍️ Redactor Creativo", "descripcion": "Textos fluidos y creativos"}
]

# Modelo ultraligero qwen2.5:0.5b (397 MB) optimizado para CPUs sin GPU
MODELO_OLLAMA = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

def obtener_cadena(rol="general"):
    """Inicializa la cadena de LangChain conectada a Ollama con la plantilla del rol seleccionado."""
    try:
        plantilla = PLANTILLAS_ROLES.get(rol, PLANTILLAS_ROLES["general"])
        modelo = OllamaLLM(
            model=MODELO_OLLAMA,
            keep_alive="24h",     # Mantiene el modelo en memoria RAM durante 24 horas
            temperature=0.3 if rol == "programador" else 0.5,
            num_predict=150,      # Límite de longitud para respuestas rápidas
            num_thread=3,         # Óptimo para CPUs multinúcleo sin saturación
        )
        prompt = ChatPromptTemplate.from_template(plantilla)
        return prompt | modelo
    except Exception as e:
        logger.error(f"Error al inicializar el modelo Ollama '{MODELO_OLLAMA}': {e}")
        return None

def chatbot_view(request):
    """Vista principal que renderiza la interfaz del ChatBot con soporte para roles."""
    return render(request, "index.html", {
        "modelo_actual": MODELO_OLLAMA,
        "ip_red": "172.25.4.247",
        "red_subred": "172.25.4.128/25",
        "roles": ROLES_METADATA
    })

def chat(request):
    """Endpoint para procesar mensajes de chat del usuario con rol dinámico."""
    if request.method == "POST":
        user_input = request.POST.get("user_input", "").strip()
        rol = request.POST.get("rol", "general").strip()
        if rol not in PLANTILLAS_ROLES:
            rol = "general"

        if not user_input:
            return JsonResponse({"error": "El mensaje no puede estar vacío."}, status=400)

        # Contexto ligero: últimas 2 interacciones para procesamiento ultrarrápido
        historial_reciente = ChatHistory.objects.all().order_by("-timestamp")[:2]
        historial_cronologico = list(reversed(historial_reciente))
        
        if historial_cronologico:
            contexto = "\n".join([
                f"U: {h.user_input}\nA: {h.bot_response}"
                for h in historial_cronologico
            ])
        else:
            contexto = "No hay interacciones previas."

        cadena = obtener_cadena(rol=rol)
        if not cadena:
            return JsonResponse({
                "error": f"No se pudo conectar con Ollama usando el modelo '{MODELO_OLLAMA}'."
            }, status=500)

        try:
            # Generar respuesta con Ollama y la plantilla del rol seleccionado
            resultado = cadena.invoke({"context": contexto, "question": user_input})
            
            # Guardar en la base de datos
            registro = ChatHistory.objects.create(
                user_input=user_input,
                bot_response=resultado
            )

            return JsonResponse({
                "user_input": user_input,
                "bot_response": resultado,
                "timestamp": registro.timestamp.strftime("%H:%M"),
                "rol": rol
            })
        except Exception as e:
            logger.error(f"Error al procesar el mensaje con Ollama: {e}")
            return JsonResponse({
                "error": f"Error al generar la respuesta con Ollama ({MODELO_OLLAMA}): {str(e)}"
            }, status=500)

    return JsonResponse({"error": "Método no permitido. Utilice POST."}, status=405)

def chat_history(request):
    """Endpoint para obtener el historial de conversaciones."""
    historial = ChatHistory.objects.all().order_by("-timestamp")[:50]
    return JsonResponse({
        "history": [
            {
                "id": h.id,
                "user": h.user_input,
                "bot": h.bot_response,
                "timestamp": h.timestamp.strftime("%d/%m/%Y %H:%M")
            }
            for h in historial
        ]
    })

def export_history(request):
    """Funcionalidad Adicional 1: Exportar el historial en formato Markdown, TXT o JSON."""
    formato = request.GET.get("formato", "md").lower()
    historial = ChatHistory.objects.all().order_by("timestamp")
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H%M")

    if formato == "json":
        data = [
            {
                "id": h.id,
                "fecha": h.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "usuario": h.user_input,
                "asistente": h.bot_response
            }
            for h in historial
        ]
        contenido = json.dumps(data, indent=2, ensure_ascii=False)
        response = HttpResponse(contenido, content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_chat_{fecha_str}.json"'
        return response

    elif formato == "txt":
        lineas = [
            "=" * 60,
            " HISTORIAL DE CONVERSACIONES - ASISTENTE VIRTUAL IA",
            f" Fecha de exportación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f" Total de mensajes registrados: {historial.count()}",
            "=" * 60,
            ""
        ]
        for h in historial:
            lineas.append(f"[{h.timestamp.strftime('%d/%m/%Y %H:%M')}] Usuario:")
            lineas.append(f"  {h.user_input}")
            lineas.append(f"[{h.timestamp.strftime('%d/%m/%Y %H:%M')}] Asistente IA:")
            lineas.append(f"  {h.bot_response}")
            lineas.append("-" * 50)
        contenido = "\n".join(lineas)
        response = HttpResponse(contenido, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_chat_{fecha_str}.txt"'
        return response

    else: # Formato Markdown (.md) por defecto
        lineas = [
            "# Historial de Conversaciones - Asistente Virtual IA",
            "",
            f"- **Fecha de exportación:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"- **Total de interacciones:** {historial.count()}",
            f"- **Modelo utilizado:** `{MODELO_OLLAMA}`",
            "",
            "---",
            ""
        ]
        for idx, h in enumerate(historial, start=1):
            lineas.append(f"### Interacción #{idx} — *{h.timestamp.strftime('%d/%m/%Y %H:%M')}*")
            lineas.append("")
            lineas.append(f"**👤 Usuario:**")
            lineas.append(f"> {h.user_input}")
            lineas.append("")
            lineas.append(f"**🤖 Asistente IA:**")
            lineas.append(f"{h.bot_response}")
            lineas.append("")
            lineas.append("---")
            lineas.append("")
        contenido = "\n".join(lineas)
        response = HttpResponse(contenido, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_chat_{fecha_str}.md"'
        return response

def clear_history(request):
    """Funcionalidad Adicional: Vaciar completamente el historial de la base de datos."""
    if request.method == "POST":
        total_borrados = ChatHistory.objects.count()
        ChatHistory.objects.all().delete()
        return JsonResponse({
            "status": "ok",
            "message": f"Se eliminaron {total_borrados} registros del historial exitosamente."
        })
    return JsonResponse({"error": "Método no permitido. Utilice POST."}, status=405)