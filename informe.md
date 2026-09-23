# Informe Técnico de Proyecto Final: Sistema Empresarial de Gestión de Inventario, Kardex Físico-Valorado y Asistente Analítico con Inteligencia Artificial Local (Ollama)
## Asignatura: Programación IV — Carrera de Ingeniería de Sistemas / Informática

---

### Portada y Datos del Proyecto
* **Asignatura:** Programación IV
* **Unidad / Ejes Temáticos:** Frameworks Web Avanzados (Django), Arquitectura de Software, Patrones de Diseño, Inteligencia Artificial Local y Trazabilidad Contable.
* **Tema:** Proyecto Final — Sistema Integral de Inventario, Auditoría de Stock en Kardex, Reportes Gerenciales y Chatbot Analítico Offline con Ollama.
* **Estudiante:** Gabriel Alcón
* **Entorno de Desarrollo y Despliegue:** Debian Linux 12 x86_64, Python 3.11.2, Django 5.1.6, Ollama 0.4.7+, SQLite3 (Modo WAL), Docker & Docker Compose.
* **Fecha:** Septiembre de 2026

---

## 1. Resumen Ejecutivo

El presente proyecto final consolida las competencias de desarrollo backend profesional, ingeniería de software aplicada e integración de modelos de lenguaje de gran escala (**LLMs**) operando de manera 100% local y soberana mediante **Ollama**.

El sistema desarrollado resuelve la problemática de control de inventarios y toma de decisiones empresariales combinando:
1. Un módulo transaccional robusto para el mantenimiento del catálogo de productos (**CRUD** completo bajo los estándares RF-01 al RF-05).
2. Un sistema inmutable de trazabilidad contable mediante **Kardex físico-valorado**, donde cada ingreso, egreso o ajuste queda registrado de forma atómica.
3. Un motor analítico con **8 reportes gerenciales predefinidos** y síntesis automática generada por inteligencia artificial.
4. Un asistente virtual analítico en lenguaje natural con **Server-Sent Events (SSE)**, mitigación de alucinaciones mediante resolución determinística de hechos de inventario, y capacidades multimodales de voz (**Speech-to-Text** y **Text-to-Speech**).
5. Cumplimiento de estándares de auditoría formal mediante la generación de **Hojas Oficiales de Inventario Valorizado** con casillas de firma y mecanismos de importación/exportación masiva en CSV.

---

## 2. Arquitectura de Software y Patrones de Diseño

Para evitar el antipatrón habitual de *Fat Models* o *Fat Views* en Django, el proyecto fue refactorizado adoptando una **Arquitectura en Capas (Layered Architecture)** y aplicando patrones de diseño reconocidos por la industria:

```
[ Cliente Web / UI ] <--> [ Controladores HTTP (views.py) ]
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
[ inventory_service.py ]   [ ollama_service.py ]   [ export_service.py ]
   - Reglas de Negocio        - Pool Singleton        - Patrón Strategy
   - Paginación Dinámica      - Resolver de Hechos    - Hoja PDF Oficial
   - Ledger Kardex            - Caché TTLCache        - Export / Import CSV
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
                       [ Capa de Datos (models.py) ]
                       [ SQLite 3 - Modo WAL + Índices ]
```

### 2.1 Patrón Capa de Servicios (`Service Layer Pattern`)
Se desacopló la lógica de negocio de los controladores HTTP, delegándola en módulos especializados dentro de `chatbot/app/services/`:
* **`inventory_service.py`:** Centraliza las consultas filtradas y paginadas, recálculo de valoraciones económicas consolidadas, ejecución de los 8 reportes corporativos y registro de transacciones en el Kardex.
* **`ollama_service.py`:** Encapsula la interacción con el runtime de Ollama, construcción de prompts contextuales enriquecidos con datos reales de la base de datos y control de fallas en red local.
* **`export_service.py`:** Coordina la serialización multiformato y la ingesta masiva de archivos tabulados.

### 2.2 Patrón Estrategia (`Strategy Pattern`)
Para satisfacer los requisitos de exportación del historial del chat y del catálogo de productos sin recurrir a estructuras de control monolíticas (`if/elif/else`), se implementó el patrón Strategy mediante una clase base abstracta:

```python
class BaseExportStrategy(ABC):
    @abstractmethod
    def exportar(self, datos, **kwargs):
        """Retorna una tupla: (contenido: str|bytes, content_type: str, filename: str)"""
        pass
```

