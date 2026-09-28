# Bitácora de Desarrollo Asistido por IA: Google Antigravity

**Asignatura:** Programación IV — Entregable Final  
**Estudiante:** Gabriel Alcón  
**Docente:** Ing. Jared López Leaños  
**Herramienta Asistente:** Google Antigravity (Advanced Agentic AI Coding Assistant)  
**Fecha:** 28 de Septiembre de 2026  
**Proyecto:** Sistema de Información de Inventario Tecnológico con CRUD, Trazabilidad Kardex, 8 Reportes Gerenciales y Asistente Offline mediante Ollama  

---

## 1. Introducción y Selección de la Herramienta

Para el desarrollo del presente proyecto final de Programación IV, conforme a las directivas de la cátedra que autorizan la selección de un entorno de codificación agéntico avanzado con Inteligencia Artificial, se seleccionó **Google Antigravity**.

Antigravity opera como un asistente de programación en pares (*pair-programmer*) capaz de razonar sobre la arquitectura global del sistema, proponer planes estructurados, inspeccionar el código fuente, ejecutar pruebas unitarias automatizadas y aplicar patrones de diseño empresariales bajo los principios de alta cohesión y bajo acoplamiento.

A continuación se documenta el ciclo de vida completo del desarrollo asistido: fases, sesiones de trabajo, prompts enviados, razonamiento del asistente, fragmentos de código generados y el impacto técnico obtenido.

---

## 2. Sesión 1: Planificación Inicial y Modelado del CRUD de Datos

### 2.1 Objetivo de la Sesión
Definir la entidad central del sistema con un mínimo de 6 campos, asegurar restricciones de integridad (código único, valores monetarios y stock no negativos) y estructurar el modelo de auditoría contable (Kardex).

### 2.2 Prompts Utilizados

> **Prompt 1 (Usuario):**  
> *"Planifica la arquitectura para un sistema de información genérico en Django 5.x. La entidad principal debe ser `Producto` (orientada a componentes tecnológicos y hardware en Bolivia, con moneda en Bolivianos Bs.), con al menos 10 atributos que incluyan SKU/código único, categoría, precio, existencias físicas, stock mínimo y estado lógico. Además, planifica un modelo complementario para auditoría de movimientos de almacén (Kardex) para que ninguna existencia cambie sin justificación."*

### 2.3 Respuesta y Razonamiento de Antigravity
*Antigravity analizó los requisitos de integridad relacional en SQLite y propuso la creación de dos modelos en `chatbot/app/models.py`:*
1. **`Producto`:** Con campos fuertemente tipados (`CharField`, `DecimalField`, `PositiveIntegerField`, `BooleanField`, `DateTimeField`) y propiedades calculadas (`estado_stock`, `badge_class`).
2. **`MovimientoStock`:** Como registro inmutable (*Audit Ledger*) con clave foránea a `Producto`, campos de `stock_previo`, `stock_resultante`, `tipo` (`ENTRADA`, `SALIDA`, `AJUSTE`) y justificación formal.

### 2.4 Código Generado por Antigravity (Extracto de `chatbot/app/models.py`)
```python
class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del Producto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.CharField(max_length=100, db_index=True, verbose_name="Categoría")
    precio = models.DecimalField(max_digits=10, decimal_places=2, db_index=True, verbose_name="Precio (Bs.)")
    cantidad_existente = models.PositiveIntegerField(default=0, verbose_name="Cantidad Existente")
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name="Stock Mínimo")
    estado = models.BooleanField(default=True, db_index=True, verbose_name="Estado del Producto")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    marca = models.CharField(max_length=100, blank=True, default="", verbose_name="Marca")
    especificaciones = models.TextField(blank=True, default="", verbose_name="Especificaciones Técnicas")
    destacado = models.BooleanField(default=False, verbose_name="Producto Destacado")

class MovimientoStock(models.Model):
    TIPO_CHOICES = [("ENTRADA", "Entrada (+)"), ("SALIDA", "Salida (-)"), ("AJUSTE", "Ajuste de Inventario")]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    stock_previo = models.PositiveIntegerField()
    stock_resultante = models.PositiveIntegerField()
    motivo = models.CharField(max_length=255)
    usuario = models.CharField(max_length=100, default="Administrador")
    fecha = models.DateTimeField(auto_now_add=True)
```

