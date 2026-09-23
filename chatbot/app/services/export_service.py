import io
import csv
import json
from abc import ABC, abstractmethod
from datetime import datetime
from django.http import HttpResponse
from ..models import Producto, ChatHistory, MovimientoStock

class BaseExportStrategy(ABC):
    """Clase base abstracta para el patrón Strategy de exportación de documentos."""
    @abstractmethod
    def exportar(self, formato="csv", **kwargs) -> HttpResponse:
        pass


class ChatHistoryExportStrategy(BaseExportStrategy):
    """Estrategia de exportación para el historial de conversaciones y consultas a la IA."""

    def exportar(self, formato="md", **kwargs) -> HttpResponse:
        formato = formato.lower()
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
            buffer = io.StringIO()
            buffer.write('\ufeff')
            writer = csv.writer(buffer)
            writer.writerow(["ID", "Fecha y Hora", "Pregunta", "Respuesta"])
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
    <title>Historial de Consultas IA - {fecha_str}</title>
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
        <h1>Historial Oficial de Consultas IA</h1>
        <p style="color:#64748b; font-size: 0.85rem;">Exportado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Total: {historial.count()} consultas</p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 18px 0;">
        {"".join(filas_html) if filas_html else "<p>No hay consultas registradas.</p>"}
    </div>
