import json
import logging
import hashlib
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.core.cache import cache

from .models import ChatHistory, Producto, MovimientoStock, ConsultaIA
from .forms import ProductoForm, AjusteStockForm

# Importar capa de servicios (Patrones Service Layer y Strategy)
from .services.inventory_service import (
    listar_productos,
    calcular_estadisticas,
    obtener_reporte_predefinido,
    registrar_movimiento_kardex,
    obtener_kardex_producto,
    invalidar_cache_inventario,
)
from .services.ollama_service import (
    consultar_ollama_local,
    resolver_contexto_inteligente,
    construir_prompt_chat,
    obtener_modelo_activo,
    obtener_url_ollama,
    limpiar_cache_chat,
)
from .services.export_service import (
    ChatHistoryExportStrategy,
    ProductCatalogExportStrategy,
    importar_catalogo_csv,
)

logger = logging.getLogger(__name__)


def invalidar_cache():
    """Invalida la caché de estadísticas, reportes e inferencias al modificarse el inventario."""
    cache.clear()
    invalidar_cache_inventario()
    limpiar_cache_chat()


# ==============================================================================
# VISTA PRINCIPAL
# ==============================================================================

def chatbot_view(request):
    """Renderiza la interfaz web principal con métricas iniciales y categorías cargadas."""
    stats = calcular_estadisticas()
    categorias = list(
        Producto.objects.filter(estado=True)
        .values_list("categoria", flat=True)
        .distinct()
        .order_by("categoria")
    )

    context = {
        "total_productos": stats["total_productos"],
        "productos_activos": stats["productos_activos"],
        "unidades_totales": stats["unidades_totales"],
        "valor_total": stats["valor_total_formateado"].replace("Bs. ", ""),
        "mas_caro": stats["mas_caro"],
        "mas_barato": stats["mas_barato"],
        "alertas_count": stats["alertas_count"],
        "categorias": categorias,
        "modelo_activo": stats["modelo_activo"],
        "ip_equipo": getattr(settings, "EQUIPO_IP", "172.25.4.247"),
    }
    return render(request, "index.html", context)


# ==============================================================================
# CRUD Y CONTROL DE PRODUCTOS (RF-01, RF-02, RF-03, RF-04)
# ==============================================================================

def api_productos(request):
    """
    Endpoint JSON para listar y buscar productos con soporte de paginación (RF-02).
    Acepta parámetros: q, categoria, estado, orden, solo_alertas, page, page_size.
    """
    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    estado = request.GET.get("estado", "activos").strip().lower()
    orden = request.GET.get("orden", "codigo_asc").strip()
    solo_alertas = request.GET.get("solo_alertas", "false").lower() == "true"

    try:
        raw_page = request.GET.get("page") or request.GET.get("pagina", "1")
        page = int(raw_page)
    except (ValueError, TypeError):
        page = 1

    try:
        raw_size = request.GET.get("page_size") or request.GET.get("por_pagina", "15")
        page_size = int(raw_size) if str(raw_size) != "0" and str(raw_size).lower() != "todos" else 0
    except (ValueError, TypeError):
        page_size = 15

    resultado = listar_productos(
        q=q,
        categoria=categoria,
        estado=estado,
        orden=orden,
        solo_alertas=solo_alertas,
        page=page,
        page_size=page_size
    )

    # Aliases en español para máxima compatibilidad
    resultado["pagina"] = resultado["page"]
    resultado["por_pagina"] = resultado["page_size"]
    resultado["total_paginas"] = resultado["total_pages"]

    return JsonResponse(resultado)


@csrf_exempt
@require_http_methods(["POST"])
def api_crear_producto(request):
    """RF-01: Registro de un nuevo producto con validación estricta y apertura en Kardex."""
    form = ProductoForm(request.POST)
    if form.is_valid():
        producto = form.save()
        # Registrar movimiento inicial de apertura en Kardex si tiene existencias
        if producto.cantidad_existente > 0:
            registrar_movimiento_kardex(
                producto=producto,
                tipo="ENTRADA",
                cantidad=producto.cantidad_existente,
                stock_previo=0,
                stock_resultante=producto.cantidad_existente,
                motivo="Registro inicial y alta en catálogo",
                usuario="Administrador"
            )
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{producto.nombre}' ({producto.codigo}) registrado exitosamente.",
            "id": producto.id,
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "precio": float(producto.precio),
            "cantidad": producto.cantidad_existente,
        }, status=201)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Errores de validación en el formulario.",
            "errors": form.errors
        }, status=400)