Estrategias concretas desarrolladas:
* `ChatHistoryExportStrategy`: Exporta en PDF/HTML con diseño formal, CSV, JSON, Markdown y Texto plano.
* `ProductCatalogExportStrategy`: Genera la **Hoja Oficial de Inventario Valorizado** (HTML/PDF con casillas de rúbrica de auditoría) y exportación de datos tabulados en CSV con codificación `UTF-8 con BOM` para total compatibilidad con Microsoft Excel.

### 2.3 Patrón Singleton (Pool de Conexiones Persistentes HTTP)
Las consultas continuas al runtime de Ollama a través de llamadas HTTP repetitivas pueden saturar los descriptores de archivos del sistema operativo si se instancian clientes en cada petición. Se implementó una sesión singleton reutilizable con `urllib3.util.retry.Retry` y `HTTPAdapter`:
```python
_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=40,
            max_retries=Retry(total=2, backoff_factor=0.2)
        )
        _session.mount('http://', adapter)
        _session.mount('https://', adapter)
    return _session
```

### 2.4 Patrón Registro Inmutable / Audit Ledger (Kardex Físico-Valorado)
El inventario no se limita a un contador mutable en la tabla de productos. Cada alteración de existencias queda auditada en el modelo `MovimientoStock`, registrando:
* Tipo de transacción: `ENTRADA` (ingreso por proveedor o compra), `SALIDA` (despacho, venta), `AJUSTE` (corrección física por inventario) o `APERTURA`.
* Existencias antes del movimiento (`stock_previo`) y existencias resultantes (`stock_resultante`).
* Justificación o motivo formal del movimiento.
* Usuario y marca temporal inmutable.

---

## 3. Requerimientos Funcionales Implementados

### 3.1 Módulo Transaccional de Catálogo (RF-01 al RF-05)
* **RF-01 (Registro):** Formulario modal con validación estricta de código único, precio positivo ($\ge 0$), existencias positivas y stock mínimo. Crea automáticamente el registro inicial de apertura en el Kardex.
* **RF-02 (Consulta, Búsqueda y Paginación):** Visualización interactiva en tabla HTML responsiva. Incorpora selector de paginación interactiva (10, 15, 25, 50 y 'Todos') sin refrescar la página, búsqueda instantánea por código/nombre/categoría y filtro por estado.
* **RF-03 (Modificación):** Edición completa de campos con recálculo dinámico del estado del stock (`En Stock`, `Stock Bajo`, `Agotado`). Si el stock cambia, se asienta un movimiento de ajuste en el Kardex.
* **RF-04 (Eliminación Lógica y Física):** Soporte para desactivación lógica (`estado=False`) preservando la integridad referencial histórica del Kardex, además de eliminación física opcional.
* **RF-05 (Ajuste Rápido de Stock):** Botones `+` y `-` que abren un modal para ingresar la cantidad y el motivo del movimiento. Se bloquea a nivel de base de datos cualquier intento de generar existencias negativas.

### 3.2 Menú de Reportes Corporativos (RF-06)
El sistema cuenta con un panel visual que genera los 8 reportes oficiales requeridos por la materia:
1. **Catálogo Completo:** Visión general de todos los productos activos.
2. **Producto más Caro:** Localización inmediata del ítem con mayor precio unitario.
3. **Producto más Barato:** Localización del ítem de menor costo.
4. **Pocas Existencias:** Detección de artículos cuyo stock es inferior o igual al stock mínimo.
5. **Agotados:** Artículos con existencia física en cero (0).
6. **Agrupación por Categoría:** Cantidad de ítems y valoración total agrupada.
7. **Valor Total del Inventario:** Cálculo económico exacto de existencias $\sum (\text{precio} \times \text{stock})$.
8. **Mayor Disponibilidad:** Artículos con mayor volumen físico en almacén.
* **Explicación Analítica con IA:** Botón interactivo que transmite la estructura del reporte a Ollama para obtener un análisis cualitativo en lenguaje natural en menos de 2 segundos.

### 3.3 Chatbot Analítico Local con Ollama (RF-07 al RF-10)
* **Inferencia Offline en CPU:** Integración nativa con Ollama en el puerto local 11434, compatible con modelos cuantizados de alta eficiencia (`qwen2.5:1.5b` o `qwen2.5:0.5b`).
* **Streaming en Tiempo Real (SSE):** Implementación de Server-Sent Events en `/chat/stream/` para emitir los tokens conforme son generados por el modelo, logrando una sensación de inmediatez.
* **Resolución Determinística de Hechos (RF-09):** Mitigación total de alucinaciones en preguntas analíticas (ej. "¿cuál es el producto más caro?", "¿cuántas unidades hay en total?", "¿qué productos están agotados?"). El backend calcula las respuestas directas sobre el ORM y las inyecta como hechos verificados en el prompt. Ante preguntas no pertinentes a la empresa, el modelo declina formalmente según la directiva del proyecto.
* **Chips de Sugerencia Rápida:** Botones de consulta frecuente en la interfaz para agilizar la interacción del usuario.

