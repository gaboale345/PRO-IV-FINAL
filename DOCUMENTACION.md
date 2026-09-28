# Decisiones Técnicas y Arquitectura del Sistema (DOCUMENTACION.md)

**Asignatura:** Programación IV  
**Actividad:** Actividad 5 – Sistema de Información con CRUD e Integración de IA Local (Ollama)  
**Estudiante:** Gabriel Alcón  
**Docente:** Ing. Jared López Leaños  
**Asistente de Codificación IA:** Google Antigravity (Advanced Agentic IDE)  
**Entorno:** Python 3.11+, Django 5.1.6, Ollama (qwen2.5:1.5b), SQLite3 (WAL mode), Linux Debian 12  
**Fecha:** 28 de Septiembre de 2026  

---

## 1. Visión General del Proyecto

El sistema es una solución empresarial completa para la administración y auditoría de catálogo de productos tecnológicos en el mercado boliviano, incorporando trazabilidad contable mediante **Kardex Físico-Valorado**, generación de **8 reportes gerenciales**, y un asistente virtual en lenguaje natural impulsado por **Ollama (IA local offline)** con mitigación determinística de alucinaciones y streaming en tiempo real (Server-Sent Events).

---

## 2. Decisiones Arquitectónicas

### 2.1 Arquitectura en Capas (Service Layer Pattern)
Para evitar el antipatrón de *Fat Models* o *Fat Views*, la lógica de negocio se extrajo de `views.py` y se organizó en una capa de servicios dentro de `chatbot/app/services/`:

1. **`inventory_service.py`**:
   - Centraliza el ciclo de vida del catálogo de productos.
   - Paginación dinámica configurable (10, 15, 25, 50 y 'Todos') y búsqueda multifiltro (código, nombre, categoría, marca, estado, alertas).
   - Generación de los 8 reportes corporativos predefinidos.
   - Registro transaccional inmutable en el Kardex.
   - Mecanismo reactivo de invalidación de caché ante modificaciones en la base de datos.

2. **`ollama_service.py`**:
   - Encapsula la comunicación HTTP con la API REST de Ollama (`http://localhost:11434/api/generate`).
   - Implementa un **Pool de Conexiones Singleton** con `requests.Session` y reintentos automáticos para evitar agotamiento de sockets.
   - **Resolver de Hechos Determinístico (Anti-alucinaciones):** Ante preguntas de métricas o existencias, consulta el ORM directamente e inyecta hechos verificados en el prompt del sistema.
   - Control de fallas y desconexión de Ollama con respuestas claras para el usuario.
   - Caché en memoria `TTLCache` para respuestas frecuentes.

3. **`export_service.py`**:
   - Implementa el **Patrón Estrategia (`Strategy Pattern`)** mediante `BaseExportStrategy`.
   - `ChatHistoryExportStrategy`: Exporta consultas en JSON, CSV, Markdown, Texto plano y HTML formal.
   - `ProductCatalogExportStrategy`: Genera la **Hoja Oficial de Inventario Valorizado** (HTML/PDF imprimible con casillas de firma formal de almacén, compras y auditoría) y exportación a CSV con codificación `UTF-8 con BOM` para Microsoft Excel.
   - `importar_catalogo_csv`: Ingesta masiva de productos por lotes con actualización automática de existencias en el Kardex.

---

## 3. Patrones de Diseño Aplicados

### 3.1 Patrón Estrategia (Strategy Pattern)
* **Problema:** Múltiples formatos de exportación (CSV, PDF/HTML, JSON, Markdown) que saturaban las vistas con condicionales monolíticos.
* **Solución:** Definición de una interfaz común abstracta `BaseExportStrategy` con método `exportar()`. Clases concretas encapsulan las particularidades de renderizado y cabeceras HTTP de cada formato.

### 3.2 Patrón Singleton (Pool de Conexiones HTTP Persistentes)
* **Problema:** Múltiples peticiones HTTP a Ollama creaban y destruían sockets TCP, provocando latencia innecesaria y riesgo de *socket exhaustion*.
* **Solución:** Función `_get_session()` en `ollama_service.py` que mantiene una instancia única de `requests.Session` con `HTTPAdapter` (pool de 20 a 40 conexiones con keep-alive).

### 3.3 Patrón Registro Inmutable / Audit Ledger (Kardex Físico-Valorado)
* **Problema:** Modificar el contador de existencias directamente en la tabla de productos destruye la trazabilidad histórica de entradas, salidas y ajustes.
* **Solución:** Cada cambio genera un registro inmutable en el modelo `MovimientoStock`, auditando fecha, usuario, tipo (`ENTRADA`, `SALIDA`, `AJUSTE`), existencias previas, existencias resultantes y motivo formal.

---

## 4. Mitigación de Alucinaciones y Restricción de Dominio (IA Local)

El servicio de integración con Ollama implementa tres barreras de seguridad:
1. **Filtro Semántico de Entrada:** Si el usuario consulta sobre temas no pertinentes (deportes, cocina, política, entretenimiento), el backend declina responder antes de invocar a la IA:
   > *"No encontré información suficiente en el inventario para responder esa pregunta."*
2. **Inyección de Hechos Verificados (Grounding Determinístico):** Las preguntas sobre extremos de inventario (más caro, más barato, agotados, total de existencias) se calculan con el ORM de Django y se inyectan en el prompt como hechos irrefutables.
3. **Parámetros Estrictos de Inferencia:** Temperatura fijada en `0.05` y límite estricto de contexto (`num_ctx: 1200`, `num_predict: 140`) para respuestas ultra rápidas, concisas y fidedignas.

---

## 5. Rendimiento y Persistencia de Datos

1. **SQLite en Modo WAL (`Write-Ahead Logging`):** Permite concurrencia de lecturas mientras se ejecutan escrituras en el Kardex.
2. **Indexación B-Tree:** Cláusula `db_index=True` en `categoria`, `precio` y `estado` del modelo `Producto`.
3. **Caché en Capas:** Invalidación automática cada vez que se crea, edita, elimina o ajusta el stock de un producto.

---

# Referencias

Django Software Foundation. (2024). *Django: The web framework for perfectionists with deadlines* (Versión 5.1.6) [Software de computadora]. https://docs.djangoproject.com/

Fowler, M. (2002). *Patterns of enterprise application architecture*. Addison-Wesley Professional.

Gamma, E., Helm, R., Johnson, R., y Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley.

Google DeepMind. (2024). *Google Antigravity: Advanced agentic AI coding assistant* [Software de computadora]. https://deepmind.google/technologies/antigravity

Mozilla Developer Network. (2024). *Server-sent events*. MDN Web Docs. https://developer.mozilla.org/es/docs/Web/API/Server-sent_events

Ollama. (2024). *Ollama: Get up and running with large language models locally* (Versión 0.4.7) [Software de computadora]. https://ollama.com/

OpenCode Project. (2024). *OpenCode AI: Open-source coding agent* [Software de computadora]. https://opencode.ai/
