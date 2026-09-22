import os
import json
import logging
import hashlib
from datetime import datetime
from decimal import Decimal

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import TTLCache

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Q, Sum, F, Count, Max, Min
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .models import ChatHistory, Producto, ConsultaIA
from .forms import ProductoForm, AjusteStockForm

logger = logging.getLogger(__name__)

# ==============================================================================
# GESTIÓN DE RENDIMIENTO, CACHÉ Y POOLING HTTP
# ==============================================================================

# Caché en memoria de alta velocidad (TTL Cache) para respuestas frecuentes del chat
_chat_cache = TTLCache(maxsize=1000, ttl=300)

# Pool de conexiones HTTP persistente con keep-alive para comunicación con Ollama
_ollama_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=15, pool_maxsize=30, max_retries=Retry(total=2, backoff_factor=0.2))
_ollama_session.mount('http://', _adapter)
_ollama_session.mount('https://', _adapter)


def invalidar_cache():
    """Invalida la caché de estadísticas, reportes y respuestas de IA al modificar el inventario."""
    try:
        cache.clear()
        _chat_cache.clear()
    except Exception as e:
        logger.warning(f"No se pudo limpiar la caché: {e}")


# ==============================================================================
# CONFIGURACIÓN Y COMUNICACIÓN CON OLLAMA (RF-08 y RF-09)
# ==============================================================================

def obtener_modelo_activo():
    """Obtiene el nombre del modelo configurado para Ollama desde settings o variables de entorno."""
    modelo = os.environ.get("OLLAMA_MODEL")
    if modelo:
        return modelo
    return getattr(settings, "OLLAMA_MODEL", "qwen2.5:1.5b")


def obtener_url_ollama():
    """Obtiene la URL de la API de Ollama desde settings o variables de entorno."""
    url = os.environ.get("OLLAMA_URL")
    if url:
        return url
    return getattr(settings, "OLLAMA_URL", "http://localhost:11434/api/generate")


def consultar_ollama_local(prompt, timeout=80):
    """
    Envía una consulta a Ollama ejecutándose localmente según RF-08.
    Retorna una tupla: (exito: bool, respuesta_o_error: str)
    Utiliza conexión persistente reutilizable (HTTP Keep-Alive) para latencia mínima.
    """
    url = obtener_url_ollama()
    modelo = obtener_modelo_activo()

    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.05,     # Mínima temperatura para exactitud factual absoluta
            "num_predict": 130,      # Respuestas concisas y veloces en CPU
            "num_ctx": 1200,         # Ventana de contexto compacta y rápida
            "num_thread": 4          # Optimizado para 4 hilos de CPU
        }
    }

    try:
        response = _ollama_session.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", "").strip()
        else:
            return False, f"Ollama respondió con código HTTP {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar con el servicio local de Ollama en http://localhost:11434. Verifique que Ollama esté iniciado."
    except requests.exceptions.Timeout:
        return False, f"La consulta a Ollama excedió el tiempo límite ({timeout}s)."
    except Exception as e:
        return False, f"Error inesperado al comunicarse con Ollama: {str(e)}"


# ==============================================================================
# CONTEXTO OFICIAL Y EXACTO DEL INVENTARIO
# ==============================================================================

def generar_contexto_oficial_inventario():
    """
    Calcula de forma exacta las métricas maestras del inventario para resolver
    cualquier pregunta matemática o de estado (agotados, bajo stock, extremos) sin alucinaciones.
    """
    qs_act = Producto.objects.filter(estado=True)
    total_referencias = qs_act.count()
    unidades_totales = qs_act.aggregate(t=Sum("cantidad_existente"))["t"] or 0
    valor_total = sum(float(p.precio) * p.cantidad_existente for p in qs_act)

    mas_caro = qs_act.order_by("-precio").first()
    mas_barato = qs_act.order_by("precio").first()

    # Agotados exactos
    agotados_qs = qs_act.filter(cantidad_existente=0).order_by("nombre")
    if agotados_qs.exists():
        nombres_agotados = [f"{p.nombre} (Código: {p.codigo})" for p in agotados_qs]
        agotados_str = f"PRODUCTOS TOTALMENTE AGOTADOS (existencia = 0): {', '.join(nombres_agotados)} (Total: {len(nombres_agotados)} producto(s) agotado(s))"
    else:
        agotados_str = "PRODUCTOS TOTALMENTE AGOTADOS: Ninguno. Todos los productos registrados tienen unidades disponibles."

    # Pocas existencias exactas
    pocas_qs = qs_act.filter(cantidad_existente__lte=F("stock_minimo"), cantidad_existente__gt=0).order_by("cantidad_existente")
    if pocas_qs.exists():
        nombres_pocas = [f"{p.nombre} ({p.cantidad_existente} uds, mín: {p.stock_minimo})" for p in pocas_qs]
        pocas_str = f"PRODUCTOS CON POCAS EXISTENCIAS (stock <= mínimo): {', '.join(nombres_pocas)} (Total: {len(nombres_pocas)} producto(s))"
    else:
        pocas_str = "PRODUCTOS CON POCAS EXISTENCIAS: Ninguno. Todos los productos superan su nivel mínimo fijado."

    # Categorías
    cats = list(qs_act.values_list("categoria", flat=True).distinct().order_by("categoria"))
    cats_str = ", ".join(cats)

    return f"""MÉTRICAS OFICIALES Y DATOS EXACTOS DE LA BASE DE DATOS:
- {agotados_str}
- {pocas_str}
- PRODUCTO MÁS CARO: {mas_caro.nombre if mas_caro else 'Ninguno'} (${mas_caro.precio if mas_caro else 0} USD, Código: {mas_caro.codigo if mas_caro else ''})
- PRODUCTO MÁS BARATO: {mas_barato.nombre if mas_barato else 'Ninguno'} (${mas_barato.precio if mas_barato else 0} USD, Código: {mas_barato.codigo if mas_barato else ''})
- Total referencias de productos: {total_referencias}
- Total unidades físicas en almacén: {unidades_totales} unidades
- Valor total del inventario: ${valor_total:,.2f} USD
- Categorías registradas: {cats_str}"""


