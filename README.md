# Sistema Empresarial de Gestión de Inventario, Kardex Valorizado e Inteligencia Artificial Local (Ollama)
### Proyecto Final — Programación IV | Universidad

Aplicación web empresarial desarrollada en **Django** que implementa una arquitectura modular por capas (**Service Layer**) y patrones de diseño avanzados (**Strategy**, **Singleton**, **Audit Ledger**), integrando la gestión de inventario con control de existencias, auditoría mediante **Kardex físico-valorado**, exportación/importación masiva y un asistente analítico local impulsado por **Ollama** con interacción por voz (STT / TTS).

---

## 📌 Arquitectura y Patrones de Diseño Implementados

El sistema fue diseñado superando el modelo estándar monolítico de Django, estructurándose mediante buenas prácticas de ingeniería de software:

1. **Capa de Servicios (`Service Layer`):** Desacoplamiento total de la lógica de negocio respecto a los controladores HTTP (`views.py`):
   - `inventory_service.py`: Gestión de catálogo, métricas financieras, reportes analíticos y ledger inmutable de Kardex.
   - `ollama_service.py`: Comunicación con el runtime de IA local, resolución de hechos de inventario y mitigación de alucinaciones.
   - `export_service.py`: Transformación y generación de reportes y hojas oficiales.
2. **Patrón Estrategia (`Strategy Pattern`):** Interfaz unificada `BaseExportStrategy` que desacopla los algoritmos de serialización en tiempo de ejecución para múltiples formatos:
   - `ChatHistoryExportStrategy`: Exportación del historial analítico en PDF/HTML, CSV, JSON, Markdown y TXT.
   - `ProductCatalogExportStrategy`: Generación de Hoja Oficial de Inventario Valorizado con casillas de firma de auditoría y exportación en CSV tabulado.
3. **Patrón Singleton:** Conexiones HTTP persistentes (`requests.Session`) con reutilización de sockets (keep-alive) y reintentos adaptativos contra la API de Ollama.
4. **Patrón Registro Inmutable / Audit Ledger (Kardex):** Modelo `MovimientoStock` que registra atómicamente cada alteración física o contable del inventario con trazabilidad total (`stock_previo`, `stock_resultante`, `motivo`, `usuario`, `fecha`).

---

## 🌟 Funcionalidades Principales

### 1. Catálogo y Operaciones CRUD (RF-01 a RF-05)
* **RF-01. Registro de Productos:** Validación estricta en servidor y cliente de códigos únicos, nombres, categorías, marcas, precios y stocks mínimos. Genera automáticamente movimiento de apertura en Kardex.
* **RF-02. Consulta, Filtrado y Paginación:** Búsqueda en tiempo real por texto, filtrado por categorías, estado y selector de paginación interactiva (10, 15, 25, 50 o todos los artículos) sin recarga de página.
* **RF-03. Modificación:** Edición fluida con recálculo de estados y registro de auditoría.
* **RF-04. Eliminación Segura:** Eliminación lógica (desactivación para salvaguardar historial contable) o física.
* **RF-05. Control de Existencias Atómico:** Aumento (recepción) y disminución (despacho) con motivo obligatorio, impidiendo valores negativos.

### 2. Trazabilidad Total: Módulo de Kardex
* **Historial Contable por Producto:** Modal interactivo que expone cada transacción cronológica: entradas, salidas y ajustes de inventario.
* **Auditoría Transaccional:** Registro de quién, cuándo y por qué se alteró cada existencia en almacén.

### 3. Reportes Analíticos e Inteligencia Artificial (RF-06 a RF-09)
* **Menú de 8 Reportes Predefinidos:**
  1. Catálogo completo valorizado.
  2. Producto de mayor precio unitario.
  3. Producto más económico.
  4. Alerta de existencias críticas ($\le$ stock mínimo).
  5. Productos agotados (stock = 0).
  6. Existencias y valoración agrupada por categoría.
  7. Valor total financiero del inventario ($\sum \text{precio} \times \text{stock}$).
  8. Artículos con mayor disponibilidad física.
