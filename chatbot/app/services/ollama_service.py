import os
import json
import logging
from cachetools import TTLCache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.db.models import Sum, F
from ..models import Producto

logger = logging.getLogger(__name__)

# Caché en memoria para respuestas frecuentes de IA (TTL 5 min)
_chat_cache = TTLCache(maxsize=1000, ttl=300)

# Pool de conexiones persistentes con keep-alive (Patrón Singleton)
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


def limpiar_cache_chat():
    """Limpia el caché de respuestas generadas por IA."""
    _chat_cache.clear()


def obtener_modelo_activo():
    """Obtiene el nombre del modelo configurado para Ollama desde entorno o settings."""
    modelo = os.environ.get("OLLAMA_MODEL")
    if modelo:
        return modelo
    return getattr(settings, "OLLAMA_MODEL", "qwen2.5:1.5b")


def obtener_url_ollama():
    """Obtiene la URL de la API de Ollama."""
    url = os.environ.get("OLLAMA_URL")
    if url:
        return url
    return getattr(settings, "OLLAMA_URL", "http://localhost:11434/api/generate")


def consultar_ollama_local(prompt, timeout=80):
    """
    Envía una consulta a Ollama ejecutándose localmente.
    Retorna una tupla: (exito: bool, respuesta_o_error: str)
    """
    url = obtener_url_ollama()
    modelo = obtener_modelo_activo()
    session = _get_session()

    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_predict": 140,
            "num_ctx": 1200,
            "num_thread": 4
        }
    }

    try:
        response = session.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", "").strip()
        else:
            return False, f"Ollama respondió con código HTTP {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar con el servicio local de Ollama en http://localhost:11434. Verifique que Ollama esté iniciado."
    except requests.exceptions.Timeout:
        return False, f"La consulta a Ollama excedió el tiempo límite ({timeout}s)."


def generar_contexto_oficial_inventario():
    """Genera un resumen oficial de los datos exactos del inventario."""
    qs_act = Producto.objects.filter(estado=True)
    total_referencias = qs_act.count()
    unidades_totales = qs_act.aggregate(t=Sum("cantidad_existente"))["t"] or 0
    valor_total = sum(float(p.precio) * p.cantidad_existente for p in qs_act)

    mas_caro = qs_act.order_by("-precio").first()
    mas_barato = qs_act.order_by("precio").first()

    agotados = list(qs_act.filter(cantidad_existente=0))
    if agotados:
        nombres_ag = [f"{p.nombre} (Cód: {p.codigo})" for p in agotados]
        agotados_str = f"PRODUCTOS AGOTADOS (stock 0): {', '.join(nombres_ag)}"
    else:
        agotados_str = "PRODUCTOS AGOTADOS: Ninguno. Todos los productos activos tienen stock disponible."

    pocas = list(qs_act.filter(cantidad_existente__lte=F("stock_minimo"), cantidad_existente__gt=0))
    if pocas:
        nombres_poc = [f"{p.nombre} (Stock: {p.cantidad_existente}, Mín: {p.stock_minimo})" for p in pocas]
        pocas_str = f"PRODUCTOS CON POCAS EXISTENCIAS: {', '.join(nombres_poc)}"
    else:
        pocas_str = "PRODUCTOS CON POCAS EXISTENCIAS: Ninguno. Todos los productos superan su nivel mínimo fijado."

    cats = list(qs_act.values_list("categoria", flat=True).distinct().order_by("categoria"))
    cats_str = ", ".join(cats)

    return f"""MÉTRICAS OFICIALES Y DATOS EXACTOS DE LA BASE DE DATOS:
- {agotados_str}
- {pocas_str}
- PRODUCTO MÁS CARO: {mas_caro.nombre if mas_caro else 'Ninguno'} (Bs. {mas_caro.precio if mas_caro else 0}, Código: {mas_caro.codigo if mas_caro else ''})
- PRODUCTO MÁS BARATO: {mas_barato.nombre if mas_barato else 'Ninguno'} (Bs. {mas_barato.precio if mas_barato else 0}, Código: {mas_barato.codigo if mas_barato else ''})
- Total referencias de productos: {total_referencias}
- Total unidades físicas en almacén: {unidades_totales} unidades
- Valor total del inventario: Bs. {valor_total:,.2f}
- Categorías registradas: {cats_str}"""