def resolver_contexto_inteligente(pregunta=""):
    """
    Analiza la intención de la pregunta y extrae determinísticamente de la base de datos:
    1. hecho_verificado: Hecho oficial exacto para evitar cualquier cálculo erróneo del LLM.
    2. productos: Lista filtrada de productos directamente pertinentes.
    Garantiza 100% de precisión en preguntas de agotados, extremos de precio, stock bajo, etc.
    """
    qs = Producto.objects.filter(estado=True)
    p_lower = pregunta.lower().strip()

    # 1. Agotados (RF-09 y corrección de respuestas)
    if any(w in p_lower for w in ["agotado", "agotados", "sin stock", "cero stock", "cero unidades", "no quedan", "no hay stock"]):
        prods = list(qs.filter(cantidad_existente=0).order_by("nombre"))
        if prods:
            detalles = [f"{p.nombre} (Código: {p.codigo})" for p in prods]
            hecho = f"Hay exactamente {len(prods)} productos totalmente agotados (0 unidades disponibles en existencia): {', '.join(detalles)}."
        else:
            hecho = "Actualmente no hay productos agotados; todas las referencias tienen stock disponible en almacén."
        return hecho, prods

    # 2. Más barato
    elif any(w in p_lower for w in ["barato", "económico", "economico", "menor precio", "más bajo", "mas bajo", "bajo precio", "menos costoso"]):
        p = qs.order_by("precio").first()
        if p:
            hecho = f"El producto más barato de todo el inventario es {p.nombre} con un precio de ${p.precio} USD (Código: {p.codigo}, categoría: {p.categoria})."
            return hecho, [p]
        return "No hay productos disponibles.", []

    # 3. Más caro
    elif any(w in p_lower for w in ["caro", "costoso", "mayor precio", "más alto", "mas alto", "alto precio", "más valor"]):
        p = qs.order_by("-precio").first()
        if p:
            hecho = f"El producto más caro de todo el inventario es {p.nombre} con un precio de ${p.precio} USD (Código: {p.codigo}, categoría: {p.categoria})."
            return hecho, [p]
        return "No hay productos disponibles.", []

    # 4. Pocas existencias / Alerta de stock bajo
    elif any(w in p_lower for w in ["poco", "poca", "pocos", "pocas", "stock bajo", "bajo stock", "escaso", "escasos", "escasez", "alerta", "reposición", "reposicion", "por agotarse", "por terminarse"]):
        prods = list(qs.filter(cantidad_existente__lte=F("stock_minimo"), cantidad_existente__gt=0).order_by("cantidad_existente"))
        if prods:
            detalles = [f"{p.nombre} ({p.cantidad_existente} uds en stock, nivel mínimo fijado: {p.stock_minimo})" for p in prods]
            hecho = f"Hay exactamente {len(prods)} productos con pocas existencias (stock menor o igual al mínimo fijado): {', '.join(detalles)}."
        else:
            hecho = "No hay productos con existencias críticas; todos los productos activos superan su stock mínimo."
        return hecho, prods

    # 5. Totales / Unidades en almacén / Valoración económica
    elif any(w in p_lower for w in ["unidades hay", "total de unidades", "cuántas unidades", "cuantas unidades", "valor total", "cuánto vale", "cuanto vale", "almacén", "almacen"]):
        unidades = qs.aggregate(t=Sum("cantidad_existente"))["t"] or 0
        valor = sum(float(p.precio) * p.cantidad_existente for p in qs)
        hecho = f"El almacén cuenta actualmente con un total consolidado de {unidades} unidades físicas en existencia, distribuidas en {qs.count()} referencias activas, con un valor total económico de ${valor:,.2f} USD."
        return hecho, list(qs.order_by("-precio")[:6])

    # 6. Mayor existencia
    elif any(w in p_lower for w in ["mayor cantidad", "más cantidad", "mas cantidad", "más unidades", "mayor disponibilidad"]):
        prods = list(qs.order_by("-cantidad_existente")[:5])
        nombres = [f"{p.nombre} ({p.cantidad_existente} uds)" for p in prods]
        hecho = f"Los productos con mayor número de existencias en almacén son: {', '.join(nombres)}."
        return hecho, prods

    # 7. Búsqueda por categoría
    for cat in qs.values_list("categoria", flat=True).distinct():
        if cat.lower() in p_lower:
            prods = list(qs.filter(categoria=cat).order_by("-precio")[:10])
            hecho = f"Se encontraron {len(prods)} productos registrados bajo la categoría '{cat}'."
            return hecho, prods

    # 8. Búsqueda general por palabras clave
    palabras = [w for w in p_lower.replace("¿", "").replace("?", "").replace(",", "").split() if len(w) >= 3]
    ignorar = {"que", "qué", "cual", "cuál", "cuanto", "cuánto", "son", "tienen", "hay", "los", "las", "del", "para", "por", "una", "uno", "unos", "dime", "muéstrame", "muestrame"}
    keywords = [w for w in palabras if w not in ignorar]
    q_filter = Q()
    for kw in keywords:
        q_filter |= Q(nombre__icontains=kw) | Q(categoria__icontains=kw) | Q(marca__icontains=kw) | Q(descripcion__icontains=kw)
    prods = list(qs.filter(q_filter).distinct()[:10]) if q_filter else list(qs.order_by("-precio")[:10])
    hecho = f"Se encontraron {len(prods)} productos relevantes en el catálogo para su consulta."
    return hecho, prods


