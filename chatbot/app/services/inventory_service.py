from decimal import Decimal
from django.db.models import Q, F, Sum, Count
from django.core.cache import cache
from ..models import Producto, MovimientoStock

def invalidar_cache_inventario():
    """Invalida la caché de estadísticas y reportes al producirse cambios en los productos."""
    try:
        cache.delete("api_estadisticas")
        # Invalidar reportes en caché
        for rep in ["todos", "mas_caro", "mas_barato", "pocas_existencias", "agotados", "por_categoria", "valor_total", "mayor_existencia"]:
            cache.delete(f"reporte_{rep}")
    except Exception:
        pass


def registrar_movimiento_kardex(producto, tipo, cantidad, stock_previo, stock_resultante, motivo, usuario="Administrador"):
    """Registra una transacción atómica e inmutable en el Kardex de almacén."""
    return MovimientoStock.objects.create(
        producto=producto,
        tipo=tipo,
        cantidad=cantidad,
        stock_previo=stock_previo,
        stock_resultante=stock_resultante,
        motivo=motivo,
        usuario=usuario
    )


def obtener_kardex_producto(producto_id):
    """Obtiene el historial de auditoría de un producto ordenado cronológicamente descendente."""
    return MovimientoStock.objects.filter(producto_id=producto_id).order_by("-fecha")


def inicializar_kardex_si_vacio():
    """Asegura que los productos registrados cuenten con su movimiento de apertura en el Kardex."""
    if MovimientoStock.objects.count() == 0:
        for p in Producto.objects.all():
            if p.cantidad_existente > 0:
                registrar_movimiento_kardex(
                    producto=p,
                    tipo="ENTRADA",
                    cantidad=p.cantidad_existente,
                    stock_previo=0,
                    stock_resultante=p.cantidad_existente,
                    motivo="Inventario inicial de apertura de almacén",
                    usuario="Sistema"
                )


def listar_productos(q="", categoria="", estado="activos", orden="codigo_asc", solo_alertas=False, page=1, page_size=15):
    """
    Consulta y filtra el catálogo de productos con paginación integrada.
    Si page_size es None o 0, devuelve todos los productos sin paginación (compatibilidad).
    """
    qs = Producto.objects.all()

    # Filtro por estado
    if estado == "activos":
        qs = qs.filter(estado=True)
    elif estado == "inactivos":
        qs = qs.filter(estado=False)

    # Búsqueda por texto (código, nombre, categoría, marca, descripción)
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

    # Alertas de stock crítico
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

    total_items = qs.count()

    # Paginación
    if page_size and page_size > 0:
        import math
        total_pages = max(1, math.ceil(total_items / page_size))
        page = max(1, min(page, total_pages))
        inicio = (page - 1) * page_size
        fin = inicio + page_size
        items = qs[inicio:fin]
    else:
        items = qs
        total_pages = 1
        page = 1
        page_size = total_items

    productos_data = [
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
            "fecha_actualizacion": p.fecha_actualizacion.strftime("%d/%m/%Y %H:%M") if hasattr(p, "fecha_actualizacion") and p.fecha_actualizacion else "",
        }
        for p in items
    ]

    return {
        "productos": productos_data,
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def calcular_estadisticas():
    """Calcula y cachea las métricas maestras del inventario."""
    cached = cache.get("api_estadisticas")
    if cached:
        return cached

    total = Producto.objects.count()
    activos = Producto.objects.filter(estado=True).count()
    unidades = Producto.objects.filter(estado=True).aggregate(t=Sum('cantidad_existente'))['t'] or 0
    valor_total = sum(float(p.precio) * p.cantidad_existente for p in Producto.objects.filter(estado=True))
    mas_caro = Producto.objects.filter(estado=True).order_by('-precio').first()
    mas_barato = Producto.objects.filter(estado=True).order_by('precio').first()
    alertas_count = Producto.objects.filter(estado=True, cantidad_existente__lte=F('stock_minimo')).count()

    from .ollama_service import obtener_modelo_activo

    data = {
        "total_productos": total,
        "productos_activos": activos,
        "unidades_totales": unidades,
        "valor_total": round(valor_total, 2),
        "valor_total_formateado": f"Bs. {valor_total:,.2f}",
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
    return data


def obtener_reporte_predefinido(tipo):
    """
    Genera la data estructurada de cualquiera de los 8 reportes oficiales requeridos (RF-06).
    Retorna una tupla: (titulo, descripcion, resumen_texto, datos)
    """
    qs_activos = Producto.objects.filter(estado=True)

    if tipo == "todos":
        titulo = "1. Catálogo Completo de Productos"
        descripcion = "Listado general de todas las referencias de productos registradas en el inventario."
        datos = [
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "precio": float(p.precio),
                "cantidad": p.cantidad_existente,
                "stock_minimo": p.stock_minimo,
                "estado_stock": p.estado_stock,
            }
            for p in Producto.objects.all().order_by("codigo")
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
            resumen_texto = f"El producto más costoso es '{p.nombre}' (Código: {p.codigo}) con un precio de Bs. {p.precio} y {p.cantidad_existente} unidades disponibles."
        else:
            datos = []
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
            resumen_texto = f"El producto más económico es '{p.nombre}' (Código: {p.codigo}) con un precio de Bs. {p.precio} y {p.cantidad_existente} unidades disponibles."
        else:
            datos = []
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
                "valor_total_formateado": f"Bs. {valor_cat:,.2f}"
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
            "valor_total_inventario_bs": round(valor_total, 2),
            "valor_total_inventario_usd": round(valor_total, 2),
            "valor_total_formateado": f"Bs. {valor_total:,.2f}",
            "precio_promedio": round(promedio_precio, 2)
        }]
        resumen_texto = f"El valor total del inventario es de Bs. {valor_total:,.2f} distribuidos en {unidades} unidades físicas de {total_refs} referencias de productos."

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
        raise ValueError(f"Tipo de reporte desconocido: {tipo}")

    return titulo, descripcion, resumen_texto, datos