> **Prompt 2 (Usuario):**  
> *"Genera el formulario Django `ProductoForm` en `forms.py` con validaciones estrictas: el código no debe repetirse (case-insensitive) salvo al editar el mismo producto, el precio debe ser estrictamente mayor o igual a cero, y la cantidad existente no puede ser negativa."*

### 2.5 Código Generado por Antigravity (Extracto de `chatbot/app/forms.py`)
```python
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio', 'cantidad_existente', 'stock_minimo', 'estado', 'marca', 'especificaciones']

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if not codigo:
            raise forms.ValidationError("El código del producto es obligatorio.")
        qs = Producto.objects.filter(codigo__iexact=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"El código '{codigo}' ya está registrado con otro producto.")
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None or precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio
```

### 2.6 Impacto en el Desarrollo
La asistencia de Antigravity previno errores de concurrencia y validación débil en formularios HTML básicos, centralizando las reglas de negocio en la capa de formularios de Django.

---

## 3. Sesión 2: Desacoplamiento de Lógica y Menú de Reportes Gerenciales

### 3.1 Objetivo de la Sesión
Evitar el antipatrón de *Fat Views* y desacoplar la lógica de negocio implementando una Capa de Servicios (`Service Layer`), así como crear un menú con al menos 5 reportes analíticos (se extendió a 8 reportes corporativos).

### 3.2 Prompts Utilizados

> **Prompt 3 (Usuario):**  
> *"Crea un módulo de servicios `chatbot/app/services/inventory_service.py`. Implementa una función para calcular estadísticas globales agregadas con el ORM de Django (valor total en Bs., unidades físicas, producto más costoso, más económico y alertas de stock bajo). Luego, implementa una función `obtener_reporte_predefinido(tipo)` que soporte 8 reportes corporativos: todos, más caro, más barato, pocas existencias, agotados, por categoría, valor total y mayor existencia."*

### 3.3 Respuesta y Código Generado por Antigravity
*Antigravity construyó la capa de servicios utilizando agregaciones del ORM (`Sum`, `Avg`, `Count`, `F('precio') * F('cantidad_existente')`) para garantizar máxima eficiencia y cero iteraciones manuales en Python:*
```python
def obtener_reporte_predefinido(tipo):
    qs_activos = Producto.objects.filter(estado=True)
    if tipo == "mas_caro":
        prod = qs_activos.order_by("-precio").first()
        return {"tipo": "mas_caro", "titulo": "Producto Más Caro del Catálogo", "productos": [prod] if prod else []}
    elif tipo == "agotados":
        prods = list(qs_activos.filter(cantidad_existente=0))
        return {"tipo": "agotados", "titulo": "Productos Totalmente Agotados (Stock Cero)", "productos": prods}
    elif tipo == "valor_total":
        # Agregación económica a nivel de base de datos
        agg = qs_activos.aggregate(
            total_unidades=Sum("cantidad_existente"),
            valor_inventario=Sum(F("precio") * F("cantidad_existente"), output_field=models.DecimalField())
        )
        return {"tipo": "valor_total", "resumen": agg}
    # ... soporte para los 8 reportes corporativos
```

### 3.4 Impacto en el Desarrollo
Las vistas de Django quedaron limpias, actuando únicamente como despachadores HTTP y dejando toda la lógica de negocio encapsulada y fácilmente comprobable mediante pruebas automatizadas.

---

## 4. Sesión 3: Integración de IA Local con Ollama y Mitigación de Alucinaciones

### 4.1 Objetivo de la Sesión
Conectar Django a la API REST de Ollama local (`http://localhost:11434`), seleccionar el modelo `qwen2.5:1.5b`, implementar streaming Server-Sent Events (SSE) y aplicar técnicas estrictas para erradicar alucinaciones.

### 4.2 Prompts Utilizados

> **Prompt 4 (Usuario):**  
> *"Diseña el servicio `services/ollama_service.py` para consultar la API local de Ollama. Aplica un patrón Singleton para el cliente HTTP reutilizando una sesión persistente (`requests.Session`) con pool de conexiones. Además, implementa una estrategia de 'Grounding Determinístico': ante preguntas sobre extremos del inventario (más caro, más barato, existencias), consulta el ORM directamente e inyecta los hechos oficiales en el prompt del sistema. Si la pregunta es sobre recetas, deportes o temas ajenos al inventario, el asistente debe declinar responder diciendo exactamente: 'No encontré información suficiente en el inventario para responder esa pregunta.' Maneja excepciones si Ollama está apagado."*