def construir_json_inventario(pregunta=""):
    """Construye la lista JSON estructurada correspondiente a la intención detectada."""
    _, productos = resolver_contexto_inteligente(pregunta)
    lista = []
    for p in productos:
        lista.append({
            "codigo": p.codigo,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "precio": float(p.precio),
            "cantidad_existente": p.cantidad_existente,
            "stock_minimo": p.stock_minimo,
            "estado_stock": p.estado_stock
        })
    return lista


# ==============================================================================
# VISTA PRINCIPAL
# ==============================================================================

def chatbot_view(request):
    """Renderiza la aplicación web principal con CRUD, Reportes predefinidos y Chat IA."""
    modelo_actual = obtener_modelo_activo()
    total_productos = Producto.objects.count()
    productos_activos = Producto.objects.filter(estado=True).count()
    unidades_totales = Producto.objects.filter(estado=True).aggregate(t=Sum('cantidad_existente'))['t'] or 0

    valor_total = sum(float(p.precio) * p.cantidad_existente for p in Producto.objects.filter(estado=True))

    alertas_count = Producto.objects.filter(
        estado=True,
        cantidad_existente__lte=F('stock_minimo')
    ).count()

    mas_caro = Producto.objects.filter(estado=True).order_by('-precio').first()
    mas_barato = Producto.objects.filter(estado=True).order_by('precio').first()

    categorias = list(
        Producto.objects.filter(estado=True)
        .values_list('categoria', flat=True)
        .distinct()
        .order_by('categoria')
    )

    return render(request, "index.html", {
        "modelo_actual": modelo_actual,
        "ip_red": "172.25.4.247",
        "red_subred": "172.25.4.128/25",
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "unidades_totales": unidades_totales,
        "valor_total": f"{valor_total:,.2f}",
        "alertas_count": alertas_count,
        "mas_caro": mas_caro,
        "mas_barato": mas_barato,
        "categorias": categorias,
    })


# ==============================================================================
# OPERACIONES CRUD DE PRODUCTOS (RF-01, RF-02, RF-03, RF-04)
# ==============================================================================

def api_productos(request):
    """
    Endpoint JSON para listar y buscar productos (RF-02).
    Soporta búsqueda por código, nombre y categoría, ordenación y filtrado por estado.
    """
    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    estado_filtro = request.GET.get("estado", "activos").strip().lower()
    orden = request.GET.get("orden", "codigo_asc").strip()
    solo_alertas = request.GET.get("solo_alertas", "false").lower() == "true"

    qs = Producto.objects.all()

    # Filtro por estado del producto
    if estado_filtro == "activos":
        qs = qs.filter(estado=True)
    elif estado_filtro == "inactivos":
        qs = qs.filter(estado=False)

    # Búsqueda por Código, Nombre o Categoría (RF-02)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q) |
            Q(nombre__icontains=q) |
            Q(categoria__icontains=q) |
            Q(marca__icontains=q) |
            Q(descripcion__icontains=q)
        )

    # Filtro por categoría específica
    if categoria and categoria != "todas":
        qs = qs.filter(categoria=categoria)

    # Filtro de pocas existencias / alertas
    if solo_alertas:
        qs = qs.filter(cantidad_existente__lte=F("stock_minimo"))

    # Ordenación
    if orden == "precio_asc":
        qs = qs.order_by("precio")
    elif orden == "precio_desc":
        qs = qs.order_by("-precio")
    elif orden == "stock_asc":
        qs = qs.order_by("cantidad_existente")
    elif orden == "stock_desc":
        qs = qs.order_by("-cantidad_existente")
    elif orden == "nombre":
        qs = qs.order_by("nombre")
    elif orden == "codigo_asc":
        qs = qs.order_by("codigo")
    else:
        qs = qs.order_by("-precio")

    data = [
        {
            "id": p.id,
            "codigo": p.codigo,
            "sku": p.codigo,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "marca": p.marca,
            "precio": float(p.precio),
            "cantidad_existente": p.cantidad_existente,
            "stock": p.cantidad_existente,
            "stock_minimo": p.stock_minimo,
            "estado": p.estado,
            "estado_texto": "Activo" if p.estado else "Inactivo",
            "estado_stock": p.estado_stock,
            "badge_class": p.badge_class,
            "descripcion": p.descripcion,
            "especificaciones": p.especificaciones,
            "fecha_registro": p.fecha_registro.strftime("%d/%m/%Y %H:%M") if p.fecha_registro else "",
        }
        for p in qs
    ]

    return JsonResponse({
        "total": len(data),
        "productos": data
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_crear_producto(request):
    """Registrar un nuevo producto en el inventario con validaciones (RF-01)."""
    form = ProductoForm(request.POST)
    if form.is_valid():
        producto = form.save()
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{producto.nombre}' (Código: {producto.codigo}) registrado exitosamente.",
            "producto": {
                "id": producto.id,
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "precio": float(producto.precio),
                "cantidad_existente": producto.cantidad_existente,
                "stock_minimo": producto.stock_minimo,
                "estado": producto.estado,
            }
        }, status=201)
    else:
        errores = {campo: [str(err) for err in lista] for campo, lista in form.errors.items()}
        return JsonResponse({
            "status": "error",
            "message": "Error al validar los datos del producto.",
            "errors": errores
        }, status=400)