def api_obtener_producto(request, pk):
    """Obtiene los datos detallados de un producto para edición modal."""
    producto = get_object_or_404(Producto, pk=pk)
    return JsonResponse({
        "id": producto.id,
        "codigo": producto.codigo,
        "sku": producto.codigo,
        "nombre": producto.nombre,
        "categoria": producto.categoria,
        "marca": producto.marca,
        "precio": float(producto.precio),
        "cantidad_existente": producto.cantidad_existente,
        "stock": producto.cantidad_existente,
        "stock_minimo": producto.stock_minimo,
        "estado": producto.estado,
        "descripcion": producto.descripcion,
        "especificaciones": producto.especificaciones,
        "estado_stock": producto.estado_stock,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_editar_producto(request, pk):
    """RF-03: Actualización de datos de un producto con control de inventario."""
    producto = get_object_or_404(Producto, pk=pk)
    stock_anterior = producto.cantidad_existente
    form = ProductoForm(request.POST, instance=producto)

    if form.is_valid():
        prod_guardado = form.save()
        # Si se editó la cantidad directamente, registrar ajuste en Kardex
        if stock_anterior != prod_guardado.cantidad_existente:
            delta = prod_guardado.cantidad_existente - stock_anterior
            registrar_movimiento_kardex(
                producto=prod_guardado,
                tipo="AJUSTE",
                cantidad=abs(delta),
                stock_previo=stock_anterior,
                stock_resultante=prod_guardado.cantidad_existente,
                motivo=f"Ajuste manual de stock en edición ({'+' if delta > 0 else ''}{delta} uds)",
                usuario="Administrador"
            )
        invalidar_cache()
        return JsonResponse({
            "status": "ok",
            "message": f"Producto '{prod_guardado.nombre}' actualizado correctamente.",
            "id": prod_guardado.id,
            "codigo": prod_guardado.codigo,
            "precio": float(prod_guardado.precio),
            "cantidad": prod_guardado.cantidad_existente,
        })
    else:
        return JsonResponse({
            "status": "error",
            "message": "Errores de validación en la edición del producto.",
            "errors": form.errors
        }, status=400)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def api_eliminar_producto(request, pk):
    """RF-04: Eliminación lógica (desactivar) o física de un producto."""
    producto = get_object_or_404(Producto, pk=pk)
    nombre = producto.nombre
    codigo = producto.codigo
    accion = request.POST.get("tipo_eliminacion", "logica").strip()

    if accion == "fisica":
        producto.delete()
        mensaje = f"Producto '{nombre}' ({codigo}) eliminado definitivamente del sistema."
    else:
        producto.estado = False
        producto.save()
        mensaje = f"Producto '{nombre}' ({codigo}) desactivado lógicamente (Estado: Inactivo)."

    invalidar_cache()
    return JsonResponse({"status": "ok", "message": mensaje})


@csrf_exempt
@require_http_methods(["POST"])
def api_cambiar_estado(request, pk):
    """Alterna rápidamente el estado Activo / Inactivo de un producto."""
    producto = get_object_or_404(Producto, pk=pk)
    producto.estado = not producto.estado
    producto.save()
    invalidar_cache()

    estado_str = "Activo" if producto.estado else "Inactivo"
    return JsonResponse({
        "status": "ok",
        "message": f"Producto '{producto.nombre}' cambiado a {estado_str}.",
        "estado": producto.estado,
        "estado_texto": estado_str
    })


# ==============================================================================
# CONTROL DE EXISTENCIA Y KARDEX (RF-05)
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_ajustar_stock(request, pk):
    """Control de existencia atómico con registro obligatorio en Kardex (RF-05)."""
    producto = get_object_or_404(Producto, pk=pk)
    form = AjusteStockForm(request.POST, producto=producto)

    if form.is_valid():
        accion = form.cleaned_data["accion"]
        cantidad = form.cleaned_data["cantidad"]
        motivo = request.POST.get("motivo", "").strip()
        stock_previo = producto.cantidad_existente

        if accion == "aumentar":
            producto.cantidad_existente += cantidad
            tipo_mov = "ENTRADA"
            motivo = motivo or f"Ingreso / Aumento de existencias (+{cantidad} uds)"
            mensaje = f"Se aumentaron {cantidad} unidades. Nueva existencia: {producto.cantidad_existente}."
        else:
            producto.cantidad_existente -= cantidad
            tipo_mov = "SALIDA"
            motivo = motivo or f"Despacho / Salida de almacén (-{cantidad} uds)"
            mensaje = f"Se disminuyeron {cantidad} unidades. Nueva existencia: {producto.cantidad_existente}."

        producto.save()

        # Registrar transacción inmutable en Kardex
        registrar_movimiento_kardex(
            producto=producto,
            tipo=tipo_mov,
            cantidad=cantidad,
            stock_previo=stock_previo,
            stock_resultante=producto.cantidad_existente,
            motivo=motivo,
            usuario="Administrador"
        )
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


def api_kardex_producto(request, pk):
    """Retorna el historial completo de movimientos en el Kardex para el producto especificado."""
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = obtener_kardex_producto(pk)

    data = [
        {
            "id": m.id,
            "tipo": m.tipo,
            "cantidad": m.cantidad,
            "stock_previo": m.stock_previo,
            "stock_resultante": m.stock_resultante,
            "motivo": m.motivo,
            "usuario": m.usuario,
            "fecha": m.fecha.strftime("%d/%m/%Y %H:%M:%S")
        }
        for m in movimientos
    ]

    return JsonResponse({
        "status": "ok",
        "producto": {
            "id": producto.id,
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "stock_actual": producto.cantidad_existente,
            "stock_minimo": producto.stock_minimo,
            "precio": float(producto.precio),
        },
        "total_movimientos": len(data),
        "movimientos": data
    })


# ==============================================================================
# REPORTES Y ESTADÍSTICAS (RF-06)
# ==============================================================================

def api_reportes(request, tipo):
    """Genera cualquiera de los 8 reportes oficiales con soporte de explicación en IA local."""
    explicar_ia = request.GET.get("explicar", "false").lower() == "true"

    try:
        titulo, descripcion, resumen_texto, datos = obtener_reporte_predefinido(tipo)
    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    explicacion_ia = None
    if explicar_ia:
        prompt_reporte = f"""Eres un asistente encargado de consultar un inventario de productos.
Genera una explicación clara, natural, profesional y concisa (en 2 a 4 oraciones) en español para el usuario sobre el siguiente reporte oficial:

Reporte: {titulo}
Descripción: {descripcion}
Datos oficiales: {resumen_texto}
Detalle: {json.dumps(datos, ensure_ascii=False)}

Instrucciones:
- Responde únicamente con base en estos datos.
- Menciona precios siempre en Bolivianos con el prefijo "Bs." cuando aplique.
- No inventes cantidades."""

        exito, resp_ia = consultar_ollama_local(prompt_reporte, timeout=80)
        explicacion_ia = resp_ia if exito else f"No fue posible generar la explicación: {resp_ia}"

    return JsonResponse({
        "status": "ok",
        "tipo": tipo,
        "titulo": titulo,
        "descripcion": descripcion,
        "resumen_texto": resumen_texto,
        "datos": datos,
        "explicacion_ia": explicacion_ia
    })


def api_estadisticas(request):
    """Devuelve los indicadores métricos en tiempo real con caché."""
    data = calcular_estadisticas()
    return JsonResponse(data)


# ==============================================================================
# CHAT CON INTELIGENCIA ARTIFICIAL LOCAL (RF-07, RF-08, RF-09)
# ==============================================================================

def _generar_clave_cache(pregunta):
    norm = " ".join(pregunta.lower().strip().replace("¿", "").replace("?", "").split())
    return "chat_" + hashlib.md5(norm.encode("utf-8")).hexdigest()


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    """Procesa preguntas en el chat enviando los datos a Ollama para respuesta en lenguaje natural."""
    pregunta = request.POST.get("user_input", "").strip()
    if not pregunta:
        return JsonResponse({"error": "La pregunta no puede estar vacía."}, status=400)

    p_lower = pregunta.lower()

    # RF-09: Restricción estricta ante preguntas no pertinentes
    temas_ajenos = ["cocina", "pizza", "receta", "fútbol", "futbol", "mundial", "canción", "cancion", "poema", "política", "politica", "chiste", "cuento", "clima", "película", "pelicula", "capital de"]
    if any(tema in p_lower for tema in temas_ajenos):
        resp_declinada = "No encontré información suficiente en el inventario para responder esa pregunta."
        ChatHistory.objects.create(user_input=pregunta, bot_response=resp_declinada)
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": resp_declinada,
            "timestamp": datetime.now().strftime("%H:%M"),
            "cached": False,
            "modelo": obtener_modelo_activo()
        })

    # Verificación en caché de inferencias previas
    clave_cache = _generar_clave_cache(pregunta)
    resp_en_cache = cache.get(clave_cache)
    if resp_en_cache:
        ChatHistory.objects.create(user_input=pregunta, bot_response=resp_en_cache)
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": resp_en_cache,
            "timestamp": datetime.now().strftime("%H:%M"),
            "cached": True,
            "modelo": obtener_modelo_activo()
        })

    prompt_final = construir_prompt_chat(pregunta)
    exito, respuesta = consultar_ollama_local(prompt_final, timeout=80)

    if not exito:
        return JsonResponse({
            "user_input": pregunta,
            "bot_response": f"⚠️ Error con Ollama: {respuesta}",
            "timestamp": datetime.now().strftime("%H:%M"),
            "cached": False,
            "modelo": obtener_modelo_activo()
        })

    # Guardar en memoria caché y registrar en base de datos
    cache.set(clave_cache, respuesta, timeout=300)
    ChatHistory.objects.create(user_input=pregunta, bot_response=respuesta)

    return JsonResponse({
        "user_input": pregunta,
        "bot_response": respuesta,
        "timestamp": datetime.now().strftime("%H:%M"),
        "cached": False,
        "modelo": obtener_modelo_activo()
    })