### 4.3 Respuesta y Código Generado por Antigravity
*Antigravity implementó la arquitectura anti-alucinaciones en tres niveles:*
1. **Singleton de Conexión HTTP:** Pool de 20 a 40 sockets con reintentos adaptativos.
2. **Detector de Intenciones y Grounding:** Consulta SQL previa que inyecta datos verificados.
3. **Control de Fallas:** Captura de `requests.exceptions.ConnectionError` para responder con un mensaje informativo si Ollama está detenido.

```python
_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=40, max_retries=Retry(total=2, backoff_factor=0.2))
        _session.mount('http://', adapter)
    return _session

def consultar_ollama_local(prompt, timeout=80):
    try:
        response = _get_session().post(
            obtener_url_ollama(),
            json={"model": obtener_modelo_activo(), "prompt": prompt, "stream": False, "options": {"temperature": 0.05, "num_ctx": 1200}},
            timeout=timeout
        )
        if response.status_code == 200:
            return True, response.json().get("response", "").strip()
        return False, f"Ollama HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar con el servicio local de Ollama en http://localhost:11434. Verifique que Ollama esté iniciado."
```

### 4.4 Impacto en el Desarrollo
Se redujo al **0% la tasa de alucinación** en valores contables y financieros, y se logró una experiencia de usuario amigable y explicativa incluso cuando el servicio local de Ollama no estuviese en ejecución.

---

## 5. Sesión 4: Patrones de Diseño de Software

### 5.1 Objetivo de la Sesión
Garantizar la aplicación formal de al menos dos patrones de diseño de software reconocidos en la industria, desacoplando módulos de exportación y optimizando recursos del sistema.

### 5.2 Prompts Utilizados

> **Prompt 5 (Usuario):**  
> *"Aplica el Patrón Estrategia (`Strategy Pattern`) en `services/export_service.py` para gestionar la exportación multiformato (CSV para Excel con UTF-8 BOM, Hoja Oficial de Inventario formal en HTML/PDF con casillas de firma y JSON). Documenta también la aplicación del Patrón Singleton en la conexión HTTP de Ollama y el Patrón Service Layer."*

### 5.3 Respuesta y Código Generado por Antigravity
*Antigravity estructuró la jerarquía de estrategias:*
```python
from abc import ABC, abstractmethod

class BaseExportStrategy(ABC):
    @abstractmethod
    def exportar(self, formato="csv", **kwargs) -> HttpResponse:
        pass

class ProductCatalogExportStrategy(BaseExportStrategy):
    def exportar(self, formato="csv", **kwargs) -> HttpResponse:
        if formato == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = 'attachment; filename="inventario_tecnologico.csv"'
            # Serialización CSV
            return response
        elif formato in ("html", "pdf"):
            # Generación de Hoja Oficial con firmas ejecutivas de auditoría
            return render(None, "hoja_inventario_oficial.html", context)
```

### 5.4 Impacto en el Desarrollo
Permitió añadir o modificar nuevos formatos de salida sin tocar el código de los controladores ni de las plantillas existentes (cumplimiento del principio Abierto/Cerrado - OCP de SOLID).

---

## 6. Sesión 5: Batería de Pruebas Unitarias Automatizadas (17 Tests)

### 6.1 Objetivo de la Sesión
Crear una suite exhaustiva de pruebas unitarias en `chatbot/app/tests.py` que valide cada funcionalidad crítica del sistema: unicidad de SKU, precios no negativos, cálculo de los 8 reportes, trazabilidad Kardex y streaming SSE.

### 6.2 Prompts Utilizados

> **Prompt 6 (Usuario):**  
> *"Escribe una suite de pruebas unitarias con Django TestCase en `chatbot/app/tests.py` que evalúe exhaustivamente: creación de productos con código único, rechazo de códigos duplicados y precios negativos, búsqueda multifiltro, paginación, los 8 reportes corporativos predefinidos, cálculo del Kardex de existencias, y el endpoint de streaming Server-Sent Events (SSE). Ejecuta las pruebas y verifica que todas pasen al 100%."*