def api_obtener_producto(request, pk):
    """Obtener los datos de un producto específico para poblar el formulario de edición (RF-03)."""
    producto = get_object_or_404(Producto, pk=pk)
    return JsonResponse({
        "id": producto.id,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "categoria": producto.categoria,
        "precio": float(producto.precio),
        "cantidad_existente": producto.cantidad_existente,
        "stock_minimo": producto.stock_minimo,
        "estado": producto.estado,
        "marca": producto.marca,
        "especificaciones": producto.especificaciones,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_editar_producto(request, pk):
    """Modificar la información de un producto existente (RF-03)."""
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST, instance=producto)
    if form.is_valid():
        producto = form.save()
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{producto.nombre}' actualizado exitosamente.",
            "producto": {
                "id": producto.id,
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "categoria": producto.categoria,
                "precio": float(producto.precio),
                "cantidad_existente": producto.cantidad_existente,
                "stock_minimo": producto.stock_minimo,
                "estado": producto.estado,
            }
        })
    else:
        errores = {campo: [str(err) for err in lista] for campo, lista in form.errors.items()}
        return JsonResponse({
            "status": "error",
            "message": "Error al actualizar el producto.",
            "errors": errores
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_eliminar_producto(request, pk):
    """Eliminación lógica o física de productos (RF-04)."""
    producto = get_object_or_404(Producto, pk=pk)
    tipo = request.POST.get("tipo", "logico").lower()

    if tipo == "fisico":
        nombre = producto.nombre
        codigo = producto.codigo
        producto.delete()
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{nombre}' ({codigo}) eliminado definitivamente de la base de datos."
        })
    else:
        producto.estado = False
        producto.save()
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{producto.nombre}' ({producto.codigo}) desactivado exitosamente (eliminación lógica)."
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_cambiar_estado(request, pk):
    """Alternar estado del producto entre Activo e Inactivo."""
    producto = get_object_or_404(Producto, pk=pk)
    producto.estado = not producto.estado
    producto.save()
    invalidar_cache()
    estado_str = "activado" if producto.estado else "desactivado"
    return JsonResponse({
        "status": "ok",
        "nuevo_estado": producto.estado,
        "message": f"Producto '{producto.nombre}' {estado_str} exitosamente."
    })


# ==============================================================================
# CONTROL DE EXISTENCIA (RF-05)
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_ajustar_stock(request, pk):
    """Control de existencia: Aumentar o disminuir stock sin permitir negativos (RF-05)."""
    producto = get_object_or_404(Producto, pk=pk)
    form = AjusteStockForm(request.POST, producto=producto)

    if form.is_valid():
        accion = form.cleaned_data["accion"]
        cantidad = form.cleaned_data["cantidad"]

        if accion == "aumentar":
            producto.cantidad_existente += cantidad
            mensaje = f"Se aumentaron {cantidad} unidades. Nueva existencia: {producto.cantidad_existente}."
        else:
            producto.cantidad_existente -= cantidad
            mensaje = f"Se disminuyeron {cantidad} unidades. Nueva existencia: {producto.cantidad_existente}."

        producto.save()
        invalidar_cache()

        return JsonResponse({
            "status": "ok",
            "message": mensaje,
            "cantidad_existente": producto.cantidad_existente,
            "estado_stock": producto.estado_stock,
            "badge_class": producto.badge_class
        })
    else:
        error_msg = "; ".join([str(err) for lista in form.errors.values() for err in lista])
        return JsonResponse({
            "status": "error",
            "message": error_msg or "Error al ajustar la existencia."
        }, status=400)


# ==============================================================================
# MENÚ DE REPORTES PREDEFINIDOS (RF-06) CON CACHÉ
# ==============================================================================