def resolver_contexto_inteligente(pregunta=""):
    """
    Analiza la intención de la pregunta y extrae determinísticamente de la base de datos:
    1. hecho_verificado: Hecho oficial exacto para evitar alucinaciones.
    2. productos: Lista de productos relevantes.
    """
    qs = Producto.objects.filter(estado=True)
    p_lower = pregunta.lower().strip()

    # 1. Agotados
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
            hecho = f"El producto más barato de todo el inventario es {p.nombre} con un precio de Bs. {p.precio} (Código: {p.codigo}, categoría: {p.categoria})."
            return hecho, [p]
        return "No hay productos disponibles.", []

    # 3. Más caro
    elif any(w in p_lower for w in ["caro", "costoso", "mayor precio", "más alto", "mas alto", "alto precio", "más valor"]):
        p = qs.order_by("-precio").first()
        if p:
            hecho = f"El producto más caro de todo el inventario es {p.nombre} con un precio de Bs. {p.precio} (Código: {p.codigo}, categoría: {p.categoria})."
            return hecho, [p]
        return "No hay productos disponibles.", []

    # 4. Pocas existencias / Stock bajo
    elif any(w in p_lower for w in ["poco", "poca", "pocos", "pocas", "stock bajo", "bajo stock", "escaso", "escasos", "escasez", "alerta", "reposición", "reposicion", "por agotarse", "por terminarse"]):
        prods = list(qs.filter(cantidad_existente__lte=F("stock_minimo"), cantidad_existente__gt=0).order_by("cantidad_existente"))
        if prods:
            detalles = [f"{p.nombre} ({p.cantidad_existente} uds en stock, nivel mínimo: {p.stock_minimo})" for p in prods]
            hecho = f"Hay exactamente {len(prods)} productos con pocas existencias (stock menor o igual al mínimo fijado): {', '.join(detalles)}."
        else:
            hecho = "No hay productos con existencias críticas; todos los productos activos superan su stock mínimo."
        return hecho, prods

    # 5. Totales y Valoración Económica
    elif any(w in p_lower for w in ["unidades hay", "total de unidades", "cuántas unidades", "cuantas unidades", "valor total", "cuánto vale", "cuanto vale", "almacén", "almacen"]):
        unidades = qs.aggregate(t=Sum("cantidad_existente"))["t"] or 0
        valor = sum(float(p.precio) * p.cantidad_existente for p in qs)
        hecho = f"El almacén cuenta actualmente con un total consolidado de {unidades} unidades físicas en existencia, distribuidas en {qs.count()} referencias activas, con un valor total económico de Bs. {valor:,.2f}."
        return hecho, list(qs.order_by("-precio")[:6])

    # 6. Mayor existencia
    elif any(w in p_lower for w in ["mayor cantidad", "más cantidad", "mas cantidad", "más unidades", "mayor disponibilidad"]):
        prods = list(qs.order_by("-cantidad_existente")[:5])
        nombres = [f"{p.nombre} ({p.cantidad_existente} uds)" for p in prods]
        hecho = f"Los productos con mayor número de existencias en almacén son: {', '.join(nombres)}."
        return hecho, prods

    # 7. Por categoría o búsqueda general
    palabras = [w for w in p_lower.replace("?", "").replace("¿", "").split() if len(w) > 2]
    q_filter = None
    for w in palabras:
        f = Q(nombre__icontains=w) | Q(codigo__icontains=w) | Q(categoria__icontains=w) | Q(marca__icontains=w)
        q_filter = (q_filter | f) if q_filter else f

    prods = list(qs.filter(q_filter).distinct()[:10]) if q_filter else list(qs.order_by("-precio")[:10])
    return "Consulta general del catálogo de inventario.", prods


def construir_prompt_chat(pregunta):
    """Construye el prompt estructurado oficial para enviar a Ollama."""
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
Moneda oficial del inventario: Bolivianos (Bs. / BOB). Todos los precios están expresados en Bolivianos (Bs.).

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
2. No inventes productos, cantidades ni precios. Menciona siempre los precios en Bolivianos con el prefijo "Bs." y códigos cuando sea pertinente.
3. Si la pregunta no está relacionada con los productos o el inventario, responde exclusivamente:
"No encontré información suficiente en el inventario para responder esa pregunta."
Respuesta:"""
