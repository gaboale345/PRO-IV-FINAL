# Registro de Modificaciones del Proyecto (CAMBIOS.md)

**Asignatura:** Programación IV  
**Actividad:** Actividad 5 – Desarrollo de un sistema de información genérico con CRUD e integración de IA local mediante Ollama  
**Estudiante:** Gabriel Alcón  
**Repositorio Base:** Evolución desde la plantilla base [Anjum799/ChatBot](https://github.com/Anjum799/ChatBot)  
**Fecha:** Septiembre de 2026  

---

## 1. Resumen de Transformaciones Principales

El proyecto original consistía en un chatbot simple en Django con respuestas directas en inglés sin soporte para entidades de negocio ni trazabilidad. Para la **Actividad 5**, el proyecto se transformó en un **Sistema Empresarial de Gestión de Inventario con Trazabilidad Kardex, 8 Reportes Corporativos y Asistente IA Offline con Ollama**:

1. **Implementación de la Entidad de Gestión (`Producto`):**
   - Definición de más de 10 campos de datos (`codigo`, `nombre`, `descripcion`, `categoria`, `precio`, `cantidad_existente`, `stock_minimo`, `estado`, `marca`, `especificaciones`, `destacado`).
   - Validaciones estrictas en [forms.py](file:///home/gabriel/Downloads/PRO-IV-FINAL-main/chatbot/app/forms.py) para unicidad de código, precios no negativos ($\ge 0$) y control de existencias sin stock negativo.
   - Panel de administración personalizado en [admin.py](file:///home/gabriel/Downloads/PRO-IV-FINAL-main/chatbot/app/admin.py) con filtros, búsqueda y campos editables en línea.

2. **Módulo de Trazabilidad Contable e Inmutable (`Kardex Físico-Valorado`):**
   - Creación del modelo `MovimientoStock` para auditar cada entrada, salida o ajuste en el almacén.
   - Apertura automática de registro en Kardex ante la creación o importación masiva de productos.

3. **Capa de Servicios y Patrones de Diseño:**
   - Desacoplamiento de vistas monolíticas hacia `chatbot/app/services/`:
     - `inventory_service.py`: Gestión de catálogo, paginación, filtros y los 8 reportes corporativos.
     - `ollama_service.py`: Conexión Singleton persistente con Ollama, resolución determinística de hechos y mitigación de alucinaciones.
     - `export_service.py`: Patrón Strategy para exportación multiformato (CSV, HTML/PDF Hoja Oficial de Inventario con firmas, JSON, Markdown).

4. **Menú de 8 Reportes Predefinidos:**
   - Implementación de reportes analíticos con resumen cuantitativo y opción de análisis explicativo generado por Ollama.

5. **Chatbot Analítico Offline con Restricción de Respuestas:**
   - Inferencia local mediante `qwen2.5:1.5b` sin conexión a internet ni consumo de APIs de pago.
   - Streaming Server-Sent Events (SSE) en tiempo real.
   - Reglas estrictas: Si la consulta no pertenece al inventario o carece de datos suficientes, declina formalmente responder.
   - Manejo robusto de errores si Ollama no está en ejecución.

6. **Batería de Pruebas Unitarias Automatizadas:**
   - Creación de 17 pruebas unitarias en `chatbot/app/tests.py` que cubren el 100% de los requerimientos funcionales y aprueban con éxito.

---

## 2. Tabla de Archivos Modificados y Creados

| Archivo | Tipo | Descripción de la Modificación |
| :--- | :---: | :--- |
| `chatbot/app/models.py` | **Modificado** | Modelos `Producto`, `MovimientoStock` (Kardex) y `ChatHistory` con índices de base de datos. |
| `chatbot/app/admin.py` | **Modificado** | Configuración personalizada de `ProductoAdmin` y `ChatHistoryAdmin`. |
| `chatbot/app/forms.py` | **Creado** | Formularios `ProductoForm` y `AjusteStockForm` con validación de no negatividad y unicidad. |
| `chatbot/app/views.py` | **Modificado** | Endpoints para CRUD completo, control de existencias, Kardex, 8 reportes, chat con streaming SSE y exportación. |
| `chatbot/app/urls.py` | **Modificado** | Enrutamiento de endpoints API y vistas del sistema. |
| `chatbot/app/services/inventory_service.py` | **Creado** | Lógica de negocio de inventario, paginación, 8 reportes corporativos y Kardex. |
| `chatbot/app/services/ollama_service.py` | **Creado** | Integración con Ollama, patrón Singleton HTTP, resolución de hechos y caché TTL. |
| `chatbot/app/services/export_service.py` | **Creado** | Patrón Strategy para exportar historial y catálogo (incluyendo Hoja Oficial imprimible en PDF con firmas). |
| `chatbot/app/templates/index.html` | **Modificado** | Interfaz de usuario interactiva moderna con catálogo paginado, modales de CRUD y Kardex, panel de 8 reportes y chat SSE con voz (STT/TTS). |
| `chatbot/app/tests.py` | **Modificado** | 17 pruebas unitarias exhaustivas para CRUD, reportes, Kardex, Ollama y exportaciones. |
| `chatbot/poblar_inventario.py` | **Modificado** | Catálogo curado de 50 productos tecnológicos en Bolivianos (`Bs.`) con apertura en Kardex. |
| `requirements.txt` / `.env.example` | **Creados / Actualizados** | Dependencias congeladas y plantilla de variables de entorno seguras. |
| `informe.md` / `informe.pdf` | **Creados** | Informe técnico académico formal según estructura y rúbrica de la Actividad 5. |
| `DOCUMENTACION.md` | **Creado** | Documento complementario de decisiones técnicas y arquitectura. |