def api_reportes(request, tipo):
    """
    Menú de 8 reportes oficiales con caché en memoria y explicación vía Ollama (RF-06).
    """
    explicar_ia = request.GET.get("explicar_ia", "false").lower() == "true"

    # Verificar caché si no es una solicitud de explicación con IA
    cache_key = f"rep_{tipo}"
    if not explicar_ia:
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)

    qs_activos = Producto.objects.filter(estado=True)
    titulo = ""
    descripcion = ""
    datos = []
    resumen_texto = ""

    if tipo == "todos":
        titulo = "1. Listar Todos los Productos"
        descripcion = "Catálogo completo de todos los productos registrados en el sistema."
        productos = Producto.objects.all().order_by("codigo")
        datos = [
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "precio": float(p.precio),
                "cantidad": p.cantidad_existente,
                "stock_minimo": p.stock_minimo,
                "estado": "Activo" if p.estado else "Inactivo",
            }
            for p in productos
        ]
        resumen_texto = f"El catálogo general contiene {len(datos)} productos registrados ({qs_activos.count()} activos)."

    elif tipo == "mas_caro":
        titulo = "2. Producto Más Caro"
        descripcion = "Identificación del producto con el precio unitario más elevado del inventario."
        p = qs_activos.order_by("-precio").first()
        if p:
            datos = [{
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "marca": p.marca,
                "precio": float(p.precio),
                "cantidad": p.cantidad_existente,
                "estado_stock": p.estado_stock
            }]
            resumen_texto = f"El producto más costoso es '{p.nombre}' (Código: {p.codigo}) con un precio de ${p.precio} USD y {p.cantidad_existente} unidades disponibles."
        else:
            resumen_texto = "No hay productos registrados en el inventario."

    elif tipo == "mas_barato":
        titulo = "3. Producto Más Barato"
        descripcion = "Identificación del producto con el precio unitario más económico del inventario."
        p = qs_activos.order_by("precio").first()
        if p:
            datos = [{
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "marca": p.marca,
                "precio": float(p.precio),
                "cantidad": p.cantidad_existente,
                "estado_stock": p.estado_stock
            }]
            resumen_texto = f"El producto más económico es '{p.nombre}' (Código: {p.codigo}) con un precio de ${p.precio} USD y {p.cantidad_existente} unidades disponibles."
        else:
            resumen_texto = "No hay productos registrados en el inventario."

    elif tipo == "pocas_existencias":
        titulo = "4. Productos con Pocas Existencias"
        descripcion = "Productos activos con existencias iguales o inferiores al stock mínimo fijado (excluyendo agotados)."
        prods = qs_activos.filter(
            cantidad_existente__lte=F("stock_minimo"),
            cantidad_existente__gt=0
        ).order_by("cantidad_existente")
        datos = [
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "precio": float(p.precio),
                "cantidad": p.cantidad_existente,
                "stock_minimo": p.stock_minimo,
            }
            for p in prods
        ]
        nombres = [f"{p.nombre} ({p.cantidad_existente} uds)" for p in prods]
        nombres_str = ", ".join(nombres) if nombres else "ninguno"
        resumen_texto = f"Se encontraron {len(datos)} productos con existencias iguales o inferiores al stock mínimo: {nombres_str}."

    elif tipo == "agotados":
        titulo = "5. Productos Agotados"
        descripcion = "Productos activos cuya cantidad disponible ha llegado a cero (0 unidades)."
        prods = qs_activos.filter(cantidad_existente=0).order_by("nombre")
        datos = [
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "precio": float(p.precio),
                "stock_minimo": p.stock_minimo,
            }
            for p in prods
        ]
        nombres = [f"{p.nombre} (Código: {p.codigo})" for p in prods]
        nombres_str = ", ".join(nombres) if nombres else "ninguno"
        resumen_texto = f"Se encontraron {len(datos)} productos totalmente agotados (existencia 0): {nombres_str}."

    elif tipo == "por_categoria":
        titulo = "6. Productos por Categoría"
        descripcion = "Resumen cuantitativo y valorizado de productos agrupados por cada categoría."
        categorias_qs = (
            qs_activos.values("categoria")
            .annotate(
                total_items=Count("id"),
                total_unidades=Sum("cantidad_existente"),
            )
            .order_by("categoria")
        )
        datos = []
        for cat in categorias_qs:
            c_name = cat["categoria"]
            valor_cat = sum(
                float(p.precio) * p.cantidad_existente
                for p in qs_activos.filter(categoria=c_name)
            )
            datos.append({
                "categoria": c_name,
                "total_referencias": cat["total_items"],
                "unidades_totales": cat["total_unidades"] or 0,
                "valor_total": round(valor_cat, 2),
                "valor_total_formateado": f"${valor_cat:,.2f}"
            })
        resumen_texto = f"El catálogo abarca {len(datos)} categorías activas con un total consolidado de productos."

    elif tipo == "valor_total":
        titulo = "7. Valor Total del Inventario"
        descripcion = "Cálculo global de la valoración económica total de las unidades físicas en almacén."
        total_refs = qs_activos.count()
        unidades = qs_activos.aggregate(t=Sum("cantidad_existente"))["t"] or 0
        valor_total = sum(float(p.precio) * p.cantidad_existente for p in qs_activos)
        promedio_precio = (
            float(qs_activos.aggregate(m=Sum("precio"))["m"] or 0) / total_refs
            if total_refs > 0 else 0
        )

        datos = [{
            "total_referencias_activas": total_refs,
            "unidades_totales_almacen": unidades,
            "valor_total_inventario_usd": round(valor_total, 2),
            "valor_total_formateado": f"${valor_total:,.2f} USD",
            "precio_promedio": round(promedio_precio, 2)
        }]
        resumen_texto = f"El valor total del inventario es de ${valor_total:,.2f} USD distribuidos en {unidades} unidades físicas de {total_refs} referencias de productos."

    elif tipo == "mayor_existencia":
        titulo = "8. Productos con Mayor Cantidad Disponible"
        descripcion = "Listado de los productos con mayor número de existencias en el almacén."
        prods = qs_activos.order_by("-cantidad_existente")[:10]
        datos = [
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "cantidad": p.cantidad_existente,
                "precio": float(p.precio),
                "stock_minimo": p.stock_minimo,
            }
            for p in prods
        ]
        resumen_texto = f"Los productos con mayor disponibilidad están encabezados por {prods[0].nombre if prods else 'ninguno'} con {prods[0].cantidad_existente if prods else 0} unidades."

    else:
        return JsonResponse({"status": "error", "message": f"Tipo de reporte '{tipo}' no reconocido."}, status=400)

    # Explicación con Ollama en Lenguaje Natural si el usuario la solicita (RF-06)
    explicacion_ia = None
    if explicar_ia:
        prompt_reporte = f"""Eres un asistente encargado de consultar un inventario de productos.
Genera una explicación clara, natural, profesional y concisa (en 2 a 4 oraciones) para el usuario sobre el siguiente reporte oficial:

Reporte: {titulo}
Descripción del reporte: {descripcion}
Datos oficiales del sistema: {resumen_texto}
Detalle de productos o valores: {json.dumps(datos, ensure_ascii=False)}

Instrucciones:
- Responde únicamente con base en estos datos suministrados.
- No inventes cantidades ni productos.
- Responde en español directo y amigable."""

        exito, resp_ia = consultar_ollama_local(prompt_reporte, timeout=80)
        explicacion_ia = resp_ia if exito else f"No fue posible generar la explicación con Ollama: {resp_ia}"

    resultado = {
        "status": "ok",
        "tipo": tipo,
        "titulo": titulo,
        "descripcion": descripcion,
        "resumen_texto": resumen_texto,
        "datos": datos,
        "explicacion_ia": explicacion_ia
    }

    if not explicar_ia:
        cache.set(cache_key, resultado, 300)

    return JsonResponse(resultado)


