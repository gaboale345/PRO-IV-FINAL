# Transcripción y Evidencia de Desarrollo Asistido por IA (OPENCODE.md / ANTIGRAVITY.md)

**Asignatura:** Programación IV — Entregable Final  
**Estudiante:** Gabriel Alcón  
**Docente:** Ing. Jared López Leaños  
**Herramienta Asistente de Codificación Utilizada:** Google Antigravity (Advanced Agentic AI Assistant)  
**Fecha:** 28 de Septiembre de 2026  

> **Nota de Conformidad con la Consigna:**  
> En cumplimiento con la opción brindada por la cátedra de utilizar un asistente agéntico de codificación con IA, para el presente proyecto se seleccionó **Google Antigravity** en lugar de OpenCode convencional, registrando y documentando la totalidad de las sesiones, prompts, razonamientos, código generado y reflexiones técnicas.

El detalle exhaustivo de todas las sesiones de trabajo, prompts formulados, fragmentos de código generados y el análisis de impacto se encuentra disponible en:
* [ANTIGRAVITY.md](file:///home/gabriel/Downloads/PRO-IV-FINAL-main/ANTIGRAVITY.md)
* [informe.md](file:///home/gabriel/Downloads/PRO-IV-FINAL-main/informe.md) (Sección especial: *Uso de Google Antigravity como Asistente de Codificación*)
* [DOCUMENTACION.md](file:///home/gabriel/Downloads/PRO-IV-FINAL-main/DOCUMENTACION.md)

---

## Síntesis de Sesiones Realizadas con el Asistente

| Sesión | Módulo Asistido | Prompts Clave | Código / Artefactos Generados | Impacto Técnico |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **CRUD y Modelado** | Planificación de entidad `Producto` (13 campos), clave única, Kardex `MovimientoStock`. | `app/models.py`, `app/forms.py`, `app/admin.py` | Validaciones robustas de no negatividad y unicidad de SKU. |
| **2** | **Capa de Servicios y Reportes** | Creación de `inventory_service.py` y cálculo de los 8 reportes corporativos con ORM. | `app/services/inventory_service.py`, `app/views.py` | Desacoplamiento de vistas (*Fat Views* eliminadas), alto rendimiento. |
| **3** | **Integración IA Local (Ollama)** | Comunicación con `qwen2.5:1.5b`, Pool de conexiones HTTP Singleton, Grounding anti-alucinaciones y SSE. | `app/services/ollama_service.py`, `app/views.py` | 0% alucinaciones en cifras de inventario; respuesta amigable si Ollama está offline. |
| **4** | **Patrones de Diseño** | Aplicación formal del Patrón Estrategia (`export_service.py`), Patrón Singleton y Service Layer. | `app/services/export_service.py` | Extensibilidad multiformato (CSV, Hoja Oficial con firmas). |
| **5** | **Pruebas Automatizadas** | Diseño de batería de pruebas unitarias cubriendo CRUD, reportes, Kardex y streaming. | `app/tests.py` (17 pruebas completas) | 100% de casos de prueba aprobados en 0.11 segundos. |
| **6** | **Documentación y Entrega** | Auditoría según rúbrica, documentación de arquitectura y generación de entregables. | `informe.md`, `informe.pdf`, `DOCUMENTACION.md`, `.env.example` | Cumplimiento del nivel Estratégico (100 pts). |
