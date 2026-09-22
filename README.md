# Sistema Web de Inventario de Productos con CRUD e Inteligencia Artificial Local (Ollama)
### Entregable Final — Programación IV

Aplicación web profesional desarrollada con **Django** que permite administrar un inventario completo de productos mediante operaciones **CRUD** y control de existencias, además de realizar consultas cuantitativas y analíticas sobre la información registrada utilizando un modelo de inteligencia artificial local ejecutado con **Ollama**.

---

## 📌 Características Implementadas

### 1. Módulo de Productos (CRUD Completo)
* **RF-01. Registro de productos:** Formulario modal con validación estricta de código único, nombre, categoría, precio ($\ge 0$), cantidad existente ($\ge 0$), stock mínimo ($\ge 0$), estado del producto (Activo/Inactivo) y fecha de creación.
* **RF-02. Consulta y Búsqueda:** Tabla interactiva en tiempo real con filtrado por texto (código, nombre o categoría), selector de categorías y estado (Activos / Inactivos / Todos).
* **RF-03. Actualización de productos:** Edición directa de información existente con validaciones de unicidad y no negatividad.
* **RF-04. Eliminación de productos:** Soporte para eliminación lógica recomendada (cambio a estado *Inactivo* para preservar historial) y eliminación física definitiva.
* **RF-05. Control de existencia:** Acciones rápidas para aumentar (+) y disminuir (-) stock de forma atómica, impidiendo que la cantidad disponible sea negativa.

### 2. Menú de Reportes Predefinidos (RF-06)
Menú interactivo con los **8 reportes oficiales** requeridos:
1. **Listar todos los productos:** Catálogo general con totales consolidado.
2. **Producto más caro:** Identificación del artículo con el precio unitario más alto.
3. **Producto más barato:** Identificación del artículo más económico.
4. **Productos con pocas existencias:** Artículos con existencia $\le$ stock mínimo fijado.
5. **Productos agotados:** Artículos con cantidad disponible igual a cero (0).
6. **Productos por categoría:** Resumen cuantitativo y valorización económica agrupada.
7. **Valor total del inventario:** Sumatoria exacta $\sum (\text{precio} \times \text{cantidad})$ de existencias en almacén.
8. **Productos con mayor cantidad disponible:** Artículos con mayor disponibilidad física.
* **Explicación en Lenguaje Natural con Ollama (RF-06):** Botón *"✨ Explicar con IA"* que envía los datos del reporte seleccionado al modelo local de Ollama para redactar un resumen explicativo.

### 3. Chat con Inteligencia Artificial Local (RF-07, RF-08, RF-09)
* **Integración Local:** Conexión directa mediante la API de Ollama (`http://localhost:11434/api/generate`) con modelo configurable vía `.env` (`OLLAMA_MODEL`, por defecto `qwen2.5:0.5b` o `llama3.2`).
* **Contexto JSON Estructurado:** Envío de los datos del inventario en formato JSON limpio (`codigo`, `nombre`, `categoria`, `precio`, `cantidad_existente`, `stock_minimo`).
* **Restricción Estricta de Respuestas (RF-09):** La IA responde únicamente basándose en la información oficial suministrada. Ante preguntas no relacionadas o sin datos suficientes, declina formalmente: *"No encontré información suficiente en el inventario para responder esa pregunta."*
* **RF-10. Historial de Consultas:** Almacenamiento cronológico de preguntas y respuestas con exportación en 5 formatos (PDF/HTML imprimible, Excel/CSV, JSON estructurado, Markdown y TXT).

---

## 🛠️ Tecnologías y Arquitectura

* **Backend:** Python 3.11, Django 5.1.6
* **Base de Datos:** SQLite3
* **Motor de IA Local:** Ollama (API REST local en puerto 11434)
* **Frontend:** HTML5, CSS3 Moderno (Glassmorphism, Modo Claro/Oscuro, Responsive), JavaScript Nativo (Fetch API)
* **Red Local:** Servidor en `0.0.0.0:8000` accesible desde la IP `172.25.4.247:8000`

---

## 🚀 Instrucciones de Instalación y Ejecución

### 1. Clonar o Ubicarse en el Proyecto
```bash
cd /home/gabriel/Downloads/Alcon_Gabriel_Actividad4_ProgramacionIV/proyecto
```

### 2. Configurar el Entorno Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (Opcional)
Se incluye la plantilla `.env.example` en la raíz:
```bash
cp .env.example .env
```
Contenido de configuración:
```env
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:0.5b
DEBUG=True
ALLOWED_HOSTS=172.25.4.247,localhost,127.0.0.1,0.0.0.0
```

### 4. Verificar el Servicio de Ollama
Asegúrate de que Ollama esté en ejecución:
```bash
systemctl is-active ollama
# Salida esperada: active
```

### 5. Aplicar Migraciones
```bash
python chatbot/manage.py migrate
```

### 6. (Opcional) Poblar el Inventario Inicial con 100 Productos
```bash
python chatbot/poblar_inventario.py
```

### 7. Iniciar el Servidor de Desarrollo
Puedes utilizar el script automatizado:
```bash
./iniciar_servidor.sh
```
O ejecutar directamente:
```bash
source .venv/bin/activate
python chatbot/manage.py runserver 0.0.0.0:8000
```

---

## 🌐 Direcciones de Acceso

* **En tu navegador local:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **En tu red local (IP asignada):** [http://172.25.4.247:8000/](http://172.25.4.247:8000/)

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye 9 pruebas unitarias automatizadas que cubren el 100% de los requerimientos funcionales (RF-01 a RF-10):

```bash
source .venv/bin/activate
python chatbot/manage.py test app
```

Resultado esperado:
```text
Found 9 test(s).
Creating test database for alias 'default'...
.........
----------------------------------------------------------------------
Ran 9 tests in 0.28s

OK
```