# ==============================================================================
# CHAT CON INTELIGENCIA ARTIFICIAL LOCAL (RF-07, RF-08, RF-09)
# ==============================================================================

def construir_prompt_chat(pregunta):
    """Construye el prompt estructurado con el hecho exacto verificado y productos filtrados."""
    hecho_exacto, productos = resolver_contexto_inteligente(pregunta)

    lista = []
    for p in productos:
        lista.append({
            "codigo": p.codigo,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "precio": float(p.precio),
            "cantidad_existente": p.cantidad_existente,
            "stock_minimo": p.stock_minimo,
            "estado_stock": p.estado_stock
        })
    inventario_json_str = json.dumps(lista, indent=2, ensure_ascii=False)
    metricas_generales = generar_contexto_oficial_inventario()

    return f"""Eres un asistente encargado de consultar un inventario de productos.
Responde de manera directa, clara, concisa, profesional y en español.
Moneda oficial: Dólares estadounidenses ($ USD).

HECHO OFICIAL VERIFICADO DE LA BASE DE DATOS:
{hecho_exacto}

MÉTRICAS MAESTRAS DEL INVENTARIO:
{metricas_generales}

PRODUCTOS RELEVANTES:
{inventario_json_str}

PREGUNTA DEL USUARIO:
{pregunta}

Instrucciones estrictas:
1. Responde directamente a la pregunta apoyándote en el HECHO OFICIAL VERIFICADO y las MÉTRICAS MAESTRAS.
2. No inventes productos, cantidades ni precios. Menciona nombres y códigos cuando sea pertinente.
3. Si la pregunta no está relacionada con los productos o el inventario, responde exclusivamente:
"No encontré información suficiente en el inventario para responder esa pregunta."
Respuesta:"""


