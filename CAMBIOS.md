# Registro de Modificaciones del Proyecto (CAMBIOS.md)

**Proyecto:** ChatBot Web con Django y Ollama  
**Estudiante:** Gabriel Alcón  
**Materia:** Programación IV  
**Actividad:** Actividad 4 – Implementación, localización y extensión de un proyecto open source con Ollama  
**Repositorio Base Original:** [Anjum799/ChatBot](https://github.com/Anjum799/ChatBot) (GitHub, 2024–2025)

---

## 1. Resumen de Modificaciones

El proyecto original consistía en una aplicación web elemental en Django que integraba Ollama mediante LangChain con el modelo `gemma:2b`. La interfaz gráfica original era básica, estaba completamente en inglés y solo permitía enviar mensajes y visualizar el historial sobreescribiendo el contenedor principal.

En esta entrega se realizaron las siguientes transformaciones integrales:
1. **Localización completa al español:** Traducción al 100% de la interfaz visual, etiquetas, mensajes de error, placeholders y documentación técnica.
2. **Ajuste del System Prompt en Ollama:** Modificación de las directivas del modelo para garantizar respuestas coherentes, gramaticalmente correctas y exclusivamente en idioma español.
3. **Optimización de Modelo Local:** Adaptación para modelos ultraligeros y eficientes en CPU (`qwen2.5:0.5b` y `qwen2.5:1.5b`), permitiendo tiempos de inferencia rápidos sin requerir GPU dedicada.
4. **Funcionalidad Adicional 1 – Sistema de Exportación Multiformato del Historial:** Descarga en un clic de las conversaciones en formatos Markdown (`.md`), Texto plano (`.txt`) o JSON estructurado (`.json`).
5. **Funcionalidad Adicional 2 – Selector Dinámico de Personalidades y Plantillas de Prompts:** Módulo que permite al usuario alternar en tiempo real entre distintos roles (Asistente General, Programador Python, Tutor Académico y Redactor Creativo), transformando el prompt del sistema enviado a Ollama.
6. **Funcionalidad Adicional 3 – Gestión y Vaciado de Base de Datos:** Endpoint y control interactivo con confirmación para limpiar la base de datos SQLite.
7. **Rediseño Visual Premium (Glassmorphism):** Interfaz moderna con animaciones CSS, panel lateral deslizable para el historial, burbujas de chat diferenciadas e indicador visual de escritura.
8. **Suite de Pruebas Automatizadas:** Creación de pruebas unitarias en Django (`tests.py`) para validar el 100% de los endpoints y asegurar que no existan regresiones.

---

## 2. Tabla de Archivos Modificados y Creados

| Archivo | Estado | Descripción del Cambio |
| :--- | :---: | :--- |
| `chatbot/app/views.py` | **Modificado** | Se implementó el diccionario de plantillas de prompts por rol (`PLANTILLAS_ROLES`), la selección dinámica de roles en `chat()`, el endpoint de exportación multiformato `export_history()`, el endpoint de vaciado `clear_history()` y las respuestas en español. |
| `chatbot/app/urls.py` | **Modificado** | Se registraron las nuevas rutas `/export/` y `/clear-history/`. |
| `chatbot/app/templates/index.html` | **Modificado** | Rediseño integral con estilo Glassmorphism, traducción de todos los textos al español, incorporación del selector de roles en el encabezado, botón de exportación, panel lateral de historial y notificaciones tipo toast. |
| `chatbot/app/tests.py` | **Modificado** | Implementación de 7 pruebas unitarias automatizadas que evalúan carga en español, chat con roles, exportación en Markdown/TXT/JSON y vaciado de BD. |
| `README.md` | **Modificado** | Documentación técnica en español con instrucciones detalladas de instalación, configuración del modelo Ollama, ejecución y pruebas. |
| `requirements.txt` | **Modificado / Generado** | Generado automáticamente con `pip freeze` dentro del entorno virtual con todas las dependencias exactas. |
| `iniciar_servidor.sh` | **Creado** | Script Bash para arranque automático del servidor Django en todas las interfaces de red (`0.0.0.0:8000`). |
| `CAMBIOS.md` | **Creado** | Este documento detallando los cambios realizados. |
| `informe.md` | **Creado** | Informe académico completo de la actividad con justificación, comandos, capturas y reflexiones. |

---

## 3. Detalle de Localización al Español (Punto 2)

### A. Interfaz de Usuario (UI)
- **Título:** De *"ChatBot"* a *"Asistente Virtual IA"*.
- **Placeholders:** De *"Type your message..."* a *"Escribe tu mensaje en español aquí..."*.
- **Botones y Acciones:**
  - *"Send"* $\rightarrow$ Botón estilizado *"Enviar"* con tecla Enter interactiva.
  - *"View History"* $\rightarrow$ Panel lateral *"Historial"*.
  - Agregado de *"Limpiar"* y *"Exportar"*.
- **Indicadores de Estado:** Agregado de indicador animado *"En línea"* y estado de escritura animado (*typing indicator*).

### B. Plantilla del Sistema (Prompt de Ollama)
**Código Original (Inglés):**
```python
template = '''
answer the question below

here is the conversation history:{context}

Question:{question}

Answer:
'''
```

**Código Modificado (Español y Modular):**
```python
PLANTILLAS_ROLES = {
    "general": """Eres un asistente virtual conciso, útil y amable.
Responde siempre en español de forma directa, breve y clara (máximo 2 a 3 oraciones).

Historial:
{context}

Pregunta: {question}
Respuesta:""",
...
}
```

---

## 4. Detalle de las Nuevas Funcionalidades (Punto 3)

### Funcionalidad 1: Exportación Multiformato del Historial
- **Archivos involucrados:** `chatbot/app/views.py`, `chatbot/app/urls.py`, `chatbot/app/templates/index.html`.
- **Qué hace:** Permite al usuario descargar en un solo clic todo el historial de interacciones almacenado en SQLite.
- **Formatos soportados:**
  - **Markdown (`.md`):** Formato estructurado con encabezados, citas de bloque y marcas de tiempo, ideal para documentación o GitHub.
  - **Texto Plano (`.txt`):** Formato universal legible en cualquier editor.
  - **JSON (`.json`):** Formato estructurado para interoperabilidad con otras aplicaciones.
- **Implementación técnica:** Vista `export_history(request)` que consulta `ChatHistory.objects.all().order_by("timestamp")` y devuelve un `HttpResponse` con cabecera `Content-Disposition: attachment; filename="..."`.

### Funcionalidad 2: Selector Dinámico de Personalidades y Plantillas de Prompts
- **Archivos involucrados:** `chatbot/app/views.py`, `chatbot/app/templates/index.html`.
- **Qué hace:** Permite modificar en tiempo de ejecución el rol y tono con el que Ollama genera sus respuestas.
- **Roles integrados:**
  1. 🤖 **Asistente General:** Respuestas directas, concisas y amables en español.
  2. 💻 **Programador Python:** Proporciona soluciones técnicas, arquitectura y código limpio comentado.
  3. 🎓 **Tutor Académico:** Explica paso a paso con analogías didácticas y pedagogía universitaria.
  4. ✍️ **Redactor Creativo:** Redacción fluida, elocuente y literaria.
- **Implementación técnica:** Parámetro `rol` enviado mediante POST desde JavaScript. La función `obtener_cadena(rol)` instancia la plantilla de LangChain correspondiente antes de invocar a Ollama.

### Funcionalidad Extra: Vaciado Seguro de la Base de Datos
- **Endpoint:** `/clear-history/` (método POST con validación CSRF).
- **Qué hace:** Elimina los registros previos de SQLite mediante `ChatHistory.objects.all().delete()` tras confirmación interactiva del usuario.

---

## 5. Comandos de Instalación y Dependencias

Para desplegar y ejecutar las modificaciones en Debian 12 / Linux:

```bash
# 1. Clonar o acceder al proyecto
cd proyecto/

# 2. Crear y activar entorno virtual con Python 3.11
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias exactas
pip install -r requirements.txt

# 4. Asegurar que Ollama esté activo y descargar el modelo
systemctl is-active ollama
ollama pull qwen2.5:0.5b

# 5. Aplicar migraciones de la base de datos
python chatbot/manage.py migrate

# 6. Ejecutar pruebas unitarias de validación
python chatbot/manage.py test app

# 7. Iniciar el servidor
python chatbot/manage.py runserver 0.0.0.0:8000
```