### 3.4 Interacción Multimodal por Voz (STT y TTS)
* **Reconocimiento de Voz (Speech-to-Text):** Botón de micrófono con animación pulsante en el campo de entrada del chat. Emplea la API nativa `webkitSpeechRecognition` para transcribir la voz del operador al español en tiempo real.
* **Síntesis de Voz (Text-to-Speech):** Botón `🔊 Escuchar` integrado en cada burbuja de respuesta del asistente, utilizando `window.speechSynthesis` configurado con voz en español (`es-ES` / `es-419`).

### 3.5 Generación de Hoja Oficial de Inventario e Importación Masiva
* **Hoja Oficial de Inventario Valorizado:** Documento formal imprimible a PDF que incluye membrete institucional, cuadro consolidado de KPI (total referencias, unidades en almacén, valoración total en Bs.), tabla valorizada y casillas de firma formal para:
  1. Responsable de Almacén.
  2. Jefe de Inventarios y Compras.
  3. Auditor de Sistemas / Fiscalización.
* **Importación Masiva en CSV:** Carga por lotes de archivos CSV con creación de nuevos ítems, actualización de precios/stocks de ítems existentes y registro automático de aperturas o ajustes en el Kardex.

---

## 4. Localización Económica al Mercado Boliviano

Para garantizar pertinencia contextual con el entorno real del estudiante, los 100 productos del inventario y las interfaces fueron adaptados estrictamente a **Bolivianos (`Bs.` / BOB)**, tomando como base los valores reales de reposición del mercado boliviano de hardware y componentes electrónicos (tasa de referencia comercial ~12.20 Bs/USD):

| Código | Producto | Categoría | Stock | Precio Unitario (Bs.) | Valorización (Bs.) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `GPU-NV-4090-ROG` | ASUS ROG Strix GeForce RTX 4090 24GB | Tarjetas de Video | 8 | Bs. 26,839.88 | Bs. 214,719.04 |
| `CPU-AMD-7950X3D` | AMD Ryzen 9 7950X3D (16C/32T) | Procesadores | 6 | Bs. 8,527.80 | Bs. 51,166.80 |
| `SSD-SAM-990P-4TB` | Samsung 990 PRO NVMe M.2 SSD 4TB | Almacenamiento | 7 | Bs. 4,634.78 | Bs. 32,443.46 |
| `MON-ASUS-PG42UQ` | ASUS ROG Swift OLED 41.5" 4K 138Hz | Monitores | 3 | Bs. 18,287.80 | Bs. 54,863.40 |
| `CAB-CAT6-UTP` | Cable de Red UTP Cat6 305m Nexxt | Redes y Conectividad | 22 | Bs. 915.00 | Bs. 20,130.00 |

*Valor total de existencias en almacén:* Supera los **Bs. 750,000.00**, reflejando la dimensión económica de una empresa de tecnología y suministros informáticos en Bolivia.

---

## 5. Endurecimiento de Base de Datos y Optimización