* **Explicación Analítica con IA:** Botón *"✨ Explicar con IA"* que analiza las cifras del reporte en segundos.
* **Chatbot Analítico Local con Ollama:**
  - Modelo configurable vía `.env` (ej. `qwen2.5:1.5b` o `qwen2.5:0.5b`).
  - Inferencia en tiempo real mediante **Server-Sent Events (SSE)** con efecto máquina de escribir.
  - **Resolución de Hechos sin Alucinaciones (RF-09):** Respuesta fidedigna sobre el inventario. Ante preguntas ajenas o sin información suficiente, declina formalmente.
  - **Sugerencias Rápidas (Chips):** Accesos directos a preguntas frecuentes de gestión.
* **Interacción por Voz (Multimodal):**
  - **Reconocimiento de Voz (STT):** Dictado por micrófono usando la Web Speech API nativa.
  - **Síntesis de Voz (TTS):** Botón `🔊` en cada respuesta para lectura en voz alta en español.

### 4. Importación y Exportación Oficial
* **Hoja Oficial de Inventario Valorizado (PDF Imprimible):** Documento formal con membrete, KPI consolidados, tabla valorizada en Bolivianos (`Bs.`) y casillas de firma para Responsable de Almacén, Jefe de Compras y Auditor.
* **Exportación en CSV / Excel:** Descarga directa compatible con hojas de cálculo.
* **Importación Masiva en CSV:** Carga por lotes de nuevos productos o actualización de existentes con apertura automática en Kardex.

---

## 💵 Localización Monetaria: Mercado Boliviano
Todos los precios se encuentran expresados y calculados en **Bolivianos (`Bs.` / BOB)**, reflejando el valor de reposición real del mercado de componentes y hardware en Bolivia (tipo de cambio de referencia comercial ~12.20 Bs/USD):
- Tarjetas de Video de Gama Alta: ASUS ROG Strix RTX 4090 ~ Bs. 26,839.88
- Procesadores: AMD Ryzen 9 7950X3D ~ Bs. 8,527.80
- Almacenamiento SSD NVMe 4TB ~ Bs. 4,634.78
- Periféricos y accesorios: desde Bs. 73.20

---

## 🛠️ Tecnologías Empleadas

* **Backend:** Python 3.11, Django 5.1.6
* **Base de Datos:** SQLite 3 en modo **WAL (Write-Ahead Logging)** con índices B-Tree (`db_index=True`)
* **Motor de IA Local:** Ollama 0.4.7+ (API REST en puerto 11434)
* **Frontend:** HTML5 semántico, CSS3 moderno con variables dinámicas (Glassmorphism, Modo Claro/Oscuro, Responsive Design), JavaScript nativo (Fetch API, Web Speech API)
* **Contenedores:** Docker y Docker Compose para despliegue listo para producción

---

## 🚀 Puesta en Marcha

### Opción A. Ejecución Nativa en Linux

1. **Clonar y acceder al directorio:**
   ```bash
   cd /home/gabriel/Downloads/PRO-IV-FINAL-main
   ```

2. **Activar el entorno virtual:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Verificar que Ollama esté activo:**
   ```bash
   systemctl is-active ollama
   # O iniciar manualmente: ollama serve &
   ```

4. **Aplicar migraciones:**
   ```bash
   python chatbot/manage.py migrate
   ```

5. **Iniciar el servidor:**
   ```bash
   ./iniciar_servidor.sh
   # O directamente: python chatbot/manage.py runserver 0.0.0.0:8000
   ```

---

### Opción B. Despliegue con Docker Compose

```bash
docker compose up -d --build
```
El contenedor web levantará en el puerto `8000` enlazado al servicio de Ollama.

---

## 🌐 URLs de Acceso

* **Servidor Local:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Acceso desde Red Local:** [http://172.25.4.247:8000/](http://172.25.4.247:8000/)
* **Panel de Administración Django:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con **17 pruebas unitarias** que cubren el 100% de los requerimientos funcionales y las extensiones avanzadas:

```bash
source .venv/bin/activate
python chatbot/manage.py test app
```

**Resultado obtenido:**
```text
Found 17 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................
----------------------------------------------------------------------
Ran 17 tests in 0.096s

OK
Destroying test database for alias 'default'...
```