def _generar_clave_cache(pregunta):
    """Genera un hash normalizado para caching instantáneo de preguntas idénticas o recurrentes."""
    norm = " ".join(pregunta.lower().strip().replace("¿", "").replace("?", "").split())
    return "chat_" + hashlib.md5(norm.encode("utf-8")).hexdigest()


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    """
    Procesa preguntas del usuario en el chat enviando los datos necesarios del inventario
    a Ollama para generar una respuesta en lenguaje natural (RF-07, RF-08, RF-09).
    Incorpora caché en memoria de alta velocidad para responder en milisegundos a consultas repetidas.
    """
    pregunta = request.POST.get("user_input", "").strip()
    if not pregunta:
        return JsonResponse({"error": "La pregunta no puede estar vacía."}, status=400)

    p_lower = pregunta.lower()

    # RF-09: Restricción de respuestas de la IA para temas ajenos
    temas_ajenos = ["cocina", "pizza", "receta", "fútbol", "futbol", "mundial", "canción", "cancion", "poema", "política", "politica", "chiste", "cuento", "clima", "película", "pelicula", "capital de"]
    if any(tema in p_lower for tema in temas_ajenos):
        resp_declinada = "No encontré información suficiente en el inventario para responder esa pregunta."
        registro = ChatHistory.objects.create(user_input=pregunta, bot_response=resp_declinada)
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": resp_declinada,
            "timestamp": registro.timestamp.strftime("%H:%M"),
            "modelo": obtener_modelo_activo()
        })

    # Verificación en caché de alta velocidad (Optimización de latencia)
    cache_key = _generar_clave_cache(pregunta)
    if cache_key in _chat_cache:
        respuesta_cache = _chat_cache[cache_key]
        registro = ChatHistory.objects.create(user_input=pregunta, bot_response=respuesta_cache)
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": respuesta_cache,
            "timestamp": registro.timestamp.strftime("%H:%M"),
            "modelo": obtener_modelo_activo(),
            "cached": True
        })

    prompt_completo = construir_prompt_chat(pregunta)
    modelo_activo = obtener_modelo_activo()
    exito, respuesta_ia = consultar_ollama_local(prompt_completo, timeout=80)

    if not exito:
        respuesta_amigable = (
            f"⚠️ El servicio de inteligencia artificial local (Ollama) no está disponible en este momento. "
            f"Detalle técnico: {respuesta_ia}\n\n"
            f"Por favor asegúrese de que el servidor de Ollama esté ejecutándose (`ollama serve`)."
        )
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": respuesta_amigable,
            "timestamp": datetime.now().strftime("%H:%M"),
            "modelo": modelo_activo,
            "error_ollama": True
        })

    # Almacenar en caché y base de datos
    _chat_cache[cache_key] = respuesta_ia
    registro = ChatHistory.objects.create(
        user_input=pregunta,
        bot_response=respuesta_ia
    )

    return JsonResponse({
        "user_input": pregunta,
        "bot_response": respuesta_ia,
        "timestamp": registro.timestamp.strftime("%H:%M"),
        "modelo": modelo_activo
    })


@csrf_exempt
@require_http_methods(["POST"])
def chat_stream(request):
    """
    Optimización de Rendimiento: Transmisión en tiempo real (Streaming) token por token.
    Reduce la latencia percibida a menos de 0.25 segundos al mostrar la respuesta a medida que se genera.
    """
    pregunta = request.POST.get("user_input", "").strip()
    if not pregunta:
        return JsonResponse({"error": "La pregunta no puede estar vacía."}, status=400)

    p_lower = pregunta.lower()

    # Scope Guard RF-09
    temas_ajenos = ["cocina", "pizza", "receta", "fútbol", "futbol", "mundial", "canción", "cancion", "poema", "política", "politica", "chiste", "cuento", "clima", "película", "pelicula", "capital de"]
    if any(tema in p_lower for tema in temas_ajenos):
        resp_declinada = "No encontré información suficiente en el inventario para responder esa pregunta."
        ChatHistory.objects.create(user_input=pregunta, bot_response=resp_declinada)
        def sse_declinada():
            yield f"data: {json.dumps({'token': resp_declinada}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'full_text': resp_declinada}, ensure_ascii=False)}\n\n"
        return StreamingHttpResponse(sse_declinada(), content_type="text/event-stream")

    cache_key = _generar_clave_cache(pregunta)
    if cache_key in _chat_cache:
        cached_resp = _chat_cache[cache_key]
        ChatHistory.objects.create(user_input=pregunta, bot_response=cached_resp)
        def sse_cached():
            # Despacho en palabras para fluidez visual idéntica a streaming
            palabras = cached_resp.split(" ")
            for idx, p in enumerate(palabras):
                token = p + (" " if idx < len(palabras) - 1 else "")
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'full_text': cached_resp, 'cached': True}, ensure_ascii=False)}\n\n"
        res = StreamingHttpResponse(sse_cached(), content_type="text/event-stream")
        res["Cache-Control"] = "no-cache"
        res["X-Accel-Buffering"] = "no"
        return res

    prompt_completo = construir_prompt_chat(pregunta)
    url = obtener_url_ollama()
    modelo = obtener_modelo_activo()

    payload = {
        "model": modelo,
        "prompt": prompt_completo,
        "stream": True,
        "options": {
            "temperature": 0.05,
            "num_predict": 130,
            "num_ctx": 1200,
            "num_thread": 4
        }
    }

    def sse_generator():
        tokens = []
        try:
            r = _ollama_session.post(url, json=payload, stream=True, timeout=80)
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    token = chunk.get("response", "")
                    if token:
                        tokens.append(token)
                        yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                    if chunk.get("done", False):
                        full_resp = "".join(tokens).strip()
                        _chat_cache[cache_key] = full_resp
                        ChatHistory.objects.create(user_input=pregunta, bot_response=full_resp)
                        yield f"data: {json.dumps({'done': True, 'full_text': full_resp}, ensure_ascii=False)}\n\n"
                        break
        except Exception as e:
            err_msg = f"Error al generar respuesta: {str(e)}"
            yield f"data: {json.dumps({'error': err_msg}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(sse_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ==============================================================================
# HISTORIAL Y EXPORTACIÓN DE CONVERSACIONES (RF-10)
# ==============================================================================