1. **Modo WAL en SQLite (`Write-Ahead Logging`):**  
   Por defecto, SQLite utiliza journal de retroceso que bloquea la base de datos completa durante escrituras. Se activó el modo WAL:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   ```
   Esto permite que múltiples lecturas concurrentes (reportes, chat de IA, consultas API) se ejecuten en paralelo mientras se registran movimientos en el Kardex sin bloqueos.
2. **Indexación B-Tree:**  
   Se aplicó `db_index=True` a los campos de filtrado y ordenación frecuente (`categoria`, `precio`, `estado`), reduciendo el tiempo de consulta de $O(N)$ a $O(\log N)$.
3. **Caché en Memoria (`Cache Aside`):**  
   Uso de `locmem` de Django y `TTLCache` para respuestas frecuentes de Ollama y estadísticas de cabecera, con invalidación reactiva inmediata cada vez que ocurre un cambio en el inventario.

---

## 6. Despliegue y Contenedorización (Docker)

Se diseñó la infraestructura para ejecución llave en mano:
* **`Dockerfile`:** Imagen optimizada basada en `python:3.11-slim`, con instalación de dependencias y ejecución no root.
* **`docker-compose.yml`:** Orquesta dos servicios interconectados:
  - `web`: Servidor web Django exponiendo el puerto 8000 y montando el volumen de persistencia para `db.sqlite3`.
  - `ollama`: Contenedor oficial `ollama/ollama:latest` exponiendo el puerto 11434 con volumen persistente para los modelos descargados.

---

## 7. Batería de Pruebas Automatizadas

Se elaboró una suite integral de **17 pruebas unitarias** en `chatbot/app/tests.py`, evaluando el 100% de los requerimientos funcionales, la integridad transaccional del Kardex, la paginación dinámica y las exportaciones:

```bash
python chatbot/manage.py test app -v 2
```

### Matriz de Resultados de Verificación:
| Caso de Prueba | Requerimiento / Componente Evaluado | Resultado |
| :--- | :--- | :---: |
| `test_pagina_principal_carga_correctamente` | Carga de UI en español, HTTP 200 y metadatos de red | **PASS** |
| `test_rf01_registro_producto_exitoso` | Alta de producto con campos válidos | **PASS** |
| `test_rf01_registro_producto_falla_por_codigo_duplicado_o_precio_negativo` | Validación de unicidad y no negatividad | **PASS** |
| `test_rf02_consulta_y_busqueda_productos` | Filtrado por código y categoría | **PASS** |
| `test_rf03_actualizacion_producto` | Modificación de datos y persistencia | **PASS** |
| `test_rf04_eliminacion_logica_y_cambio_estado` | Eliminación lógica para salvaguardar auditoría | **PASS** |
| `test_rf05_control_existencia_aumentar_y_disminuir` | Aumento y disminución con bloqueo de stock negativo | **PASS** |
| `test_rf06_menu_reportes_predefinidos_8_opciones` | Ejecución exitosa de los 8 reportes corporativos | **PASS** |
| `test_rf07_rf08_rf09_chat_con_ollama` | Interacción con Ollama y restricción de dominio | **PASS** |
| `test_exactitud_agotados_y_extremos_inventario` | Resolver de hechos determinístico sin alucinaciones | **PASS** |
| `test_optimizacion_cache_chat` | Caché en memoria y reducción de latencia | **PASS** |
| `test_chat_stream_sse_endpoint` | Emisión Server-Sent Events con UTF-8 íntegro | **PASS** |
| `test_kardex_registro_movimientos_y_consulta_api` | Registro atómico de movimientos y consulta del ledger | **PASS** |
| `test_paginacion_catalogo_productos` | Paginación interactiva con tamaños parametrizados | **PASS** |
| `test_exportacion_catalogo_csv` | Exportación de catálogo en CSV con cabeceras correctas | **PASS** |
| `test_exportacion_catalogo_pdf_hoja_oficial` | Generación de Hoja Oficial con firmas y moneda Bs. | **PASS** |
| `test_importacion_catalogo_csv_valido` | Ingesta masiva CSV con alta automática en Kardex | **PASS** |

**Resultado final:** 17 tests ejecutados en 0.096s — **100% Satisfactorio (OK)**.

---

## 8. Conclusiones

1. **Eficiencia y Soberanía Tecnológica:** La utilización de modelos locales compactos como **Qwen 2.5 (1.5b)** permite prescindir de suscripciones a APIs externas de pago y garantiza absoluta privacidad de los datos corporativos, operando con tiempos de respuesta inferiores a 2 segundos en CPU estándar.
2. **Madurez Arquitectónica:** La transición de un esquema tradicional de vistas monolíticas a una **Capa de Servicios** con aplicación de los patrones **Strategy**, **Singleton** y **Audit Ledger** demuestra la aplicabilidad de los principios de diseño de software empresarial aprendidos a lo largo de la materia Programación IV.
3. **Valor Empresarial:** La incorporación del **Kardex valorizado**, la emisión de la **Hoja Oficial de Inventario con firmas** y la interacción por voz transforman el proyecto de una simple aplicación académica en una solución de software lista para ser implantada en comercios o empresas del medio nacional.

---

## 9. Referencias Bibliográficas

1. Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
2. Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.
3. Django Software Foundation. (2024–2026). *Django Documentation (v5.1)*. https://docs.djangoproject.com/
4. Ollama Community. (2024–2026). *Ollama Documentation: Local AI execution and REST API reference*. https://ollama.com/
5. Mozilla Developer Network (MDN). (2025–2026). *Web Speech API: SpeechRecognition and SpeechSynthesis Interfaces*. https://developer.mozilla.org/