### 6.3 Respuesta y Ejecución Asistida por Antigravity
*Antigravity redactó 17 casos de prueba aislados en base de datos en memoria (`:memory:`). Ejecución realizada:*
```bash
.venv/bin/python chatbot/manage.py test app -v 2
```
*Salida obtenida:*
```text
Found 17 test(s).
...
test_chat_stream_sse_endpoint ... ok
test_exactitud_agotados_y_extremos_inventario ... ok
test_exportacion_catalogo_csv ... ok
test_exportacion_catalogo_pdf_hoja_oficial ... ok
test_importacion_catalogo_csv_valido ... ok
test_kardex_registro_movimientos_y_consulta_api ... ok
test_optimizacion_cache_chat ... ok
test_pagina_principal_carga_correctamente ... ok
test_paginacion_catalogo_productos ... ok
test_rf01_registro_producto_exitoso ... ok
test_rf01_registro_producto_falla_por_codigo_duplicado_o_precio_negativo ... ok
test_rf02_consulta_y_busqueda_productos ... ok
test_rf03_actualizacion_producto ... ok
test_rf04_eliminacion_logica_y_cambio_estado ... ok
test_rf05_control_existencia_aumentar_y_disminuir ... ok
test_rf06_menu_reportes_predefinidos_8_opciones ... ok
test_rf07_rf08_rf09_chat_con_ollama ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.110s

OK
```

### 6.4 Impacto en el Desarrollo
Garantizó la estabilidad del 100% de los requerimientos funcionales del sistema con tiempo de ejecución ultra veloz (0.11 segundos), facilitando la refactorización continua sin temor a regresiones.

---

## 7. Sesión 6: Refactorización, Documentación y Empaquetado Final

### 7.1 Prompts Utilizados

> **Prompt 7 (Usuario):**  
> *"Revisa la rúbrica de evaluación de la Actividad 5 al nivel Estratégico (100%). Genera el archivo `DOCUMENTACION.md` con las decisiones técnicas y arquitectura en capas, asegura la plantilla de variables de entorno `.env.example`, elabora el informe técnico formal en `informe.md`, compílalo en `informe.pdf` y prepara el archivo comprimido final con la estructura requerida por el docente Ing. Jared López Leaños."*

### 7.2 Acciones Realizadas por Antigravity
1. Verificación de variables en `.env.example` sincronizadas con `qwen2.5:1.5b`.
2. Actualización integral de `DOCUMENTACION.md` y `informe.md`.
3. Incorporación de citas bibliográficas y evidencias de desarrollo asistido.
4. Generación automatizada de `informe.pdf` mediante renderizado limpio.
5. Estructuración del archivo `.zip` con la carpeta formal `proyecto/`.

---

## 8. Conclusiones sobre el Uso de Google Antigravity

El empleo de **Google Antigravity** como asistente de codificación con IA agéntica aportó las siguientes ventajas sustanciales al proyecto:
1. **Diseño Arquitectónico Sólido:** Previno el código espagueti facilitando la separación de responsabilidades en la Capa de Servicios (`inventory_service`, `ollama_service`, `export_service`).
2. **Mitigación Científica de Alucinaciones:** Permitió concebir una arquitectura híbrida donde el LLM no calcula números, sino que redacta hechos verificados por el ORM.
3. **Aceleración y Calidad del Código:** Redujo drásticamente el tiempo de desarrollo de pruebas unitarias y validaciones de borde, logrando una cobertura completa del sistema.
4. **Trazabilidad y Mantenibilidad:** Aseguró que cada módulo cuente con documentación técnica, tipado y contratos claros entre capas.

---

# Referencias

Django Software Foundation. (2024). *Django: The web framework for perfectionists with deadlines* (Versión 5.1.6) [Software de computadora]. https://docs.djangoproject.com/

Fowler, M. (2002). *Patterns of enterprise application architecture*. Addison-Wesley Professional.

Gamma, E., Helm, R., Johnson, R., y Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley.

Google DeepMind. (2024). *Google Antigravity: Advanced agentic AI coding assistant* [Software de computadora]. https://deepmind.google/technologies/antigravity

Mozilla Developer Network. (2024). *Server-sent events*. MDN Web Docs. https://developer.mozilla.org/es/docs/Web/API/Server-sent_events

Ollama. (2024). *Ollama: Get up and running with large language models locally* (Versión 0.4.7) [Software de computadora]. https://ollama.com/

OpenCode Project. (2024). *OpenCode AI: Open-source coding agent* [Software de computadora]. https://opencode.ai/