</body>
</html>"""
            response = HttpResponse(html_doc, content_type="text/html; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="historial_consultas_{fecha_str}.html"'
            return response

        else: # Markdown
            lineas = [
                "# Historial de Consultas al Inventario con IA",
                f"- **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                f"- **Total de interacciones:** {historial.count()}",
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


class ProductCatalogExportStrategy(BaseExportStrategy):
    """Estrategia de exportación para el catálogo oficial de inventario de productos."""

    def exportar(self, formato="csv", **kwargs) -> HttpResponse:
        formato = formato.lower()
        productos = Producto.objects.all().order_by("codigo")
        fecha_str = datetime.now().strftime("%Y-%m-%d_%H%M")

        if formato == "csv":
            buffer = io.StringIO()
            buffer.write('\ufeff')
            writer = csv.writer(buffer)
            writer.writerow([
                "Código", "Nombre", "Categoría", "Marca",
                "Precio (Bs.)", "Cantidad Existente", "Stock Mínimo",
                "Valor Total (Bs.)", "Estado", "Estado Stock", "Fecha Registro"
            ])
            for p in productos:
                valor_total_item = round(float(p.precio) * p.cantidad_existente, 2)
                writer.writerow([
                    p.codigo,
                    p.nombre,
                    p.categoria,
                    p.marca,
                    f"{p.precio:.2f}",
                    p.cantidad_existente,
                    p.stock_minimo,
                    f"{valor_total_item:.2f}",
                    "Activo" if p.estado else "Inactivo",
                    p.estado_stock,
                    p.fecha_registro.strftime("%d/%m/%Y %H:%M") if p.fecha_registro else ""
                ])
            response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="catalogo_inventario_{fecha_str}.csv"'
            return response

        elif formato in ("html", "pdf"):
            # Generar Hoja Oficial de Inventario con formato ejecutivo y firmas de auditoría
            total_items = productos.count()
            unidades_totales = sum(p.cantidad_existente for p in productos.filter(estado=True))
            valor_total_bs = sum(float(p.precio) * p.cantidad_existente for p in productos.filter(estado=True))
            from django.db.models import F
            alertas = productos.filter(estado=True, cantidad_existente__lte=F("stock_minimo")).count()
            
            filas_tr = []
            for idx, p in enumerate(productos, start=1):
                val_prod = float(p.precio) * p.cantidad_existente
                badge_color = "#10b981" if p.estado_stock == "En Stock" else ("#f59e0b" if p.estado_stock == "Stock Bajo" else "#ef4444")
                filas_tr.append(f"""
                <tr>
                    <td style="text-align: center; color: #64748b;">{idx}</td>
                    <td><strong>{p.codigo}</strong></td>
                    <td>{p.nombre}</td>
                    <td>{p.categoria}</td>
                    <td style="text-align: right;">Bs. {p.precio:,.2f}</td>
                    <td style="text-align: center; font-weight: 600;">{p.cantidad_existente}</td>
                    <td style="text-align: center; color: #64748b;">{p.stock_minimo}</td>
                    <td style="text-align: right; font-weight: 700;">Bs. {val_prod:,.2f}</td>
                    <td style="text-align: center;"><span style="color: {badge_color}; font-weight: 600;">{p.estado_stock}</span></td>
                </tr>
                """)

            html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hoja Oficial de Inventario de Almacén - {fecha_str}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; padding: 24px; color: #0f172a; margin: 0; }}
        .sheet {{ max-width: 1050px; margin: 0 auto; background: #fff; padding: 36px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0f172a; padding-bottom: 18px; margin-bottom: 24px; }}
        .company-title {{ font-size: 1.45rem; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; }}
        .company-sub {{ font-size: 0.85rem; color: #64748b; margin-top: 4px; }}
        .kpi-summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }}
        .kpi-box {{ background: #f1f5f9; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #3b82f6; }}
        .kpi-box-label {{ font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700; }}
        .kpi-box-val {{ font-size: 1.25rem; font-weight: 800; color: #0f172a; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-bottom: 30px; }}
        th {{ background: #0f172a; color: #fff; padding: 8px 10px; text-align: left; font-weight: 600; font-size: 0.76rem; text-transform: uppercase; }}
        td {{ padding: 7px 10px; border-bottom: 1px solid #e2e8f0; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .signatures {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; margin-top: 50px; page-break-inside: avoid; }}
        .sig-box {{ border-top: 1px dashed #64748b; padding-top: 8px; text-align: center; font-size: 0.8rem; color: #334155; }}
        .btn-print {{ background: #2563eb; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; float: right; font-weight: 700; font-size: 0.88rem; }}
        @media print {{
            .btn-print {{ display: none; }}
            body {{ padding: 0; background: #fff; }}
            .sheet {{ box-shadow: none; border: none; padding: 0; max-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="sheet">
        <button class="btn-print" onclick="window.print()">🖨️ Imprimir Hoja Oficial (PDF)</button>
        <div class="header">
            <div>
                <div class="company-title">SISTEMA INTEGRADO DE INVENTARIO Y ALMACÉN</div>
                <div class="company-sub">Reporte Oficial de Existencias Físicas y Valoración Contable | Moneda: Bolivianos (Bs.)</div>
            </div>
            <div style="text-align: right; font-size: 0.8rem; color: #64748b;">
                <div><strong>Emisión:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
                <div><strong>Equipo / Red:</strong> 172.25.4.247:8000</div>
                <div><strong>Entorno:</strong> Producción Local</div>
            </div>
        </div>

        <div class="kpi-summary">
            <div class="kpi-box">
                <div class="kpi-box-label">Total Referencias</div>
                <div class="kpi-box-val">{total_items} productos</div>
            </div>
            <div class="kpi-box" style="border-left-color: #10b981;">
                <div class="kpi-box-label">Unidades en Almacén</div>
                <div class="kpi-box-val">{unidades_totales} uds.</div>
            </div>
            <div class="kpi-box" style="border-left-color: #8b5cf6;">
                <div class="kpi-box-label">Valoración Total</div>
                <div class="kpi-box-val">Bs. {valor_total_bs:,.2f}</div>
            </div>
            <div class="kpi-box" style="border-left-color: #f59e0b;">
                <div class="kpi-box-label">Estado Auditoría</div>
                <div class="kpi-box-val">Conforme</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">#</th>
                    <th style="width: 130px;">Código</th>
                    <th>Producto</th>
                    <th style="width: 120px;">Categoría</th>
                    <th style="width: 95px; text-align: right;">Precio Unit.</th>
                    <th style="width: 50px; text-align: center;">Stock</th>
                    <th style="width: 50px; text-align: center;">Mín.</th>
                    <th style="width: 110px; text-align: right;">Total (Bs.)</th>
                    <th style="width: 80px; text-align: center;">Estado</th>
                </tr>
            </thead>
            <tbody>
                {"".join(filas_tr)}
            </tbody>
        </table>

        <div class="signatures">
            <div class="sig-box">
                <strong>Responsable de Almacén</strong><br>
                Firma y Aclaración
            </div>
            <div class="sig-box">
                <strong>Jefe de Inventarios y Compras</strong><br>
                Firma y Sello
            </div>
            <div class="sig-box">
                <strong>Auditor de Sistemas / Fiscalización</strong><br>
                Revisión Conforme
            </div>
        </div>
    </div>
</body>
</html>"""
            response = HttpResponse(html_doc, content_type="text/html; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="hoja_oficial_inventario_{fecha_str}.html"'
            return response

        else:
            raise ValueError(f"Formato de exportación no soportado: {formato}")


def importar_catalogo_csv(archivo_csv, usuario="Administrador"):
    """
    Importa masivamente productos desde un archivo CSV con auditoría automática en el Kardex.
    Retorna un diccionario con estadísticas de la operación.
    """
    creados = 0
    actualizados = 0
    errores = []

    try:
        contenido = archivo_csv.read().decode("utf-8-sig")
        lector = csv.DictReader(io.StringIO(contenido))

        for num_fila, fila in enumerate(lector, start=2):
            codigo = fila.get("Código", "").strip() or fila.get("codigo", "").strip() or fila.get("sku", "").strip()
            nombre = fila.get("Nombre", "").strip() or fila.get("nombre", "").strip()
            categoria = fila.get("Categoría", "").strip() or fila.get("categoria", "").strip() or "General"
            
            if not codigo or not nombre:
                errores.append(f"Fila {num_fila}: Código y Nombre son campos obligatorios.")
                continue

            try:
                precio_raw = fila.get("Precio (Bs.)", fila.get("precio", 0))
                precio = float(str(precio_raw).replace("Bs.", "").replace(",", "").strip())
                stock_raw = fila.get("Cantidad Existente", fila.get("cantidad_existente", fila.get("stock", 0)))
                stock = int(stock_raw)
                stock_min_raw = fila.get("Stock Mínimo", fila.get("stock_minimo", 5))
                stock_min = int(stock_min_raw)
            except (ValueError, TypeError) as e:
                errores.append(f"Fila {num_fila} ({codigo}): Error en formato de números ({e}).")
                continue

            marca = fila.get("Marca", fila.get("marca", "")).strip()
            descripcion = fila.get("Descripción", fila.get("descripcion", "")).strip()

            prod_existente = Producto.objects.filter(codigo=codigo).first()
            if prod_existente:
                stock_previo = prod_existente.cantidad_existente
                prod_existente.nombre = nombre
                prod_existente.categoria = categoria
                prod_existente.precio = precio
                prod_existente.cantidad_existente = stock
                prod_existente.stock_minimo = stock_min
                if marca:
                    prod_existente.marca = marca
                if descripcion:
                    prod_existente.descripcion = descripcion
                prod_existente.save()

                if stock_previo != stock:
                    delta = stock - stock_previo
                    MovimientoStock.objects.create(
                        producto=prod_existente,
                        tipo="AJUSTE",
                        cantidad=abs(delta),
                        stock_previo=stock_previo,
                        stock_resultante=stock,
                        motivo=f"Actualización masiva vía importación CSV ({'+' if delta > 0 else ''}{delta} uds)",
                        usuario=usuario
                    )
                actualizados += 1
            else:
                nuevo_prod = Producto.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    categoria=categoria,
                    marca=marca,
                    precio=precio,
                    cantidad_existente=stock,
                    stock_minimo=stock_min,
                    descripcion=descripcion,
                    estado=True
                )
                MovimientoStock.objects.create(
                    producto=nuevo_prod,
                    tipo="ENTRADA",
                    cantidad=stock,
                    stock_previo=0,
                    stock_resultante=stock,
                    motivo="Alta inicial mediante importación masiva CSV",
                    usuario=usuario
                )
                creados += 1

    except Exception as e:
        errores.append(f"Error crítico al procesar el archivo CSV: {str(e)}")

    from .inventory_service import invalidar_cache_inventario
    invalidar_cache_inventario()

    return {
        "creados": creados,
        "actualizados": actualizados,
        "errores": errores,
        "exito": len(errores) == 0
    }