@csrf_exempt
@require_http_methods(["POST"])
def chat_stream(request):
    """Streaming de respuestas en tiempo real mediante Server-Sent Events (SSE)."""
    pregunta = request.POST.get("user_input", "").strip()
    if not pregunta:
        return JsonResponse({"error": "Pregunta vacía."}, status=400)

    p_lower = pregunta.lower()
    temas_ajenos = ["cocina", "pizza", "receta", "fútbol", "futbol", "mundial", "canción", "cancion", "poema", "política", "politica", "chiste", "cuento", "clima", "película", "pelicula", "capital de"]
    if any(tema in p_lower for tema in temas_ajenos):
        resp_declinada = "No encontré información suficiente en el inventario para responder esa pregunta."
        ChatHistory.objects.create(user_input=pregunta, bot_response=resp_declinada)
        def sse_declinada():
            yield f"data: {json.dumps({'token': resp_declinada, 'done': True, 'full_text': resp_declinada}, ensure_ascii=False)}\n\n"
        return StreamingHttpResponse(sse_declinada(), content_type="text/event-stream")

    url = obtener_url_ollama()
    modelo = obtener_modelo_activo()
    prompt_final = construir_prompt_chat(pregunta)

    def sse_generator():
        import requests
        payload = {
            "model": modelo,
            "prompt": prompt_final,
            "stream": True,
            "options": {
                "temperature": 0.05,
                "num_predict": 140,
                "num_ctx": 1200,
                "num_thread": 4
            }
        }
        texto_completo = ""
        try:
            with requests.post(url, json=payload, stream=True, timeout=80) as r:
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        token = chunk.get("response", "")
                        texto_completo += token
                        done = chunk.get("done", False)
                        yield f"data: {json.dumps({'token': token, 'done': done, 'full_text': texto_completo if done else None}, ensure_ascii=False)}\n\n"
                        if done:
                            break
            ChatHistory.objects.create(user_input=pregunta, bot_response=texto_completo.strip())
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(sse_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ==============================================================================
# EXPORTACIÓN E IMPORTACIÓN (RF-10 Y GESTIÓN DE INVENTARIO)
# ==============================================================================

def chat_history(request):
    """Devuelve las últimas interacciones del historial en JSON."""
    historial = ChatHistory.objects.all().order_by("-timestamp")[:30]
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
    """Exportación del historial de chat utilizando el patrón Strategy."""
    formato = request.GET.get("formato", "md").lower()
    estrategia = ChatHistoryExportStrategy()
    return estrategia.exportar(formato)


def api_exportar_productos(request):
    """Exportación del catálogo oficial de productos en CSV o Hoja Oficial en PDF (Strategy Pattern)."""
    formato = request.GET.get("formato", "csv").lower()
    estrategia = ProductCatalogExportStrategy()
    return estrategia.exportar(formato)


@csrf_exempt
@require_http_methods(["POST"])
def api_importar_productos(request):
    """Importación masiva de productos desde un archivo CSV con auditoría en Kardex."""
    if "archivo_csv" not in request.FILES:
        return JsonResponse({"status": "error", "message": "No se adjuntó ningún archivo CSV."}, status=400)

    archivo = request.FILES["archivo_csv"]
    if not archivo.name.endswith(".csv"):
        return JsonResponse({"status": "error", "message": "El archivo debe tener extensión .csv."}, status=400)

    resultado = importar_catalogo_csv(archivo, usuario="Administrador")
    return JsonResponse({
        "status": "ok" if resultado["exito"] else "parcial",
        "creados": resultado.get("creados", 0),
        "actualizados": resultado.get("actualizados", 0),
        "total_procesados": resultado.get("total_procesados", 0),
        "errores": resultado.get("errores", []),
        "resultado": resultado
    })


@csrf_exempt
@require_http_methods(["POST"])
def clear_history(request):
    """Vacía de manera segura el historial de consultas de la base de datos."""
    total = ChatHistory.objects.count()
    ChatHistory.objects.all().delete()
    return JsonResponse({
        "status": "ok",
        "message": f"Se eliminaron {total} interacciones del historial correctamente."
    })