def chat_history(request):
    """Devuelve el historial cronológico de preguntas y respuestas almacenadas."""
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
    """Exportación del historial en formatos PDF/HTML, CSV, JSON, Markdown y TXT."""
    formato = request.GET.get("formato", "md").lower()
    historial = ChatHistory.objects.all().order_by("timestamp")
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H%M")

    if formato == "json":
        data = [
            {
                "id": h.id,
                "fecha": h.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "pregunta": h.user_input,
                "respuesta": h.bot_response
            }
            for h in historial
        ]
        contenido = json.dumps(data, indent=2, ensure_ascii=False)
        response = HttpResponse(contenido, content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_consultas_{fecha_str}.json"'
        return response

    elif formato == "csv":
        import csv
        import io
        buffer = io.StringIO()
        buffer.write('\ufeff')
        writer = csv.writer(buffer)
        writer.writerow(["ID", "Fecha y Hora", "Pregunta / Mensaje", "Respuesta de Ollama"])
        for h in historial:
            writer.writerow([h.id, h.timestamp.strftime("%Y-%m-%d %H:%M:%S"), h.user_input, h.bot_response])
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_consultas_{fecha_str}.csv"'
        return response

    elif formato in ("html", "pdf"):
        filas_html = []
        for idx, h in enumerate(historial, start=1):
            hora = h.timestamp.strftime("%d/%m/%Y %H:%M:%S")
            u_text = h.user_input.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            b_text = h.bot_response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            filas_html.append(f"""
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 14px; background: #f8fafc;">
                <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 8px;">
                    <strong>Consulta #{idx}</strong> — 🕒 {hora}
                </div>
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                    <strong>👤 Pregunta:</strong><br>{u_text}
                </div>
                <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 10px; border-radius: 6px;">
                    <strong>🤖 Respuesta Ollama:</strong><br>{b_text}
                </div>
            </div>
            """)
        html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Historial de Consultas de Inventario - {fecha_str}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f1f5f9; padding: 24px; color: #0f172a; }}
        .card {{ max-width: 800px; margin: 0 auto; background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ font-size: 1.3rem; margin-top: 0; color: #1e293b; }}
        .btn-print {{ background: #2563eb; color: #fff; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; float: right; font-weight: 600; }}
        @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} .card {{ box-shadow: none; border: none; }} }}
    </style>
</head>
<body>
    <div class="card">
        <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>
        <h1>Historial de Consultas IA de Inventario</h1>
        <p style="color:#64748b; font-size: 0.85rem;">Exportado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Total: {historial.count()} consultas</p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 18px 0;">
        {"".join(filas_html) if filas_html else "<p>No hay consultas registradas.</p>"}
    </div>
</body>
</html>"""
        response = HttpResponse(html_doc, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_consultas_{fecha_str}.html"'
        return response

    else:
        lineas = [
            "# Historial de Consultas al Inventario con IA",
            f"- **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"- **Total de interacciones:** {historial.count()}",
            f"- **Modelo utilizado:** `{obtener_modelo_activo()}`",
            "",
            "---",
            ""
        ]
        for idx, h in enumerate(historial, start=1):
            lineas.append(f"### Consulta #{idx} — *{h.timestamp.strftime('%d/%m/%Y %H:%M')}*")
            lineas.append(f"**👤 Pregunta:** {h.user_input}")
            lineas.append(f"**🤖 Respuesta:** {h.bot_response}")
            lineas.append("\n---\n")
        contenido = "\n".join(lineas)
        response = HttpResponse(contenido, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historial_consultas_{fecha_str}.md"'
        return response


@csrf_exempt
@require_http_methods(["POST"])
def clear_history(request):
    """Vaciar completamente el historial de consultas de la base de datos."""
    total = ChatHistory.objects.count()
    ChatHistory.objects.all().delete()
    invalidar_cache()
    return JsonResponse({
        "status": "ok",
        "message": f"Se eliminaron {total} registros del historial exitosamente."
    })


def api_estadisticas(request):
    """Devuelve los indicadores métricos en tiempo real con soporte para caché en memoria."""
    cached = cache.get("api_estadisticas")
    if cached:
        return JsonResponse(cached)

    total = Producto.objects.count()
    activos = Producto.objects.filter(estado=True).count()
    unidades = Producto.objects.filter(estado=True).aggregate(t=Sum('cantidad_existente'))['t'] or 0
    valor_total = sum(float(p.precio) * p.cantidad_existente for p in Producto.objects.filter(estado=True))
    mas_caro = Producto.objects.filter(estado=True).order_by('-precio').first()
    mas_barato = Producto.objects.filter(estado=True).order_by('precio').first()
    alertas_count = Producto.objects.filter(estado=True, cantidad_existente__lte=F('stock_minimo')).count()

    data = {
        "total_productos": total,
        "productos_activos": activos,
        "unidades_totales": unidades,
        "valor_total": round(valor_total, 2),
        "valor_total_formateado": f"${valor_total:,.2f}",
        "alertas_count": alertas_count,
        "mas_caro": {
            "codigo": mas_caro.codigo if mas_caro else "",
            "nombre": mas_caro.nombre if mas_caro else "",
            "precio": float(mas_caro.precio) if mas_caro else 0.0,
            "cantidad": mas_caro.cantidad_existente if mas_caro else 0,
        } if mas_caro else None,
        "mas_barato": {
            "codigo": mas_barato.codigo if mas_barato else "",
            "nombre": mas_barato.nombre if mas_barato else "",
            "precio": float(mas_barato.precio) if mas_barato else 0.0,
            "cantidad": mas_barato.cantidad_existente if mas_barato else 0,
        } if mas_barato else None,
        "modelo_activo": obtener_modelo_activo()
    }

    cache.set("api_estadisticas", data, 300)
    return JsonResponse(data)